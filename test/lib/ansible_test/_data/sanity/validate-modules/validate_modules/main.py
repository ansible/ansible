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
from distutils.version import StrictVersion
from fnmatch import fnmatch

from ansible import __version__ as ansible_version
from ansible.executor.module_common import REPLACER_WINDOWS
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils._text import to_bytes
from ansible.plugins.loader import fragment_loader
from ansible.utils.collection_loader import AnsibleCollectionLoader
from ansible.utils.plugin_docs import BLACKLIST, add_fragments, get_docstring

from .module_args import AnsibleModuleImportError, AnsibleModuleNotInitialized, get_argument_spec

from .schema import ansible_module_kwargs_schema, doc_schema, metadata_1_1_schema, return_schema

from .utils import CaptureStd, NoArgsAnsibleModule, compare_unordered_lists, is_empty, parse_yaml
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import PY3, with_metaclass
from ansible.module_utils.basic import FILE_COMMON_ARGUMENTS

if PY3:
    # Because there is no ast.TryExcept in Python 3 ast module
    TRY_EXCEPT = ast.Try
    # REPLACER_WINDOWS from ansible.executor.module_common is byte
    # string but we need unicode for Python 3
    REPLACER_WINDOWS = REPLACER_WINDOWS.decode('utf-8')
else:
    TRY_EXCEPT = ast.TryExcept

BLACKLIST_DIRS = frozenset(('.git', 'test', '.github', '.idea'))
INDENT_REGEX = re.compile(r'([\t]*)')
TYPE_REGEX = re.compile(r'.*(if|or)(\s+[^"\']*|\s+)(?<!_)(?<!str\()type\([^)].*')
SYS_EXIT_REGEX = re.compile(r'[^#]*sys.exit\s*\(.*')
BLACKLIST_IMPORTS = {
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
                print('%(path)s:%(line)d:%(column)d: E%(code)d %(msg)s' % error)
                ret.append(1)
            if warnings:
                for warning in report['warnings']:
                    warning['path'] = path
                    print('%(path)s:%(line)d:%(column)d: W%(code)d %(msg)s' % warning)

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
    BLACKLIST_PATTERNS = ('.git*', '*.pyc', '*.pyo', '.*', '*.md', '*.rst', '*.txt')
    BLACKLIST_FILES = frozenset(('.git', '.gitignore', '.travis.yml',
                                 'shippable.yml',
                                 '.gitattributes', '.gitmodules', 'COPYING',
                                 '__init__.py', 'VERSION', 'test-docs.sh'))
    BLACKLIST = BLACKLIST_FILES.union(BLACKLIST['MODULE'])

    PS_DOC_BLACKLIST = frozenset((
        'async_status.ps1',
        'slurp.ps1',
        'setup.ps1'
    ))
    PS_ARG_VALIDATE_BLACKLIST = frozenset((
        'win_dsc.ps1',  # win_dsc is a dynamic arg spec, the docs won't ever match
    ))

    WHITELIST_FUTURE_IMPORTS = frozenset(('absolute_import', 'division', 'print_function'))

    def __init__(self, path, analyze_arg_spec=False, collection=None, base_branch=None, git_cache=None, reporter=None):
        super(ModuleValidator, self).__init__(reporter=reporter or Reporter())

        self.path = path
        self.basename = os.path.basename(self.path)
        self.name = os.path.splitext(self.basename)[0]

        self.analyze_arg_spec = analyze_arg_spec

        self.collection = collection

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
                            if future_import.name not in self.WHITELIST_FUTURE_IMPORTS:
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

    def _find_blacklist_imports(self):
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
                for blacklist_import, options in BLACKLIST_IMPORTS.items():
                    if re.search(blacklist_import, name.name):
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
                        if future_import.name not in self.WHITELIST_FUTURE_IMPORTS:
                            self.reporter.error(
                                path=self.object_path,
                                code='illegal-future-imports',
                                msg=('Only the following from __future__ imports are allowed: %s'
                                     % ', '.join(self.WHITELIST_FUTURE_IMPORTS)),
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
                             'DOCUMENTATION/EXAMPLES/RETURN/ANSIBLE_METADATA.'),
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
                                     'DOCUMENTATION/EXAMPLES/RETURN/'
                                     'ANSIBLE_METADATA.'),
                                line=child.lineno
                            )
                            break

        for import_line in import_lines:
            if not (max_doc_line < import_line < first_callable):
                msg = (
                    'import-placement',
                    ('Imports should be directly below DOCUMENTATION/EXAMPLES/'
                     'RETURN/ANSIBLE_METADATA.')
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
        if self.object_name in self.PS_DOC_BLACKLIST:
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
            'ANSIBLE_METADATA': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            }
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
                    elif grandchild.id == 'ANSIBLE_METADATA':
                        docs['ANSIBLE_METADATA']['value'] = child.value
                        docs['ANSIBLE_METADATA']['lineno'] = child.lineno
                        try:
                            docs['ANSIBLE_METADATA']['end_lineno'] = (
                                child.lineno + len(child.value.s.splitlines())
                            )
                        except AttributeError:
                            docs['ANSIBLE_METADATA']['end_lineno'] = (
                                child.value.values[-1].lineno
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
                code=error_code,
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

        if self.object_name.startswith('_') and not os.path.islink(self.object_path):
            filename_deprecated_or_removed = True

        # Have to check the metadata first so that we know if the module is removed or deprecated
        metadata = None
        if not self.collection:
            if not bool(doc_info['ANSIBLE_METADATA']['value']):
                self.reporter.error(
                    path=self.object_path,
                    code='missing-metadata',
                    msg='No ANSIBLE_METADATA provided'
                )
            else:
                if isinstance(doc_info['ANSIBLE_METADATA']['value'], ast.Dict):
                    metadata = ast.literal_eval(
                        doc_info['ANSIBLE_METADATA']['value']
                    )
                else:
                    self.reporter.error(
                        path=self.object_path,
                        code='missing-metadata-format',
                        msg='ANSIBLE_METADATA was not provided as a dict, YAML not supported'
                    )

            if metadata:
                self._validate_docs_schema(metadata, metadata_1_1_schema(),
                                           'ANSIBLE_METADATA', 'invalid-metadata-type')
                # We could validate these via the schema if we knew what the values are ahead of
                # time.  We can figure that out for deprecated but we can't for removed.  Only the
                # metadata has that information.
                if 'removed' in metadata['status']:
                    removed = True
                if 'deprecated' in metadata['status']:
                    deprecated = True
                if (deprecated or removed) and len(metadata['status']) > 1:
                    self.reporter.error(
                        path=self.object_path,
                        code='missing-metadata-status',
                        msg='ANSIBLE_METADATA.status must be exactly one of "deprecated" or "removed"'
                    )

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
                            get_docstring(self.path, fragment_loader, verbose=True)
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
                        add_fragments(doc, self.object_path, fragment_loader=fragment_loader)

                    if 'options' in doc and doc['options'] is None:
                        self.reporter.error(
                            path=self.object_path,
                            code='invalid-documentation-options',
                            msg='DOCUMENTATION.options must be a dictionary/hash when used',
                        )

                    if 'deprecated' in doc and doc.get('deprecated'):
                        doc_deprecated = True
                    else:
                        doc_deprecated = False

                    if os.path.islink(self.object_path):
                        # This module has an alias, which we can tell as it's a symlink
                        # Rather than checking for `module: $filename` we need to check against the true filename
                        self._validate_docs_schema(
                            doc,
                            doc_schema(
                                os.readlink(self.object_path).split('.')[0],
                                version_added=not bool(self.collection)
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
                                version_added=not bool(self.collection)
                            ),
                            'DOCUMENTATION',
                            'invalid-documentation',
                        )

                    if not self.collection:
                        existing_doc = self._check_for_new_args(doc, metadata)
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
                self._validate_docs_schema(data, return_schema, 'RETURN', 'return-syntax-error')

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
                msg='Module deprecation/removed must agree in Metadata, by prepending filename with'
                    ' "_", and setting DOCUMENTATION.deprecated for deprecation or by removing all'
                    ' documentation for removed'
            )

        return doc_info, doc

    def _check_version_added(self, doc, existing_doc):
        version_added_raw = doc.get('version_added')
        try:
            version_added = StrictVersion(str(doc.get('version_added', '0.0') or '0.0'))
        except ValueError:
            version_added = doc.get('version_added', '0.0')
            if self._is_new_module() or version_added != 'historical':
                self.reporter.error(
                    path=self.object_path,
                    code='module-invalid-version-added',
                    msg='version_added is not a valid version number: %r' % version_added
                )
                return

        if existing_doc and str(version_added_raw) != str(existing_doc.get('version_added')):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (existing_doc.get('version_added'),
                                                                  version_added_raw)
            )

        if not self._is_new_module():
            return

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = StrictVersion(should_be)

        if (version_added < strict_ansible_version or
                strict_ansible_version < version_added):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (should_be, version_added_raw)
            )

    def _validate_ansible_module_call(self, docs):
        try:
            spec, args, kwargs = get_argument_spec(self.path, self.collection)
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

        self._validate_docs_schema(kwargs, ansible_module_kwargs_schema, 'AnsibleModule', 'invalid-ansiblemodule-schema')

        self._validate_argument_spec(docs, spec, kwargs)

    def _validate_argument_spec(self, docs, spec, kwargs, context=None):
        if not self.analyze_arg_spec:
            return

        if docs is None:
            docs = {}

        if context is None:
            context = []

        try:
            if not context:
                add_fragments(docs, self.object_path, fragment_loader=fragment_loader)
        except Exception:
            # Cannot merge fragments
            return

        # Use this to access type checkers later
        module = NoArgsAnsibleModule({})

        provider_args = set()
        args_from_argspec = set()
        deprecated_args_from_argspec = set()
        for arg, data in spec.items():
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
            if not data.get('removed_in_version', None):
                args_from_argspec.add(arg)
                args_from_argspec.update(data.get('aliases', []))
            else:
                deprecated_args_from_argspec.add(arg)
                deprecated_args_from_argspec.update(data.get('aliases', []))
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
                _type_checker = module._CHECK_ARGUMENT_TYPES_DISPATCHER.get(_type)

            _elements = data.get('elements')
            if _elements:
                if not callable(_elements):
                    module._CHECK_ARGUMENT_TYPES_DISPATCHER.get(_elements)
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
            elif data.get('default') is None and _type == 'bool' and 'options' not in data:
                arg_default = False

            try:
                doc_default = None
                doc_options_arg = (docs.get('options', {}) or {}).get(arg, {})
                if 'default' in doc_options_arg and not is_empty(doc_options_arg['default']):
                    with CaptureStd():
                        doc_default = _type_checker(doc_options_arg['default'])
                elif doc_options_arg.get('default') is None and _type == 'bool' and 'suboptions' not in doc_options_arg:
                    doc_default = False
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

            doc_type = docs.get('options', {}).get(arg, {}).get('type')
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
                    msg += "implies type as 'str' but documentation defines as %r" % doc_type
                    self.reporter.error(
                        path=self.object_path,
                        code='implied-parameter-type-mismatch',
                        msg=msg
                    )

            doc_choices = []
            try:
                for choice in docs.get('options', {}).get(arg, {}).get('choices', []):
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

            spec_suboptions = data.get('options')
            doc_suboptions = docs.get('options', {}).get(arg, {}).get('suboptions', {})
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
                self._validate_argument_spec({'options': doc_suboptions}, spec_suboptions, kwargs, context=context + [arg])

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
            file_common_arguments = set()
            for arg, data in FILE_COMMON_ARGUMENTS.items():
                file_common_arguments.add(arg)
                file_common_arguments.update(data.get('aliases', []))

            args_from_docs = set()
            for arg, data in docs.get('options', {}).items():
                args_from_docs.add(arg)
                args_from_docs.update(data.get('aliases', []))

            args_missing_from_docs = args_from_argspec.difference(args_from_docs)
            docs_missing_from_args = args_from_docs.difference(args_from_argspec | deprecated_args_from_argspec)
            for arg in args_missing_from_docs:
                # args_from_argspec contains undocumented argument
                if kwargs.get('add_file_common_args', False) and arg in file_common_arguments:
                    # add_file_common_args is handled in AnsibleModule, and not exposed earlier
                    continue
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
                # args_from_docs contains argument not in the argument_spec
                if kwargs.get('add_file_common_args', False) and arg in file_common_arguments:
                    # add_file_common_args is handled in AnsibleModule, and not exposed earlier
                    continue
                msg = "Argument '%s'" % arg
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " is listed in DOCUMENTATION.options, but not accepted by the module argument_spec"
                self.reporter.error(
                    path=self.object_path,
                    code='nonexistent-parameter-documented',
                    msg=msg
                )

    def _check_for_new_args(self, doc, metadata):
        if not self.base_branch or self._is_new_module():
            return

        with CaptureStd():
            try:
                existing_doc, dummy_examples, dummy_return, existing_metadata = get_docstring(self.base_module, fragment_loader, verbose=True)
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
            mod_version_added = StrictVersion()
            mod_version_added.parse(
                str(existing_doc.get('version_added', '0.0'))
            )
        except ValueError:
            mod_version_added = StrictVersion('0.0')

        if self.base_branch and 'stable-' in self.base_branch:
            metadata.pop('metadata_version', None)
            metadata.pop('version', None)
            if metadata != existing_metadata:
                self.reporter.error(
                    path=self.object_path,
                    code='metadata-changed',
                    msg=('ANSIBLE_METADATA cannot be changed in a point release for a stable branch')
                )

        options = doc.get('options', {}) or {}

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = StrictVersion(should_be)

        for option, details in options.items():
            try:
                names = [option] + details.get('aliases', [])
            except (TypeError, AttributeError):
                # Reporting of this syntax error will be handled by schema validation.
                continue

            if any(name in existing_options for name in names):
                for name in names:
                    existing_version = existing_options.get(name, {}).get('version_added')
                    if existing_version:
                        break
                current_version = details.get('version_added')
                if str(current_version) != str(existing_version):
                    self.reporter.error(
                        path=self.object_path,
                        code='option-incorrect-version-added',
                        msg=('version_added for new option (%s) should '
                             'be %r. Currently %r' %
                             (option, existing_version, current_version))
                    )
                continue

            try:
                version_added = StrictVersion()
                version_added.parse(
                    str(details.get('version_added', '0.0'))
                )
            except ValueError:
                version_added = details.get('version_added', '0.0')
                self.reporter.error(
                    path=self.object_path,
                    code='module-invalid-version-added-number',
                    msg=('version_added for new option (%s) '
                         'is not a valid version number: %r' %
                         (option, version_added))
                )
                continue
            except Exception:
                # If there is any other exception it should have been caught
                # in schema validation, so we won't duplicate errors by
                # listing it again
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
    def is_blacklisted(path):
        base_name = os.path.basename(path)
        file_name = os.path.splitext(base_name)[0]

        if file_name.startswith('_') and os.path.islink(path):
            return True

        if not frozenset((base_name, file_name)).isdisjoint(ModuleValidator.BLACKLIST):
            return True

        for pat in ModuleValidator.BLACKLIST_PATTERNS:
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
            if isinstance(doc_info['ANSIBLE_METADATA']['value'], ast.Dict) and 'removed' in ast.literal_eval(doc_info['ANSIBLE_METADATA']['value'])['status']:
                end_of_deprecation_should_be_removed_only = True
            elif docs and 'deprecated' in docs and docs['deprecated'] is not None and 'removed_in' in docs['deprecated']:
                try:
                    removed_in = StrictVersion(str(docs['deprecated']['removed_in']))
                except ValueError:
                    end_of_deprecation_should_be_removed_only = False
                else:
                    strict_ansible_version = StrictVersion('.'.join(ansible_version.split('.')[:2]))
                    end_of_deprecation_should_be_removed_only = strict_ansible_version >= removed_in

        if self._python_module() and not self._just_docs() and not end_of_deprecation_should_be_removed_only:
            self._validate_ansible_module_call(docs)
            self._check_for_sys_exit()
            self._find_blacklist_imports()
            main = self._find_main_call()
            self._find_module_utils(main)
            self._find_has_import()
            first_callable = self._get_first_callable()
            self._ensure_imports_below_docs(doc_info, first_callable)
            self._check_for_subprocess()
            self._check_for_os_call()

        if self._powershell_module():
            self._validate_ps_replacers()
            docs_path = self._find_ps_docs_py_file()

            # We can only validate PowerShell arg spec if it is using the new Ansible.Basic.AnsibleModule util
            pattern = r'(?im)^#\s*ansiblerequires\s+\-csharputil\s*Ansible\.Basic'
            if re.search(pattern, self.text) and self.object_name not in self.PS_ARG_VALIDATE_BLACKLIST:
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
    BLACKLIST_FILES = frozenset(('__pycache__',))

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

        if self.basename in self.BLACKLIST_FILES:
            return

        init_file = os.path.join(self.path, '__init__.py')
        if not os.path.exists(init_file):
            self.reporter.error(
                path=self.object_path,
                code='subdirectory-missing-init',
                msg='Ansible module subdirectories must contain an __init__.py'
            )


def setup_collection_loader():
    def get_source(self, fullname):
        mod = sys.modules.get(fullname)
        if not mod:
            mod = self.load_module(fullname)

        with open(to_bytes(mod.__file__), 'rb') as mod_file:
            source = mod_file.read()

        return source

    def get_code(self, fullname):
        return compile(source=self.get_source(fullname), filename=self.get_filename(fullname), mode='exec', flags=0, dont_inherit=True)

    def is_package(self, fullname):
        return self.get_filename(fullname).endswith('__init__.py')

    def get_filename(self, fullname):
        mod = sys.modules.get(fullname) or self.load_module(fullname)

        return mod.__file__

    # monkeypatch collection loader to work with runpy
    # remove this (and the associated code above) once implemented natively in the collection loader
    AnsibleCollectionLoader.get_source = get_source
    AnsibleCollectionLoader.get_code = get_code
    AnsibleCollectionLoader.is_package = is_package
    AnsibleCollectionLoader.get_filename = get_filename

    collection_loader = AnsibleCollectionLoader()

    # allow importing code from collections when testing a collection
    # noinspection PyCallingNonCallable
    sys.meta_path.insert(0, collection_loader)


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
                             'that ANSIBLE_COLLECTIONS_PATHS is set so the '
                             'contents of the collection can be located')

    args = parser.parse_args()

    args.modules[:] = [m.rstrip('/') for m in args.modules]

    reporter = Reporter()
    git_cache = GitCache(args.base_branch)

    check_dirs = set()

    if args.collection:
        setup_collection_loader()

    for module in args.modules:
        if os.path.isfile(module):
            path = module
            if args.exclude and args.exclude.search(path):
                continue
            if ModuleValidator.is_blacklisted(path):
                continue
            with ModuleValidator(path, collection=args.collection, analyze_arg_spec=args.arg_spec,
                                 base_branch=args.base_branch, git_cache=git_cache, reporter=reporter) as mv1:
                mv1.validate()
                check_dirs.add(os.path.dirname(path))

        for root, dirs, files in os.walk(module):
            basedir = root[len(module) + 1:].split('/', 1)[0]
            if basedir in BLACKLIST_DIRS:
                continue
            for dirname in dirs:
                if root == module and dirname in BLACKLIST_DIRS:
                    continue
                path = os.path.join(root, dirname)
                if args.exclude and args.exclude.search(path):
                    continue
                check_dirs.add(path)

            for filename in files:
                path = os.path.join(root, filename)
                if args.exclude and args.exclude.search(path):
                    continue
                if ModuleValidator.is_blacklisted(path):
                    continue
                with ModuleValidator(path, collection=args.collection, analyze_arg_spec=args.arg_spec,
                                     base_branch=args.base_branch, git_cache=git_cache, reporter=reporter) as mv2:
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
