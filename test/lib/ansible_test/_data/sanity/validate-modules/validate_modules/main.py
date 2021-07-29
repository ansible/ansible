# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Matt Martz <matt@sivel.net>
# Copyright (C) 2015 Rackspace US, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import argparse
import ast
import datetime
import json
import errno
import os
import re
import subprocess
import sys
import tempfile
import traceback

from collections import OrderedDict
from contextlib import contextmanager
from distutils.version import StrictVersion, LooseVersion
from fnmatch import fnmatch

import yaml

from ansible import __version__ as ansible_version
from ansible.executor.module_common import REPLACER_WINDOWS
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.parameters import DEFAULT_TYPE_VALIDATORS
from ansible.plugins.loader import fragment_loader
from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder
from ansible.utils.plugin_docs import REJECTLIST, add_collection_to_versions_and_dates, add_fragments, get_docstring
from ansible.utils.version import SemanticVersion

from .module_args import AnsibleModuleImportError, AnsibleModuleNotInitialized, get_argument_spec

from .schema import ansible_module_kwargs_schema, doc_schema, return_schema

from .utils import CaptureStd, NoArgsAnsibleModule, compare_unordered_lists, is_empty, parse_yaml, parse_isodate
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import PY3, with_metaclass, string_types

if PY3:
    # Because there is no ast.TryExcept in Python 3 ast module
    TRY_EXCEPT = ast.Try
    # REPLACER_WINDOWS from ansible.executor.module_common is byte
    # string but we need unicode for Python 3
    REPLACER_WINDOWS = REPLACER_WINDOWS.decode('utf-8')
else:
    TRY_EXCEPT = ast.TryExcept

REJECTLIST_DIRS = frozenset(('.git', 'test', '.github', '.idea'))
INDENT_REGEX = re.compile(r'([\t]*)')
TYPE_REGEX = re.compile(r'.*(if|or)(\s+[^"\']*|\s+)(?<!_)(?<!str\()type\([^)].*')
SYS_EXIT_REGEX = re.compile(r'[^#]*sys.exit\s*\(.*')
NO_LOG_REGEX = re.compile(r'(?:pass(?!ive)|secret|token|key)', re.I)


REJECTLIST_IMPORTS = {
    'requests': {
        'new_only': True,
        'error': {
            'code': 'use-module-utils-urls',
            'msg': ('requests import found, should use '
                    'ansible.module_utils.urls instead')
        }
    },
    r'boto(?:\.|$)': {
        'new_only': True,
        'error': {
            'code': 'use-boto3',
            'msg': 'boto import found, new modules should use boto3'
        }
    },
}
SUBPROCESS_REGEX = re.compile(r'subprocess\.Po.*')
OS_CALL_REGEX = re.compile(r'os\.call.*')


LOOSE_ANSIBLE_VERSION = LooseVersion('.'.join(ansible_version.split('.')[:3]))


def is_potential_secret_option(option_name):
    if not NO_LOG_REGEX.search(option_name):
        return False
    # If this is a count, type, algorithm, timeout, filename, or name, it is probably not a secret
    if option_name.endswith((
            '_count', '_type', '_alg', '_algorithm', '_timeout', '_name', '_comment',
            '_bits', '_id', '_identifier', '_period', '_file', '_filename',
    )):
        return False
    # 'key' also matches 'publickey', which is generally not secret
    if any(part in option_name for part in (
            'publickey', 'public_key', 'keyusage', 'key_usage', 'keyserver', 'key_server',
            'keysize', 'key_size', 'keyservice', 'key_service', 'pub_key', 'pubkey',
            'keyboard', 'secretary',
    )):
        return False
    return True


def compare_dates(d1, d2):
    try:
        date1 = parse_isodate(d1, allow_date=True)
        date2 = parse_isodate(d2, allow_date=True)
        return date1 == date2
    except ValueError:
        # At least one of d1 and d2 cannot be parsed. Simply compare values.
        return d1 == d2


class ReporterEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Exception):
            return str(o)

        return json.JSONEncoder.default(self, o)


class Reporter:
    def __init__(self):
        self.files = OrderedDict()

    def _ensure_default_entry(self, path):
        try:
            self.files[path]
        except KeyError:
            self.files[path] = {
                'errors': [],
                'warnings': [],
                'traces': [],
                'warning_traces': []
            }

    def _log(self, path, code, msg, level='error', line=0, column=0):
        self._ensure_default_entry(path)
        lvl_dct = self.files[path]['%ss' % level]
        lvl_dct.append({
            'code': code,
            'msg': msg,
            'line': line,
            'column': column
        })

    def error(self, *args, **kwargs):
        self._log(*args, level='error', **kwargs)

    def warning(self, *args, **kwargs):
        self._log(*args, level='warning', **kwargs)

    def trace(self, path, tracebk):
        self._ensure_default_entry(path)
        self.files[path]['traces'].append(tracebk)

    def warning_trace(self, path, tracebk):
        self._ensure_default_entry(path)
        self.files[path]['warning_traces'].append(tracebk)

    @staticmethod
    @contextmanager
    def _output_handle(output):
        if output != '-':
            handle = open(output, 'w+')
        else:
            handle = sys.stdout

        yield handle

        handle.flush()
        handle.close()

    @staticmethod
    def _filter_out_ok(reports):
        temp_reports = OrderedDict()
        for path, report in reports.items():
            if report['errors'] or report['warnings']:
                temp_reports[path] = report

        return temp_reports

    def plain(self, warnings=False, output='-'):
        """Print out the test results in plain format

        output is ignored here for now
        """
        ret = []

        for path, report in Reporter._filter_out_ok(self.files).items():
            traces = report['traces'][:]
            if warnings and report['warnings']:
                traces.extend(report['warning_traces'])

            for trace in traces:
                print('TRACE:')
                print('\n    '.join(('    %s' % trace).splitlines()))
            for error in report['errors']:
                error['path'] = path
                print('%(path)s:%(line)d:%(column)d: E%(code)s %(msg)s' % error)
                ret.append(1)
            if warnings:
                for warning in report['warnings']:
                    warning['path'] = path
                    print('%(path)s:%(line)d:%(column)d: W%(code)s %(msg)s' % warning)

        return 3 if ret else 0

    def json(self, warnings=False, output='-'):
        """Print out the test results in json format

        warnings is not respected in this output
        """
        ret = [len(r['errors']) for r in self.files.values()]

        with Reporter._output_handle(output) as handle:
            print(json.dumps(Reporter._filter_out_ok(self.files), indent=4, cls=ReporterEncoder), file=handle)

        return 3 if sum(ret) else 0


class Validator(with_metaclass(abc.ABCMeta, object)):
    """Validator instances are intended to be run on a single object.  if you
    are scanning multiple objects for problems, you'll want to have a separate
    Validator for each one."""

    def __init__(self, reporter=None):
        self.reporter = reporter

    @abc.abstractproperty
    def object_name(self):
        """Name of the object we validated"""
        pass

    @abc.abstractproperty
    def object_path(self):
        """Path of the object we validated"""
        pass

    @abc.abstractmethod
    def validate(self):
        """Run this method to generate the test results"""
        pass


class ModuleValidator(Validator):
    REJECTLIST_PATTERNS = ('.git*', '*.pyc', '*.pyo', '.*', '*.md', '*.rst', '*.txt')
    REJECTLIST_FILES = frozenset(('.git', '.gitignore', '.travis.yml',
                                  'shippable.yml',
                                  '.gitattributes', '.gitmodules', 'COPYING',
                                  '__init__.py', 'VERSION', 'test-docs.sh'))
    REJECTLIST = REJECTLIST_FILES.union(REJECTLIST['MODULE'])

    PS_DOC_REJECTLIST = frozenset((
        'async_status.ps1',
        'slurp.ps1',
        'setup.ps1'
    ))

    # win_dsc is a dynamic arg spec, the docs won't ever match
    PS_ARG_VALIDATE_REJECTLIST = frozenset(('win_dsc.ps1', ))

    ACCEPTLIST_FUTURE_IMPORTS = frozenset(('absolute_import', 'division', 'print_function'))

    def __init__(self, path, analyze_arg_spec=False, collection=None, collection_version=None,
                 base_branch=None, git_cache=None, reporter=None, routing=None):
        super(ModuleValidator, self).__init__(reporter=reporter or Reporter())

        self.path = path
        self.basename = os.path.basename(self.path)
        self.name = os.path.splitext(self.basename)[0]

        self.analyze_arg_spec = analyze_arg_spec

        self._Version = LooseVersion
        self._StrictVersion = StrictVersion

        self.collection = collection
        self.collection_name = 'ansible.builtin'
        if self.collection:
            self._Version = SemanticVersion
            self._StrictVersion = SemanticVersion
            collection_namespace_path, collection_name = os.path.split(self.collection)
            self.collection_name = '%s.%s' % (os.path.basename(collection_namespace_path), collection_name)
        self.routing = routing
        self.collection_version = None
        if collection_version is not None:
            self.collection_version_str = collection_version
            self.collection_version = SemanticVersion(collection_version)

        self.base_branch = base_branch
        self.git_cache = git_cache or GitCache()

        self._python_module_override = False

        with open(path) as f:
            self.text = f.read()
        self.length = len(self.text.splitlines())
        try:
            self.ast = ast.parse(self.text)
        except Exception:
            self.ast = None

        if base_branch:
            self.base_module = self._get_base_file()
        else:
            self.base_module = None

    def _create_version(self, v, collection_name=None):
        if not v:
            raise ValueError('Empty string is not a valid version')
        if collection_name == 'ansible.builtin':
            return LooseVersion(v)
        if collection_name is not None:
            return SemanticVersion(v)
        return self._Version(v)

    def _create_strict_version(self, v, collection_name=None):
        if not v:
            raise ValueError('Empty string is not a valid version')
        if collection_name == 'ansible.builtin':
            return StrictVersion(v)
        if collection_name is not None:
            return SemanticVersion(v)
        return self._StrictVersion(v)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.base_module:
            return

        try:
            os.remove(self.base_module)
        except Exception:
            pass

    @property
    def object_name(self):
        return self.basename

    @property
    def object_path(self):
        return self.path

    def _get_collection_meta(self):
        """Implement if we need this for version_added comparisons
        """
        pass

    def _python_module(self):
        if self.path.endswith('.py') or self._python_module_override:
            return True
        return False

    def _powershell_module(self):
        if self.path.endswith('.ps1'):
            return True
        return False

    def _just_docs(self):
        """Module can contain just docs and from __future__ boilerplate
        """
        try:
            for child in self.ast.body:
                if not isinstance(child, ast.Assign):
                    # allowed from __future__ imports
                    if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                        for future_import in child.names:
                            if future_import.name not in self.ACCEPTLIST_FUTURE_IMPORTS:
                                break
                        else:
                            continue
                    return False
            return True
        except AttributeError:
            return False

    def _get_base_branch_module_path(self):
        """List all paths within lib/ansible/modules to try and match a moved module"""
        return self.git_cache.base_module_paths.get(self.object_name)

    def _has_alias(self):
        """Return true if the module has any aliases."""
        return self.object_name in self.git_cache.head_aliased_modules

    def _get_base_file(self):
        # In case of module moves, look for the original location
        base_path = self._get_base_branch_module_path()

        command = ['git', 'show', '%s:%s' % (self.base_branch, base_path or self.path)]
        p = subprocess.Popen(command, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if int(p.returncode) != 0:
            return None

        t = tempfile.NamedTemporaryFile(delete=False)
        t.write(stdout)
        t.close()

        return t.name

    def _is_new_module(self):
        if self._has_alias():
            return False

        return not self.object_name.startswith('_') and bool(self.base_branch) and not bool(self.base_module)

    def _check_interpreter(self, powershell=False):
        if powershell:
            if not self.text.startswith('#!powershell\n'):
                self.reporter.error(
                    path=self.object_path,
                    code='missing-powershell-interpreter',
                    msg='Interpreter line is not "#!powershell"'
                )
            return

        if not self.text.startswith('#!/usr/bin/python'):
            self.reporter.error(
                path=self.object_path,
                code='missing-python-interpreter',
                msg='Interpreter line is not "#!/usr/bin/python"',
            )

    def _check_type_instead_of_isinstance(self, powershell=False):
        if powershell:
            return
        for line_no, line in enumerate(self.text.splitlines()):
            typekeyword = TYPE_REGEX.match(line)
            if typekeyword:
                # TODO: add column
                self.reporter.error(
                    path=self.object_path,
                    code='unidiomatic-typecheck',
                    msg=('Type comparison using type() found. '
                         'Use isinstance() instead'),
                    line=line_no + 1
                )

    def _check_for_sys_exit(self):
        # Optimize out the happy path
        if 'sys.exit' not in self.text:
            return

        for line_no, line in enumerate(self.text.splitlines()):
            sys_exit_usage = SYS_EXIT_REGEX.match(line)
            if sys_exit_usage:
                # TODO: add column
                self.reporter.error(
                    path=self.object_path,
                    code='use-fail-json-not-sys-exit',
                    msg='sys.exit() call found. Should be exit_json/fail_json',
                    line=line_no + 1
                )

    def _check_gpl3_header(self):
        header = '\n'.join(self.text.split('\n')[:20])
        if ('GNU General Public License' not in header or
                ('version 3' not in header and 'v3.0' not in header)):
            self.reporter.error(
                path=self.object_path,
                code='missing-gplv3-license',
                msg='GPLv3 license header not found in the first 20 lines of the module'
            )
        elif self._is_new_module():
            if len([line for line in header
                    if 'GNU General Public License' in line]) > 1:
                self.reporter.error(
                    path=self.object_path,
                    code='use-short-gplv3-license',
                    msg='Found old style GPLv3 license header: '
                        'https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_documenting.html#copyright'
                )

    def _check_for_subprocess(self):
        for child in self.ast.body:
            if isinstance(child, ast.Import):
                if child.names[0].name == 'subprocess':
                    for line_no, line in enumerate(self.text.splitlines()):
                        sp_match = SUBPROCESS_REGEX.search(line)
                        if sp_match:
                            self.reporter.error(
                                path=self.object_path,
                                code='use-run-command-not-popen',
                                msg=('subprocess.Popen call found. Should be module.run_command'),
                                line=(line_no + 1),
                                column=(sp_match.span()[0] + 1)
                            )

    def _check_for_os_call(self):
        if 'os.call' in self.text:
            for line_no, line in enumerate(self.text.splitlines()):
                os_call_match = OS_CALL_REGEX.search(line)
                if os_call_match:
                    self.reporter.error(
                        path=self.object_path,
                        code='use-run-command-not-os-call',
                        msg=('os.call() call found. Should be module.run_command'),
                        line=(line_no + 1),
                        column=(os_call_match.span()[0] + 1)
                    )

    def _find_rejectlist_imports(self):
        for child in self.ast.body:
            names = []
            if isinstance(child, ast.Import):
                names.extend(child.names)
            elif isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, ast.Import):
                        names.extend(grandchild.names)
            for name in names:
                # TODO: Add line/col
                for rejectlist_import, options in REJECTLIST_IMPORTS.items():
                    if re.search(rejectlist_import, name.name):
                        new_only = options['new_only']
                        if self._is_new_module() and new_only:
                            self.reporter.error(
                                path=self.object_path,
                                **options['error']
                            )
                        elif not new_only:
                            self.reporter.error(
                                path=self.object_path,
                                **options['error']
                            )

    def _find_module_utils(self, main):
        linenos = []
        found_basic = False
        for child in self.ast.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                names = []
                try:
                    names.append(child.module)
                    if child.module.endswith('.basic'):
                        found_basic = True
                except AttributeError:
                    pass
                names.extend([n.name for n in child.names])

                if [n for n in names if n.startswith('ansible.module_utils')]:
                    linenos.append(child.lineno)

                    for name in child.names:
                        if ('module_utils' in getattr(child, 'module', '') and
                                isinstance(name, ast.alias) and
                                name.name == '*'):
                            msg = (
                                'module-utils-specific-import',
                                ('module_utils imports should import specific '
                                 'components, not "*"')
                            )
                            if self._is_new_module():
                                self.reporter.error(
                                    path=self.object_path,
                                    code=msg[0],
                                    msg=msg[1],
                                    line=child.lineno
                                )
                            else:
                                self.reporter.warning(
                                    path=self.object_path,
                                    code=msg[0],
                                    msg=msg[1],
                                    line=child.lineno
                                )

                        if (isinstance(name, ast.alias) and
                                name.name == 'basic'):
                            found_basic = True

        if not found_basic:
            self.reporter.warning(
                path=self.object_path,
                code='missing-module-utils-basic-import',
                msg='Did not find "ansible.module_utils.basic" import'
            )

        return linenos

    def _get_first_callable(self):
        linenos = []
        for child in self.ast.body:
            if isinstance(child, (ast.FunctionDef, ast.ClassDef)):
                linenos.append(child.lineno)

        return min(linenos)

    def _find_main_call(self, look_for="main"):
        """ Ensure that the module ends with:
            if __name__ == '__main__':
                main()
        OR, in the case of modules that are in the docs-only deprecation phase
            if __name__ == '__main__':
                removed_module()
        """
        lineno = False
        if_bodies = []
        for child in self.ast.body:
            if isinstance(child, ast.If):
                try:
                    if child.test.left.id == '__name__':
                        if_bodies.extend(child.body)
                except AttributeError:
                    pass

        bodies = self.ast.body
        bodies.extend(if_bodies)

        for child in bodies:

            # validate that the next to last line is 'if __name__ == "__main__"'
            if child.lineno == (self.length - 1):

                mainchecked = False
                try:
                    if isinstance(child, ast.If) and \
                            child.test.left.id == '__name__' and \
                            len(child.test.ops) == 1 and \
                            isinstance(child.test.ops[0], ast.Eq) and \
                            child.test.comparators[0].s == '__main__':
                        mainchecked = True
                except Exception:
                    pass

                if not mainchecked:
                    self.reporter.error(
                        path=self.object_path,
                        code='missing-if-name-main',
                        msg='Next to last line should be: if __name__ == "__main__":',
                        line=child.lineno
                    )

            # validate that the final line is a call to main()
            if isinstance(child, ast.Expr):
                if isinstance(child.value, ast.Call):
                    if (isinstance(child.value.func, ast.Name) and
                            child.value.func.id == look_for):
                        lineno = child.lineno
                        if lineno < self.length - 1:
                            self.reporter.error(
                                path=self.object_path,
                                code='last-line-main-call',
                                msg=('Call to %s() not the last line' % look_for),
                                line=lineno
                            )

        if not lineno:
            self.reporter.error(
                path=self.object_path,
                code='missing-main-call',
                msg=('Did not find a call to %s()' % look_for)
            )

        return lineno or 0

    def _find_has_import(self):
        for child in self.ast.body:
            found_try_except_import = False
            found_has = False
            if isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, ast.Import):
                        found_try_except_import = True
                    if isinstance(grandchild, ast.Assign):
                        for target in grandchild.targets:
                            if not isinstance(target, ast.Name):
                                continue
                            if target.id.lower().startswith('has_'):
                                found_has = True
            if found_try_except_import and not found_has:
                # TODO: Add line/col
                self.reporter.warning(
                    path=self.object_path,
                    code='try-except-missing-has',
                    msg='Found Try/Except block without HAS_ assignment'
                )

    def _ensure_imports_below_docs(self, doc_info, first_callable):
        try:
            min_doc_line = min(
                [doc_info[key]['lineno'] for key in doc_info if doc_info[key]['lineno']]
            )
        except ValueError:
            # We can't perform this validation, as there are no DOCs provided at all
            return

        max_doc_line = max(
            [doc_info[key]['end_lineno'] for key in doc_info if doc_info[key]['end_lineno']]
        )

        import_lines = []

        for child in self.ast.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                    # allowed from __future__ imports
                    for future_import in child.names:
                        if future_import.name not in self.ACCEPTLIST_FUTURE_IMPORTS:
                            self.reporter.error(
                                path=self.object_path,
                                code='illegal-future-imports',
                                msg=('Only the following from __future__ imports are allowed: %s'
                                     % ', '.join(self.ACCEPTLIST_FUTURE_IMPORTS)),
                                line=child.lineno
                            )
                            break
                    else:  # for-else.  If we didn't find a problem nad break out of the loop, then this is a legal import
                        continue
                import_lines.append(child.lineno)
                if child.lineno < min_doc_line:
                    self.reporter.error(
                        path=self.object_path,
                        code='import-before-documentation',
                        msg=('Import found before documentation variables. '
                             'All imports must appear below '
                             'DOCUMENTATION/EXAMPLES/RETURN.'),
                        line=child.lineno
                    )
                    break
            elif isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, (ast.Import, ast.ImportFrom)):
                        import_lines.append(grandchild.lineno)
                        if grandchild.lineno < min_doc_line:
                            self.reporter.error(
                                path=self.object_path,
                                code='import-before-documentation',
                                msg=('Import found before documentation '
                                     'variables. All imports must appear below '
                                     'DOCUMENTATION/EXAMPLES/RETURN.'),
                                line=child.lineno
                            )
                            break

        for import_line in import_lines:
            if not (max_doc_line < import_line < first_callable):
                msg = (
                    'import-placement',
                    ('Imports should be directly below DOCUMENTATION/EXAMPLES/'
                     'RETURN.')
                )
                if self._is_new_module():
                    self.reporter.error(
                        path=self.object_path,
                        code=msg[0],
                        msg=msg[1],
                        line=import_line
                    )
                else:
                    self.reporter.warning(
                        path=self.object_path,
                        code=msg[0],
                        msg=msg[1],
                        line=import_line
                    )

    def _validate_ps_replacers(self):
        # loop all (for/else + error)
        # get module list for each
        # check "shape" of each module name

        module_requires = r'(?im)^#\s*requires\s+\-module(?:s?)\s*(Ansible\.ModuleUtils\..+)'
        csharp_requires = r'(?im)^#\s*ansiblerequires\s+\-csharputil\s*(Ansible\..+)'
        found_requires = False

        for req_stmt in re.finditer(module_requires, self.text):
            found_requires = True
            # this will bomb on dictionary format - "don't do that"
            module_list = [x.strip() for x in req_stmt.group(1).split(',')]
            if len(module_list) > 1:
                self.reporter.error(
                    path=self.object_path,
                    code='multiple-utils-per-requires',
                    msg='Ansible.ModuleUtils requirements do not support multiple modules per statement: "%s"' % req_stmt.group(0)
                )
                continue

            module_name = module_list[0]

            if module_name.lower().endswith('.psm1'):
                self.reporter.error(
                    path=self.object_path,
                    code='invalid-requires-extension',
                    msg='Module #Requires should not end in .psm1: "%s"' % module_name
                )

        for req_stmt in re.finditer(csharp_requires, self.text):
            found_requires = True
            # this will bomb on dictionary format - "don't do that"
            module_list = [x.strip() for x in req_stmt.group(1).split(',')]
            if len(module_list) > 1:
                self.reporter.error(
                    path=self.object_path,
                    code='multiple-csharp-utils-per-requires',
                    msg='Ansible C# util requirements do not support multiple utils per statement: "%s"' % req_stmt.group(0)
                )
                continue

            module_name = module_list[0]

            if module_name.lower().endswith('.cs'):
                self.reporter.error(
                    path=self.object_path,
                    code='illegal-extension-cs',
                    msg='Module #AnsibleRequires -CSharpUtil should not end in .cs: "%s"' % module_name
                )

        # also accept the legacy #POWERSHELL_COMMON replacer signal
        if not found_requires and REPLACER_WINDOWS not in self.text:
            self.reporter.error(
                path=self.object_path,
                code='missing-module-utils-import-csharp-requirements',
                msg='No Ansible.ModuleUtils or C# Ansible util requirements/imports found'
            )

    def _find_ps_docs_py_file(self):
        if self.object_name in self.PS_DOC_REJECTLIST:
            return
        py_path = self.path.replace('.ps1', '.py')
        if not os.path.isfile(py_path):
            self.reporter.error(
                path=self.object_path,
                code='missing-python-doc',
                msg='Missing python documentation file'
            )
        return py_path

    def _get_docs(self):
        docs = {
            'DOCUMENTATION': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
            'EXAMPLES': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
            'RETURN': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
        }
        for child in self.ast.body:
            if isinstance(child, ast.Assign):
                for grandchild in child.targets:
                    if not isinstance(grandchild, ast.Name):
                        continue

                    if grandchild.id == 'DOCUMENTATION':
                        docs['DOCUMENTATION']['value'] = child.value.s
                        docs['DOCUMENTATION']['lineno'] = child.lineno
                        docs['DOCUMENTATION']['end_lineno'] = (
                            child.lineno + len(child.value.s.splitlines())
                        )
                    elif grandchild.id == 'EXAMPLES':
                        docs['EXAMPLES']['value'] = child.value.s
                        docs['EXAMPLES']['lineno'] = child.lineno
                        docs['EXAMPLES']['end_lineno'] = (
                            child.lineno + len(child.value.s.splitlines())
                        )
                    elif grandchild.id == 'RETURN':
                        docs['RETURN']['value'] = child.value.s
                        docs['RETURN']['lineno'] = child.lineno
                        docs['RETURN']['end_lineno'] = (
                            child.lineno + len(child.value.s.splitlines())
                        )

        return docs

    def _validate_docs_schema(self, doc, schema, name, error_code):
        # TODO: Add line/col
        errors = []
        try:
            schema(doc)
        except Exception as e:
            for error in e.errors:
                error.data = doc
            errors.extend(e.errors)

        for error in errors:
            path = [str(p) for p in error.path]

            local_error_code = getattr(error, 'ansible_error_code', error_code)

            if isinstance(error.data, dict):
                error_message = humanize_error(error.data, error)
            else:
                error_message = error

            if path:
                combined_path = '%s.%s' % (name, '.'.join(path))
            else:
                combined_path = name

            self.reporter.error(
                path=self.object_path,
                code=local_error_code,
                msg='%s: %s' % (combined_path, error_message)
            )

    def _validate_docs(self):
        doc_info = self._get_docs()
        doc = None
        documentation_exists = False
        examples_exist = False
        returns_exist = False
        # We have three ways of marking deprecated/removed files.  Have to check each one
        # individually and then make sure they all agree
        filename_deprecated_or_removed = False
        deprecated = False
        removed = False
        doc_deprecated = None  # doc legally might not exist
        routing_says_deprecated = False

        if self.object_name.startswith('_') and not os.path.islink(self.object_path):
            filename_deprecated_or_removed = True

        # We are testing a collection
        if self.routing:
            routing_deprecation = self.routing.get('plugin_routing', {}).get('modules', {}).get(self.name, {}).get('deprecation', {})
            if routing_deprecation:
                # meta/runtime.yml says this is deprecated
                routing_says_deprecated = True
                deprecated = True

        if not removed:
            if not bool(doc_info['DOCUMENTATION']['value']):
                self.reporter.error(
                    path=self.object_path,
                    code='missing-documentation',
                    msg='No DOCUMENTATION provided'
                )
            else:
                documentation_exists = True
                doc, errors, traces = parse_yaml(
                    doc_info['DOCUMENTATION']['value'],
                    doc_info['DOCUMENTATION']['lineno'],
                    self.name, 'DOCUMENTATION'
                )
                if doc:
                    add_collection_to_versions_and_dates(doc, self.collection_name, is_module=True)
                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code='documentation-syntax-error',
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )
                if not errors and not traces:
                    missing_fragment = False
                    with CaptureStd():
                        try:
                            get_docstring(self.path, fragment_loader, verbose=True,
                                          collection_name=self.collection_name, is_module=True)
                        except AssertionError:
                            fragment = doc['extends_documentation_fragment']
                            self.reporter.error(
                                path=self.object_path,
                                code='missing-doc-fragment',
                                msg='DOCUMENTATION fragment missing: %s' % fragment
                            )
                            missing_fragment = True
                        except Exception as e:
                            self.reporter.trace(
                                path=self.object_path,
                                tracebk=traceback.format_exc()
                            )
                            self.reporter.error(
                                path=self.object_path,
                                code='documentation-error',
                                msg='Unknown DOCUMENTATION error, see TRACE: %s' % e
                            )

                    if not missing_fragment:
                        add_fragments(doc, self.object_path, fragment_loader=fragment_loader, is_module=True)

                    if 'options' in doc and doc['options'] is None:
                        self.reporter.error(
                            path=self.object_path,
                            code='invalid-documentation-options',
                            msg='DOCUMENTATION.options must be a dictionary/hash when used',
                        )

                    if 'deprecated' in doc and doc.get('deprecated'):
                        doc_deprecated = True
                        doc_deprecation = doc['deprecated']
                        documentation_collection = doc_deprecation.get('removed_from_collection')
                        if documentation_collection != self.collection_name:
                            self.reporter.error(
                                path=self.object_path,
                                code='deprecation-wrong-collection',
                                msg='"DOCUMENTATION.deprecation.removed_from_collection must be the current collection name: %r vs. %r' % (
                                    documentation_collection, self.collection_name)
                            )
                    else:
                        doc_deprecated = False

                    if os.path.islink(self.object_path):
                        # This module has an alias, which we can tell as it's a symlink
                        # Rather than checking for `module: $filename` we need to check against the true filename
                        self._validate_docs_schema(
                            doc,
                            doc_schema(
                                os.readlink(self.object_path).split('.')[0],
                                for_collection=bool(self.collection),
                                deprecated_module=deprecated,
                            ),
                            'DOCUMENTATION',
                            'invalid-documentation',
                        )
                    else:
                        # This is the normal case
                        self._validate_docs_schema(
                            doc,
                            doc_schema(
                                self.object_name.split('.')[0],
                                for_collection=bool(self.collection),
                                deprecated_module=deprecated,
                            ),
                            'DOCUMENTATION',
                            'invalid-documentation',
                        )

                    if not self.collection:
                        existing_doc = self._check_for_new_args(doc)
                        self._check_version_added(doc, existing_doc)

            if not bool(doc_info['EXAMPLES']['value']):
                self.reporter.error(
                    path=self.object_path,
                    code='missing-examples',
                    msg='No EXAMPLES provided'
                )
            else:
                _doc, errors, traces = parse_yaml(doc_info['EXAMPLES']['value'],
                                                  doc_info['EXAMPLES']['lineno'],
                                                  self.name, 'EXAMPLES', load_all=True)
                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code='invalid-examples',
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )

            if not bool(doc_info['RETURN']['value']):
                if self._is_new_module():
                    self.reporter.error(
                        path=self.object_path,
                        code='missing-return',
                        msg='No RETURN provided'
                    )
                else:
                    self.reporter.warning(
                        path=self.object_path,
                        code='missing-return-legacy',
                        msg='No RETURN provided'
                    )
            else:
                data, errors, traces = parse_yaml(doc_info['RETURN']['value'],
                                                  doc_info['RETURN']['lineno'],
                                                  self.name, 'RETURN')
                if data:
                    add_collection_to_versions_and_dates(data, self.collection_name, is_module=True, return_docs=True)
                self._validate_docs_schema(data, return_schema(for_collection=bool(self.collection)),
                                           'RETURN', 'return-syntax-error')

                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code='return-syntax-error',
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )

        # Check for mismatched deprecation
        if not self.collection:
            mismatched_deprecation = True
            if not (filename_deprecated_or_removed or removed or deprecated or doc_deprecated):
                mismatched_deprecation = False
            else:
                if (filename_deprecated_or_removed and deprecated and doc_deprecated):
                    mismatched_deprecation = False
                if (filename_deprecated_or_removed and removed and not (documentation_exists or examples_exist or returns_exist)):
                    mismatched_deprecation = False

            if mismatched_deprecation:
                self.reporter.error(
                    path=self.object_path,
                    code='deprecation-mismatch',
                    msg='Module deprecation/removed must agree in documentation, by prepending filename with'
                        ' "_", and setting DOCUMENTATION.deprecated for deprecation or by removing all'
                        ' documentation for removed'
                )
        else:
            # We are testing a collection
            if self.object_name.startswith('_'):
                self.reporter.error(
                    path=self.object_path,
                    code='collections-no-underscore-on-deprecation',
                    msg='Deprecated content in collections MUST NOT start with "_", update meta/runtime.yml instead',
                )

            if not (doc_deprecated == routing_says_deprecated):
                # DOCUMENTATION.deprecated and meta/runtime.yml disagree
                self.reporter.error(
                    path=self.object_path,
                    code='deprecation-mismatch',
                    msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree.'
                )
            elif routing_says_deprecated:
                # Both DOCUMENTATION.deprecated and meta/runtime.yml agree that the module is deprecated.
                # Make sure they give the same version or date.
                routing_date = routing_deprecation.get('removal_date')
                routing_version = routing_deprecation.get('removal_version')
                # The versions and dates in the module documentation are auto-tagged, so remove the tag
                # to make comparison possible and to avoid confusing the user.
                documentation_date = doc_deprecation.get('removed_at_date')
                documentation_version = doc_deprecation.get('removed_in')
                if not compare_dates(routing_date, documentation_date):
                    self.reporter.error(
                        path=self.object_path,
                        code='deprecation-mismatch',
                        msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree on removal date: %r vs. %r' % (
                            routing_date, documentation_date)
                    )
                if routing_version != documentation_version:
                    self.reporter.error(
                        path=self.object_path,
                        code='deprecation-mismatch',
                        msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree on removal version: %r vs. %r' % (
                            routing_version, documentation_version)
                    )

            # In the future we should error if ANSIBLE_METADATA exists in a collection

        return doc_info, doc

    def _check_version_added(self, doc, existing_doc):
        version_added_raw = doc.get('version_added')
        try:
            collection_name = doc.get('version_added_collection')
            version_added = self._create_strict_version(
                str(version_added_raw or '0.0'),
                collection_name=collection_name)
        except ValueError as e:
            version_added = version_added_raw or '0.0'
            if self._is_new_module() or version_added != 'historical':
                # already reported during schema validation, except:
                if version_added == 'historical':
                    self.reporter.error(
                        path=self.object_path,
                        code='module-invalid-version-added',
                        msg='version_added is not a valid version number: %r. Error: %s' % (version_added, e)
                    )
                return

        if existing_doc and str(version_added_raw) != str(existing_doc.get('version_added')):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (existing_doc.get('version_added'), version_added_raw)
            )

        if not self._is_new_module():
            return

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = self._create_strict_version(should_be, collection_name='ansible.builtin')

        if (version_added < strict_ansible_version or
                strict_ansible_version < version_added):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (should_be, version_added_raw)
            )

    def _validate_ansible_module_call(self, docs):
        try:
            spec, kwargs = get_argument_spec(self.path, self.collection)
        except AnsibleModuleNotInitialized:
            self.reporter.error(
                path=self.object_path,
                code='ansible-module-not-initialized',
                msg="Execution of the module did not result in initialization of AnsibleModule",
            )
            return
        except AnsibleModuleImportError as e:
            self.reporter.error(
                path=self.object_path,
                code='import-error',
                msg="Exception attempting to import module for argument_spec introspection, '%s'" % e
            )
            self.reporter.trace(
                path=self.object_path,
                tracebk=traceback.format_exc()
            )
            return

        self._validate_docs_schema(kwargs, ansible_module_kwargs_schema(for_collection=bool(self.collection)),
                                   'AnsibleModule', 'invalid-ansiblemodule-schema')

        self._validate_argument_spec(docs, spec, kwargs)

    def _validate_list_of_module_args(self, name, terms, spec, context):
        if terms is None:
            return
        if not isinstance(terms, (list, tuple)):
            # This is already reported by schema checking
            return
        for check in terms:
            if not isinstance(check, (list, tuple)):
                # This is already reported by schema checking
                continue
            bad_term = False
            for term in check:
                if not isinstance(term, string_types):
                    msg = name
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " must contain strings in the lists or tuples; found value %r" % (term, )
                    self.reporter.error(
                        path=self.object_path,
                        code=name + '-type',
                        msg=msg,
                    )
                    bad_term = True
            if bad_term:
                continue
            if len(set(check)) != len(check):
                msg = name
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms"
                self.reporter.error(
                    path=self.object_path,
                    code=name + '-collision',
                    msg=msg,
                )
            if not set(check) <= set(spec):
                msg = name
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms which are not part of argument_spec: %s" % ", ".join(sorted(set(check).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code=name + '-unknown',
                    msg=msg,
                )

    def _validate_required_if(self, terms, spec, context, module):
        if terms is None:
            return
        if not isinstance(terms, (list, tuple)):
            # This is already reported by schema checking
            return
        for check in terms:
            if not isinstance(check, (list, tuple)) or len(check) not in [3, 4]:
                # This is already reported by schema checking
                continue
            if len(check) == 4 and not isinstance(check[3], bool):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have forth value omitted or of type bool; got %r" % (check[3], )
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-is_one_of-type',
                    msg=msg,
                )
            requirements = check[2]
            if not isinstance(requirements, (list, tuple)):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have third value (requirements) being a list or tuple; got type %r" % (requirements, )
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-type',
                    msg=msg,
                )
                continue
            bad_term = False
            for term in requirements:
                if not isinstance(term, string_types):
                    msg = "required_if"
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " must have only strings in third value (requirements); got %r" % (term, )
                    self.reporter.error(
                        path=self.object_path,
                        code='required_if-requirements-type',
                        msg=msg,
                    )
                    bad_term = True
            if bad_term:
                continue
            if len(set(requirements)) != len(requirements):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms in requirements"
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-collision',
                    msg=msg,
                )
            if not set(requirements) <= set(spec):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms in requirements which are not part of argument_spec: %s" % ", ".join(sorted(set(requirements).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-unknown',
                    msg=msg,
                )
            key = check[0]
            if key not in spec:
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have its key %s in argument_spec" % key
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-unknown-key',
                    msg=msg,
                )
                continue
            if key in requirements:
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains its key %s in requirements" % key
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-key-in-requirements',
                    msg=msg,
                )
            value = check[1]
            if value is not None:
                _type = spec[key].get('type', 'str')
                if callable(_type):
                    _type_checker = _type
                else:
                    _type_checker = DEFAULT_TYPE_VALIDATORS.get(_type)
                try:
                    with CaptureStd():
                        dummy = _type_checker(value)
                except (Exception, SystemExit):
                    msg = "required_if"
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " has value %r which does not fit to %s's parameter type %r" % (value, key, _type)
                    self.reporter.error(
                        path=self.object_path,
                        code='required_if-value-type',
                        msg=msg,
                    )

    def _validate_required_by(self, terms, spec, context):
        if terms is None:
            return
        if not isinstance(terms, Mapping):
            # This is already reported by schema checking
            return
        for key, value in terms.items():
            if isinstance(value, string_types):
                value = [value]
            if not isinstance(value, (list, tuple)):
                # This is already reported by schema checking
                continue
            for term in value:
                if not isinstance(term, string_types):
                    # This is already reported by schema checking
                    continue
            if len(set(value)) != len(value) or key in value:
                msg = "required_by"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms"
                self.reporter.error(
                    path=self.object_path,
                    code='required_by-collision',
                    msg=msg,
                )
            if not set(value) <= set(spec) or key not in spec:
                msg = "required_by"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms which are not part of argument_spec: %s" % ", ".join(sorted(set(value).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code='required_by-unknown',
                    msg=msg,
                )

    def _validate_argument_spec(self, docs, spec, kwargs, context=None, last_context_spec=None):
        if not self.analyze_arg_spec:
            return

        if docs is None:
            docs = {}

        if context is None:
            context = []

        if last_context_spec is None:
            last_context_spec = kwargs

        try:
            if not context:
                add_fragments(docs, self.object_path, fragment_loader=fragment_loader, is_module=True)
        except Exception:
            # Cannot merge fragments
            return

        # Use this to access type checkers later
        module = NoArgsAnsibleModule({})

        self._validate_list_of_module_args('mutually_exclusive', last_context_spec.get('mutually_exclusive'), spec, context)
        self._validate_list_of_module_args('required_together', last_context_spec.get('required_together'), spec, context)
        self._validate_list_of_module_args('required_one_of', last_context_spec.get('required_one_of'), spec, context)
        self._validate_required_if(last_context_spec.get('required_if'), spec, context, module)
        self._validate_required_by(last_context_spec.get('required_by'), spec, context)

        provider_args = set()
        args_from_argspec = set()
        deprecated_args_from_argspec = set()
        doc_options = docs.get('options', {})
        if doc_options is None:
            doc_options = {}
        for arg, data in spec.items():
            restricted_argument_names = ('message', 'syslog_facility')
            if arg.lower() in restricted_argument_names:
                msg = "Argument '%s' in argument_spec " % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += "must not be one of %s as it is used " \
                       "internally by Ansible Core Engine" % (",".join(restricted_argument_names))
                self.reporter.error(
                    path=self.object_path,
                    code='invalid-argument-name',
                    msg=msg,
                )
                continue
            if 'aliases' in data:
                for al in data['aliases']:
                    if al.lower() in restricted_argument_names:
                        msg = "Argument alias '%s' in argument_spec " % al
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += "must not be one of %s as it is used " \
                               "internally by Ansible Core Engine" % (",".join(restricted_argument_names))
                        self.reporter.error(
                            path=self.object_path,
                            code='invalid-argument-name',
                            msg=msg,
                        )
                        continue

            # Could this a place where secrets are leaked?
            # If it is type: path we know it's not a secret key as it's a file path.
            # If it is type: bool it is more likely a flag indicating that something is secret, than an actual secret.
            if all((
                    data.get('no_log') is None, is_potential_secret_option(arg),
                    data.get('type') not in ("path", "bool"), data.get('choices') is None,
            )):
                msg = "Argument '%s' in argument_spec could be a secret, though doesn't have `no_log` set" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                self.reporter.error(
                    path=self.object_path,
                    code='no-log-needed',
                    msg=msg,
                )

            if not isinstance(data, dict):
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must be a dictionary/hash when used"
                self.reporter.error(
                    path=self.object_path,
                    code='invalid-argument-spec',
                    msg=msg,
                )
                continue

            removed_at_date = data.get('removed_at_date', None)
            if removed_at_date is not None:
                try:
                    if parse_isodate(removed_at_date, allow_date=False) < datetime.date.today():
                        msg = "Argument '%s' in argument_spec" % arg
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += " has a removed_at_date '%s' before today" % removed_at_date
                        self.reporter.error(
                            path=self.object_path,
                            code='deprecated-date',
                            msg=msg,
                        )
                except ValueError:
                    # This should only happen when removed_at_date is not in ISO format. Since schema
                    # validation already reported this as an error, don't report it a second time.
                    pass

            deprecated_aliases = data.get('deprecated_aliases', None)
            if deprecated_aliases is not None:
                for deprecated_alias in deprecated_aliases:
                    if 'name' in deprecated_alias and 'date' in deprecated_alias:
                        try:
                            date = deprecated_alias['date']
                            if parse_isodate(date, allow_date=False) < datetime.date.today():
                                msg = "Argument '%s' in argument_spec" % arg
                                if context:
                                    msg += " found in %s" % " -> ".join(context)
                                msg += " has deprecated aliases '%s' with removal date '%s' before today" % (
                                    deprecated_alias['name'], deprecated_alias['date'])
                                self.reporter.error(
                                    path=self.object_path,
                                    code='deprecated-date',
                                    msg=msg,
                                )
                        except ValueError:
                            # This should only happen when deprecated_alias['date'] is not in ISO format. Since
                            # schema validation already reported this as an error, don't report it a second
                            # time.
                            pass

            has_version = False
            if self.collection and self.collection_version is not None:
                compare_version = self.collection_version
                version_of_what = "this collection (%s)" % self.collection_version_str
                code_prefix = 'collection'
                has_version = True
            elif not self.collection:
                compare_version = LOOSE_ANSIBLE_VERSION
                version_of_what = "Ansible (%s)" % ansible_version
                code_prefix = 'ansible'
                has_version = True

            removed_in_version = data.get('removed_in_version', None)
            if removed_in_version is not None:
                try:
                    collection_name = data.get('removed_from_collection')
                    removed_in = self._create_version(str(removed_in_version), collection_name=collection_name)
                    if has_version and collection_name == self.collection_name and compare_version >= removed_in:
                        msg = "Argument '%s' in argument_spec" % arg
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += " has a deprecated removed_in_version %r," % removed_in_version
                        msg += " i.e. the version is less than or equal to the current version of %s" % version_of_what
                        self.reporter.error(
                            path=self.object_path,
                            code=code_prefix + '-deprecated-version',
                            msg=msg,
                        )
                except ValueError as e:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " has an invalid removed_in_version number %r: %s" % (removed_in_version, e)
                    self.reporter.error(
                        path=self.object_path,
                        code='invalid-deprecated-version',
                        msg=msg,
                    )
                except TypeError:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " has an invalid removed_in_version number %r: " % (removed_in_version, )
                    msg += " error while comparing to version of %s" % version_of_what
                    self.reporter.error(
                        path=self.object_path,
                        code='invalid-deprecated-version',
                        msg=msg,
                    )

            if deprecated_aliases is not None:
                for deprecated_alias in deprecated_aliases:
                    if 'name' in deprecated_alias and 'version' in deprecated_alias:
                        try:
                            collection_name = deprecated_alias.get('collection_name')
                            version = self._create_version(str(deprecated_alias['version']), collection_name=collection_name)
                            if has_version and collection_name == self.collection_name and compare_version >= version:
                                msg = "Argument '%s' in argument_spec" % arg
                                if context:
                                    msg += " found in %s" % " -> ".join(context)
                                msg += " has deprecated aliases '%s' with removal in version %r," % (
                                    deprecated_alias['name'], deprecated_alias['version'])
                                msg += " i.e. the version is less than or equal to the current version of %s" % version_of_what
                                self.reporter.error(
                                    path=self.object_path,
                                    code=code_prefix + '-deprecated-version',
                                    msg=msg,
                                )
                        except ValueError as e:
                            msg = "Argument '%s' in argument_spec" % arg
                            if context:
                                msg += " found in %s" % " -> ".join(context)
                            msg += " has deprecated aliases '%s' with invalid removal version %r: %s" % (
                                deprecated_alias['name'], deprecated_alias['version'], e)
                            self.reporter.error(
                                path=self.object_path,
                                code='invalid-deprecated-version',
                                msg=msg,
                            )
                        except TypeError:
                            msg = "Argument '%s' in argument_spec" % arg
                            if context:
                                msg += " found in %s" % " -> ".join(context)
                            msg += " has deprecated aliases '%s' with invalid removal version %r:" % (
                                deprecated_alias['name'], deprecated_alias['version'])
                            msg += " error while comparing to version of %s" % version_of_what
                            self.reporter.error(
                                path=self.object_path,
                                code='invalid-deprecated-version',
                                msg=msg,
                            )

            aliases = data.get('aliases', [])
            if arg in aliases:
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is specified as its own alias"
                self.reporter.error(
                    path=self.object_path,
                    code='parameter-alias-self',
                    msg=msg
                )
            if len(aliases) > len(set(aliases)):
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has at least one alias specified multiple times in aliases"
                self.reporter.error(
                    path=self.object_path,
                    code='parameter-alias-repeated',
                    msg=msg
                )
            if not context and arg == 'state':
                bad_states = set(['list', 'info', 'get']) & set(data.get('choices', set()))
                for bad_state in bad_states:
                    self.reporter.error(
                        path=self.object_path,
                        code='parameter-state-invalid-choice',
                        msg="Argument 'state' includes the value '%s' as a choice" % bad_state)
            if not data.get('removed_in_version', None) and not data.get('removed_at_date', None):
                args_from_argspec.add(arg)
                args_from_argspec.update(aliases)
            else:
                deprecated_args_from_argspec.add(arg)
                deprecated_args_from_argspec.update(aliases)
            if arg == 'provider' and self.object_path.startswith('lib/ansible/modules/network/'):
                if data.get('options') is not None and not isinstance(data.get('options'), Mapping):
                    self.reporter.error(
                        path=self.object_path,
                        code='invalid-argument-spec-options',
                        msg="Argument 'options' in argument_spec['provider'] must be a dictionary/hash when used",
                    )
                elif data.get('options'):
                    # Record provider options from network modules, for later comparison
                    for provider_arg, provider_data in data.get('options', {}).items():
                        provider_args.add(provider_arg)
                        provider_args.update(provider_data.get('aliases', []))

            if data.get('required') and data.get('default', object) != object:
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is marked as required but specifies a default. Arguments with a" \
                       " default should not be marked as required"
                self.reporter.error(
                    path=self.object_path,
                    code='no-default-for-required-parameter',
                    msg=msg
                )

            if arg in provider_args:
                # Provider args are being removed from network module top level
                # don't validate docs<->arg_spec checks below
                continue

            _type = data.get('type', 'str')
            if callable(_type):
                _type_checker = _type
            else:
                _type_checker = DEFAULT_TYPE_VALIDATORS.get(_type)

            _elements = data.get('elements')
            if (_type == 'list') and not _elements:
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " defines type as list but elements is not defined"
                self.reporter.error(
                    path=self.object_path,
                    code='parameter-list-no-elements',
                    msg=msg
                )
            if _elements:
                if not callable(_elements):
                    DEFAULT_TYPE_VALIDATORS.get(_elements)
                if _type != 'list':
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " defines elements as %s but it is valid only when value of parameter type is list" % _elements
                    self.reporter.error(
                        path=self.object_path,
                        code='parameter-invalid-elements',
                        msg=msg
                    )

            arg_default = None
            if 'default' in data and not is_empty(data['default']):
                try:
                    with CaptureStd():
                        arg_default = _type_checker(data['default'])
                except (Exception, SystemExit):
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " defines default as (%r) but this is incompatible with parameter type %r" % (data['default'], _type)
                    self.reporter.error(
                        path=self.object_path,
                        code='incompatible-default-type',
                        msg=msg
                    )
                    continue

            doc_options_args = []
            for alias in sorted(set([arg] + list(aliases))):
                if alias in doc_options:
                    doc_options_args.append(alias)
            if len(doc_options_args) == 0:
                # Undocumented arguments will be handled later (search for undocumented-parameter)
                doc_options_arg = {}
            else:
                doc_options_arg = doc_options[doc_options_args[0]]
                if len(doc_options_args) > 1:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " with aliases %s is documented multiple times, namely as %s" % (
                        ", ".join([("'%s'" % alias) for alias in aliases]),
                        ", ".join([("'%s'" % alias) for alias in doc_options_args])
                    )
                    self.reporter.error(
                        path=self.object_path,
                        code='parameter-documented-multiple-times',
                        msg=msg
                    )

            try:
                doc_default = None
                if 'default' in doc_options_arg and not is_empty(doc_options_arg['default']):
                    with CaptureStd():
                        doc_default = _type_checker(doc_options_arg['default'])
            except (Exception, SystemExit):
                msg = "Argument '%s' in documentation" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " defines default as (%r) but this is incompatible with parameter type %r" % (doc_options_arg.get('default'), _type)
                self.reporter.error(
                    path=self.object_path,
                    code='doc-default-incompatible-type',
                    msg=msg
                )
                continue

            if arg_default != doc_default:
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " defines default as (%r) but documentation defines default as (%r)" % (arg_default, doc_default)
                self.reporter.error(
                    path=self.object_path,
                    code='doc-default-does-not-match-spec',
                    msg=msg
                )

            doc_type = doc_options_arg.get('type')
            if 'type' in data and data['type'] is not None:
                if doc_type is None:
                    if not arg.startswith('_'):  # hidden parameter, for example _raw_params
                        msg = "Argument '%s' in argument_spec" % arg
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += " defines type as %r but documentation doesn't define type" % (data['type'])
                        self.reporter.error(
                            path=self.object_path,
                            code='parameter-type-not-in-doc',
                            msg=msg
                        )
                elif data['type'] != doc_type:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " defines type as %r but documentation defines type as %r" % (data['type'], doc_type)
                    self.reporter.error(
                        path=self.object_path,
                        code='doc-type-does-not-match-spec',
                        msg=msg
                    )
            else:
                if doc_type is None:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " uses default type ('str') but documentation doesn't define type"
                    self.reporter.error(
                        path=self.object_path,
                        code='doc-missing-type',
                        msg=msg
                    )
                elif doc_type != 'str':
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " implies type as 'str' but documentation defines as %r" % doc_type
                    self.reporter.error(
                        path=self.object_path,
                        code='implied-parameter-type-mismatch',
                        msg=msg
                    )

            doc_choices = []
            try:
                for choice in doc_options_arg.get('choices', []):
                    try:
                        with CaptureStd():
                            doc_choices.append(_type_checker(choice))
                    except (Exception, SystemExit):
                        msg = "Argument '%s' in documentation" % arg
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += " defines choices as (%r) but this is incompatible with argument type %r" % (choice, _type)
                        self.reporter.error(
                            path=self.object_path,
                            code='doc-choices-incompatible-type',
                            msg=msg
                        )
                        raise StopIteration()
            except StopIteration:
                continue

            arg_choices = []
            try:
                for choice in data.get('choices', []):
                    try:
                        with CaptureStd():
                            arg_choices.append(_type_checker(choice))
                    except (Exception, SystemExit):
                        msg = "Argument '%s' in argument_spec" % arg
                        if context:
                            msg += " found in %s" % " -> ".join(context)
                        msg += " defines choices as (%r) but this is incompatible with argument type %r" % (choice, _type)
                        self.reporter.error(
                            path=self.object_path,
                            code='incompatible-choices',
                            msg=msg
                        )
                        raise StopIteration()
            except StopIteration:
                continue

            if not compare_unordered_lists(arg_choices, doc_choices):
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " defines choices as (%r) but documentation defines choices as (%r)" % (arg_choices, doc_choices)
                self.reporter.error(
                    path=self.object_path,
                    code='doc-choices-do-not-match-spec',
                    msg=msg
                )

            doc_required = doc_options_arg.get('required', False)
            data_required = data.get('required', False)
            if (doc_required or data_required) and not (doc_required and data_required):
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                if doc_required:
                    msg += " is not required, but is documented as being required"
                else:
                    msg += " is required, but is not documented as being required"
                self.reporter.error(
                    path=self.object_path,
                    code='doc-required-mismatch',
                    msg=msg
                )

            doc_elements = doc_options_arg.get('elements', None)
            doc_type = doc_options_arg.get('type', 'str')
            data_elements = data.get('elements', None)
            if (doc_elements and not doc_type == 'list'):
                msg = "Argument '%s' " % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " defines parameter elements as %s but it is valid only when value of parameter type is list" % doc_elements
                self.reporter.error(
                    path=self.object_path,
                    code='doc-elements-invalid',
                    msg=msg
                )
            if (doc_elements or data_elements) and not (doc_elements == data_elements):
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                if data_elements:
                    msg += " specifies elements as %s," % data_elements
                else:
                    msg += " does not specify elements,"
                if doc_elements:
                    msg += "but elements is documented as being %s" % doc_elements
                else:
                    msg += "but elements is not documented"
                self.reporter.error(
                    path=self.object_path,
                    code='doc-elements-mismatch',
                    msg=msg
                )

            spec_suboptions = data.get('options')
            doc_suboptions = doc_options_arg.get('suboptions', {})
            if spec_suboptions:
                if not doc_suboptions:
                    msg = "Argument '%s' in argument_spec" % arg
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " has sub-options but documentation does not define it"
                    self.reporter.error(
                        path=self.object_path,
                        code='missing-suboption-docs',
                        msg=msg
                    )
                self._validate_argument_spec({'options': doc_suboptions}, spec_suboptions, kwargs,
                                             context=context + [arg], last_context_spec=data)

        for arg in args_from_argspec:
            if not str(arg).isidentifier():
                msg = "Argument '%s' in argument_spec" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is not a valid python identifier"
                self.reporter.error(
                    path=self.object_path,
                    code='parameter-invalid',
                    msg=msg
                )

        if docs:
            args_from_docs = set()
            for arg, data in doc_options.items():
                args_from_docs.add(arg)
                args_from_docs.update(data.get('aliases', []))

            args_missing_from_docs = args_from_argspec.difference(args_from_docs)
            docs_missing_from_args = args_from_docs.difference(args_from_argspec | deprecated_args_from_argspec)
            for arg in args_missing_from_docs:
                if arg in provider_args:
                    # Provider args are being removed from network module top level
                    # So they are likely not documented on purpose
                    continue
                msg = "Argument '%s'" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is listed in the argument_spec, but not documented in the module documentation"
                self.reporter.error(
                    path=self.object_path,
                    code='undocumented-parameter',
                    msg=msg
                )
            for arg in docs_missing_from_args:
                msg = "Argument '%s'" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is listed in DOCUMENTATION.options, but not accepted by the module argument_spec"
                self.reporter.error(
                    path=self.object_path,
                    code='nonexistent-parameter-documented',
                    msg=msg
                )

    def _check_for_new_args(self, doc):
        if not self.base_branch or self._is_new_module():
            return

        with CaptureStd():
            try:
                existing_doc, dummy_examples, dummy_return, existing_metadata = get_docstring(
                    self.base_module, fragment_loader, verbose=True, collection_name=self.collection_name, is_module=True)
                existing_options = existing_doc.get('options', {}) or {}
            except AssertionError:
                fragment = doc['extends_documentation_fragment']
                self.reporter.warning(
                    path=self.object_path,
                    code='missing-existing-doc-fragment',
                    msg='Pre-existing DOCUMENTATION fragment missing: %s' % fragment
                )
                return
            except Exception as e:
                self.reporter.warning_trace(
                    path=self.object_path,
                    tracebk=e
                )
                self.reporter.warning(
                    path=self.object_path,
                    code='unknown-doc-fragment',
                    msg=('Unknown pre-existing DOCUMENTATION error, see TRACE. Submodule refs may need updated')
                )
                return

        try:
            mod_collection_name = existing_doc.get('version_added_collection')
            mod_version_added = self._create_strict_version(
                str(existing_doc.get('version_added', '0.0')),
                collection_name=mod_collection_name)
        except ValueError:
            mod_collection_name = self.collection_name
            mod_version_added = self._create_strict_version('0.0')

        options = doc.get('options', {}) or {}

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = self._create_strict_version(should_be, collection_name='ansible.builtin')

        for option, details in options.items():
            try:
                names = [option] + details.get('aliases', [])
            except (TypeError, AttributeError):
                # Reporting of this syntax error will be handled by schema validation.
                continue

            if any(name in existing_options for name in names):
                # The option already existed. Make sure version_added didn't change.
                for name in names:
                    existing_collection_name = existing_options.get(name, {}).get('version_added_collection')
                    existing_version = existing_options.get(name, {}).get('version_added')
                    if existing_version:
                        break
                current_collection_name = details.get('version_added_collection')
                current_version = details.get('version_added')
                if current_collection_name != existing_collection_name:
                    self.reporter.error(
                        path=self.object_path,
                        code='option-incorrect-version-added-collection',
                        msg=('version_added for existing option (%s) should '
                             'belong to collection %r. Currently belongs to %r' %
                             (option, current_collection_name, existing_collection_name))
                    )
                elif str(current_version) != str(existing_version):
                    self.reporter.error(
                        path=self.object_path,
                        code='option-incorrect-version-added',
                        msg=('version_added for existing option (%s) should '
                             'be %r. Currently %r' %
                             (option, existing_version, current_version))
                    )
                continue

            try:
                collection_name = details.get('version_added_collection')
                version_added = self._create_strict_version(
                    str(details.get('version_added', '0.0')),
                    collection_name=collection_name)
            except ValueError as e:
                # already reported during schema validation
                continue

            if collection_name != self.collection_name:
                continue
            if (strict_ansible_version != mod_version_added and
                    (version_added < strict_ansible_version or
                     strict_ansible_version < version_added)):
                self.reporter.error(
                    path=self.object_path,
                    code='option-incorrect-version-added',
                    msg=('version_added for new option (%s) should '
                         'be %r. Currently %r' %
                         (option, should_be, version_added))
                )

        return existing_doc

    @staticmethod
    def is_on_rejectlist(path):
        base_name = os.path.basename(path)
        file_name = os.path.splitext(base_name)[0]

        if file_name.startswith('_') and os.path.islink(path):
            return True

        if not frozenset((base_name, file_name)).isdisjoint(ModuleValidator.REJECTLIST):
            return True

        for pat in ModuleValidator.REJECTLIST_PATTERNS:
            if fnmatch(base_name, pat):
                return True

        return False

    def validate(self):
        super(ModuleValidator, self).validate()
        if not self._python_module() and not self._powershell_module():
            self.reporter.error(
                path=self.object_path,
                code='invalid-extension',
                msg=('Official Ansible modules must have a .py '
                     'extension for python modules or a .ps1 '
                     'for powershell modules')
            )
            self._python_module_override = True

        if self._python_module() and self.ast is None:
            self.reporter.error(
                path=self.object_path,
                code='python-syntax-error',
                msg='Python SyntaxError while parsing module'
            )
            try:
                compile(self.text, self.path, 'exec')
            except Exception:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=traceback.format_exc()
                )
            return

        end_of_deprecation_should_be_removed_only = False
        if self._python_module():
            doc_info, docs = self._validate_docs()

            # See if current version => deprecated.removed_in, ie, should be docs only
            if docs and docs.get('deprecated', False):

                if 'removed_in' in docs['deprecated']:
                    removed_in = None
                    collection_name = docs['deprecated'].get('removed_from_collection')
                    version = docs['deprecated']['removed_in']
                    if collection_name != self.collection_name:
                        self.reporter.error(
                            path=self.object_path,
                            code='invalid-module-deprecation-source',
                            msg=('The deprecation version for a module must be added in this collection')
                        )
                    else:
                        try:
                            removed_in = self._create_strict_version(str(version), collection_name=collection_name)
                        except ValueError as e:
                            self.reporter.error(
                                path=self.object_path,
                                code='invalid-module-deprecation-version',
                                msg=('The deprecation version %r cannot be parsed: %s' % (version, e))
                            )

                    if removed_in:
                        if not self.collection:
                            strict_ansible_version = self._create_strict_version(
                                '.'.join(ansible_version.split('.')[:2]), self.collection_name)
                            end_of_deprecation_should_be_removed_only = strict_ansible_version >= removed_in
                        elif self.collection_version:
                            strict_ansible_version = self.collection_version
                            end_of_deprecation_should_be_removed_only = strict_ansible_version >= removed_in

                # handle deprecation by date
                if 'removed_at_date' in docs['deprecated']:
                    try:
                        removed_at_date = docs['deprecated']['removed_at_date']
                        if parse_isodate(removed_at_date, allow_date=True) < datetime.date.today():
                            msg = "Module's deprecated.removed_at_date date '%s' is before today" % removed_at_date
                            self.reporter.error(path=self.object_path, code='deprecated-date', msg=msg)
                    except ValueError:
                        # This happens if the date cannot be parsed. This is already checked by the schema.
                        pass

        if self._python_module() and not self._just_docs() and not end_of_deprecation_should_be_removed_only:
            self._validate_ansible_module_call(docs)
            self._check_for_sys_exit()
            self._find_rejectlist_imports()
            main = self._find_main_call()
            self._find_module_utils(main)
            self._find_has_import()
            first_callable = self._get_first_callable()
            self._ensure_imports_below_docs(doc_info, first_callable)
            self._check_for_subprocess()
            self._check_for_os_call()

        if self._powershell_module():
            if self.basename in self.PS_DOC_REJECTLIST:
                return

            self._validate_ps_replacers()
            docs_path = self._find_ps_docs_py_file()

            # We can only validate PowerShell arg spec if it is using the new Ansible.Basic.AnsibleModule util
            pattern = r'(?im)^#\s*ansiblerequires\s+\-csharputil\s*Ansible\.Basic'
            if re.search(pattern, self.text) and self.object_name not in self.PS_ARG_VALIDATE_REJECTLIST:
                with ModuleValidator(docs_path, base_branch=self.base_branch, git_cache=self.git_cache) as docs_mv:
                    docs = docs_mv._validate_docs()[1]
                    self._validate_ansible_module_call(docs)

        self._check_gpl3_header()
        if not self._just_docs() and not end_of_deprecation_should_be_removed_only:
            self._check_interpreter(powershell=self._powershell_module())
            self._check_type_instead_of_isinstance(
                powershell=self._powershell_module()
            )
        if end_of_deprecation_should_be_removed_only:
            # Ensure that `if __name__ == '__main__':` calls `removed_module()` which ensure that the module has no code in
            main = self._find_main_call('removed_module')
            # FIXME: Ensure that the version in the call to removed_module is less than +2.
            # Otherwise it's time to remove the file (This may need to be done in another test to
            # avoid breaking whenever the Ansible version bumps)


class PythonPackageValidator(Validator):
    REJECTLIST_FILES = frozenset(('__pycache__',))

    def __init__(self, path, reporter=None):
        super(PythonPackageValidator, self).__init__(reporter=reporter or Reporter())

        self.path = path
        self.basename = os.path.basename(path)

    @property
    def object_name(self):
        return self.basename

    @property
    def object_path(self):
        return self.path

    def validate(self):
        super(PythonPackageValidator, self).validate()

        if self.basename in self.REJECTLIST_FILES:
            return

        init_file = os.path.join(self.path, '__init__.py')
        if not os.path.exists(init_file):
            self.reporter.error(
                path=self.object_path,
                code='subdirectory-missing-init',
                msg='Ansible module subdirectories must contain an __init__.py'
            )


def setup_collection_loader():
    collections_paths = os.environ.get('ANSIBLE_COLLECTIONS_PATH', '').split(os.pathsep)
    _AnsibleCollectionFinder(collections_paths)


def re_compile(value):
    """
    Argparse expects things to raise TypeError, re.compile raises an re.error
    exception

    This function is a shorthand to convert the re.error exception to a
    TypeError
    """

    try:
        return re.compile(value)
    except re.error as e:
        raise TypeError(e)


def run():
    parser = argparse.ArgumentParser(prog="validate-modules")
    parser.add_argument('modules', nargs='+',
                        help='Path to module or module directory')
    parser.add_argument('-w', '--warnings', help='Show warnings',
                        action='store_true')
    parser.add_argument('--exclude', help='RegEx exclusion pattern',
                        type=re_compile)
    parser.add_argument('--arg-spec', help='Analyze module argument spec',
                        action='store_true', default=False)
    parser.add_argument('--base-branch', default=None,
                        help='Used in determining if new options were added')
    parser.add_argument('--format', choices=['json', 'plain'], default='plain',
                        help='Output format. Default: "%(default)s"')
    parser.add_argument('--output', default='-',
                        help='Output location, use "-" for stdout. '
                             'Default "%(default)s"')
    parser.add_argument('--collection',
                        help='Specifies the path to the collection, when '
                             'validating files within a collection. Ensure '
                             'that ANSIBLE_COLLECTIONS_PATH is set so the '
                             'contents of the collection can be located')
    parser.add_argument('--collection-version',
                        help='The collection\'s version number used to check '
                             'deprecations')

    args = parser.parse_args()

    args.modules = [m.rstrip('/') for m in args.modules]

    reporter = Reporter()
    git_cache = GitCache(args.base_branch)

    check_dirs = set()

    routing = None
    if args.collection:
        setup_collection_loader()
        routing_file = 'meta/runtime.yml'
        # Load meta/runtime.yml if it exists, as it may contain deprecation information
        if os.path.isfile(routing_file):
            try:
                with open(routing_file) as f:
                    routing = yaml.safe_load(f)
            except yaml.error.MarkedYAMLError as ex:
                print('%s:%d:%d: YAML load failed: %s' % (routing_file, ex.context_mark.line + 1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
            except Exception as ex:  # pylint: disable=broad-except
                print('%s:%d:%d: YAML load failed: %s' % (routing_file, 0, 0, re.sub(r'\s+', ' ', str(ex))))

    for module in args.modules:
        if os.path.isfile(module):
            path = module
            if args.exclude and args.exclude.search(path):
                continue
            if ModuleValidator.is_on_rejectlist(path):
                continue
            with ModuleValidator(path, collection=args.collection, collection_version=args.collection_version,
                                 analyze_arg_spec=args.arg_spec, base_branch=args.base_branch,
                                 git_cache=git_cache, reporter=reporter, routing=routing) as mv1:
                mv1.validate()
                check_dirs.add(os.path.dirname(path))

        for root, dirs, files in os.walk(module):
            basedir = root[len(module) + 1:].split('/', 1)[0]
            if basedir in REJECTLIST_DIRS:
                continue
            for dirname in dirs:
                if root == module and dirname in REJECTLIST_DIRS:
                    continue
                path = os.path.join(root, dirname)
                if args.exclude and args.exclude.search(path):
                    continue
                check_dirs.add(path)

            for filename in files:
                path = os.path.join(root, filename)
                if args.exclude and args.exclude.search(path):
                    continue
                if ModuleValidator.is_on_rejectlist(path):
                    continue
                with ModuleValidator(path, collection=args.collection, collection_version=args.collection_version,
                                     analyze_arg_spec=args.arg_spec, base_branch=args.base_branch,
                                     git_cache=git_cache, reporter=reporter, routing=routing) as mv2:
                    mv2.validate()

    if not args.collection:
        for path in sorted(check_dirs):
            pv = PythonPackageValidator(path, reporter=reporter)
            pv.validate()

    if args.format == 'plain':
        sys.exit(reporter.plain(warnings=args.warnings, output=args.output))
    else:
        sys.exit(reporter.json(warnings=args.warnings, output=args.output))


class GitCache:
    def __init__(self, base_branch):
        self.base_branch = base_branch

        if self.base_branch:
            self.base_tree = self._git(['ls-tree', '-r', '--name-only', self.base_branch, 'lib/ansible/modules/'])
        else:
            self.base_tree = []

        try:
            self.head_tree = self._git(['ls-tree', '-r', '--name-only', 'HEAD', 'lib/ansible/modules/'])
        except GitError as ex:
            if ex.status == 128:
                # fallback when there is no .git directory
                self.head_tree = self._get_module_files()
            else:
                raise
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                # fallback when git is not installed
                self.head_tree = self._get_module_files()
            else:
                raise

        self.base_module_paths = dict((os.path.basename(p), p) for p in self.base_tree if os.path.splitext(p)[1] in ('.py', '.ps1'))

        self.base_module_paths.pop('__init__.py', None)

        self.head_aliased_modules = set()

        for path in self.head_tree:
            filename = os.path.basename(path)

            if filename.startswith('_') and filename != '__init__.py':
                if os.path.islink(path):
                    self.head_aliased_modules.add(os.path.basename(os.path.realpath(path)))

    @staticmethod
    def _get_module_files():
        module_files = []

        for (dir_path, dir_names, file_names) in os.walk('lib/ansible/modules/'):
            for file_name in file_names:
                module_files.append(os.path.join(dir_path, file_name))

        return module_files

    @staticmethod
    def _git(args):
        cmd = ['git'] + args
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise GitError(stderr, p.returncode)
        return stdout.decode('utf-8').splitlines()


class GitError(Exception):
    def __init__(self, message, status):
        super(GitError, self).__init__(message)

        self.status = status


def main():
    try:
        run()
    except KeyboardInterrupt:
        pass
