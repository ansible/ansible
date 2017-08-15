#!/usr/bin/env python
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

from __future__ import print_function

import abc
import argparse
import ast
import json
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
from ansible.utils.plugin_docs import BLACKLIST, get_docstring

from module_args import get_argument_spec

from schema import doc_schema, metadata_schema, return_schema

from utils import CaptureStd, parse_yaml
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import PY3, with_metaclass

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
TYPE_REGEX = re.compile(r'.*(if|or)(\s+[^"\']*|\s+)(?<!_)(?<!str\()type\(.*')
BLACKLIST_IMPORTS = {
    'requests': {
        'new_only': True,
        'error': {
            'code': 203,
            'msg': ('requests import found, should use '
                    'ansible.module_utils.urls instead')
        }
    },
    'boto(?:\.|$)': {
        'new_only': True,
        'error': {
            'code': 204,
            'msg': 'boto import found, new modules should use boto3'
        }
    },
}


class ReporterEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Exception):
            return str(o)

        return json.JSONEncoder.default(self, o)


class Reporter(object):
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
        ret = [len(r['errors']) for _, r in self.files.items()]

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

    WHITELIST_FUTURE_IMPORTS = frozenset(('absolute_import', 'division', 'print_function'))

    def __init__(self, path, analyze_arg_spec=False, base_branch=None, git_cache=None, reporter=None):
        super(ModuleValidator, self).__init__(reporter=reporter or Reporter())

        self.path = path
        self.basename = os.path.basename(self.path)
        self.name, _ = os.path.splitext(self.basename)

        self.analyze_arg_spec = analyze_arg_spec

        self.base_branch = base_branch
        self.git_cache = git_cache or GitCache()

        self._python_module_override = False

        with open(path) as f:
            self.text = f.read()
        self.length = len(self.text.splitlines())
        try:
            self.ast = ast.parse(self.text)
        except:
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
        except:
            pass

    @property
    def object_name(self):
        return self.basename

    @property
    def object_path(self):
        return self.path

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
                    code=102,
                    msg='Interpreter line is not "#!powershell"'
                )
            return

        if not self.text.startswith('#!/usr/bin/python'):
            self.reporter.error(
                path=self.object_path,
                code=101,
                msg='Interpreter line is not "#!/usr/bin/python"'
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
                    code=403,
                    msg=('Type comparison using type() found. '
                         'Use isinstance() instead'),
                    line=line_no + 1
                )

    def _check_for_sys_exit(self):
        if 'sys.exit(' in self.text:
            # TODO: Add line/col
            self.reporter.error(
                path=self.object_path,
                code=205,
                msg='sys.exit() call found. Should be exit_json/fail_json'
            )

    def _check_for_gpl3_header(self):
        if ('GNU General Public License' not in self.text and
                'version 3' not in self.text):
            self.reporter.error(
                path=self.object_path,
                code=105,
                msg='GPLv3 license header not found'
            )

    def _check_for_tabs(self):
        for line_no, line in enumerate(self.text.splitlines()):
            indent = INDENT_REGEX.search(line)
            if indent and '\t' in line:
                index = line.index('\t')
                self.reporter.error(
                    path=self.object_path,
                    code=402,
                    msg='indentation contains tabs',
                    line=line_no + 1,
                    column=index
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
                                208,
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

        if not linenos:
            self.reporter.error(
                path=self.object_path,
                code=201,
                msg='Did not find a module_utils import'
            )
        elif not found_basic:
            self.reporter.warning(
                path=self.object_path,
                code=292,
                msg='Did not find "ansible.module_utils.basic" import'
            )

        return linenos

    def _get_first_callable(self):
        linenos = []
        for child in self.ast.body:
            if isinstance(child, (ast.FunctionDef, ast.ClassDef)):
                linenos.append(child.lineno)

        return min(linenos)

    def _find_main_call(self):
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
            if isinstance(child, ast.Expr):
                if isinstance(child.value, ast.Call):
                    if (isinstance(child.value.func, ast.Name) and
                            child.value.func.id == 'main'):
                        lineno = child.lineno
                        if lineno < self.length - 1:
                            self.reporter.error(
                                path=self.object_path,
                                code=104,
                                msg='Call to main() not the last line',
                                line=lineno
                            )

        if not lineno:
            self.reporter.error(
                path=self.object_path,
                code=103,
                msg='Did not find a call to main'
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
                            if target.id.lower().startswith('has_'):
                                found_has = True
            if found_try_except_import and not found_has:
                # TODO: Add line/col
                self.reporter.warning(
                    path=self.object_path,
                    code=291,
                    msg='Found Try/Except block without HAS_ assginment'
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
                                code=209,
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
                        code=106,
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
                                code=106,
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
                    107,
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

    def _find_ps_replacers(self):
        ps_module_util_template = '#Requires -Module Ansible.ModuleUtils.'
        if ps_module_util_template not in self.text and REPLACER_WINDOWS not in self.text:
            self.reporter.error(
                path=self.object_path,
                code=207,
                msg='"%s" not found in module' % ps_module_util_template
            )

    def _find_ps_docs_py_file(self):
        if self.object_name in self.PS_DOC_BLACKLIST:
            return
        py_path = self.path.replace('.ps1', '.py')
        if not os.path.isfile(py_path):
            self.reporter.error(
                path=self.object_path,
                code=503,
                msg='Missing python documentation file'
            )

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

            self.reporter.error(
                path=self.object_path,
                code=error_code,
                msg='%s.%s: %s' % (name, '.'.join(path), error_message)
            )

    def _validate_docs(self):
        doc_info = self._get_docs()
        deprecated = False
        if not bool(doc_info['DOCUMENTATION']['value']):
            self.reporter.error(
                path=self.object_path,
                code=301,
                msg='No DOCUMENTATION provided'
            )
        else:
            doc, errors, traces = parse_yaml(
                doc_info['DOCUMENTATION']['value'],
                doc_info['DOCUMENTATION']['lineno'],
                self.name, 'DOCUMENTATION'
            )
            for error in errors:
                self.reporter.error(
                    path=self.object_path,
                    code=302,
                    **error
                )
            for trace in traces:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=trace
                )
            if not errors and not traces:
                with CaptureStd():
                    try:
                        get_docstring(self.path, verbose=True)
                    except AssertionError:
                        fragment = doc['extends_documentation_fragment']
                        self.reporter.error(
                            path=self.object_path,
                            code=303,
                            msg='DOCUMENTATION fragment missing: %s' % fragment
                        )
                    except Exception:
                        self.reporter.trace(
                            path=self.object_path,
                            tracebk=traceback.format_exc()
                        )
                        self.reporter.error(
                            path=self.object_path,
                            code=304,
                            msg='Unknown DOCUMENTATION error, see TRACE'
                        )

                if 'options' in doc and doc['options'] is None and doc.get('extends_documentation_fragment'):
                    self.reporter.error(
                        path=self.object_path,
                        code=304,
                        msg=('DOCUMENTATION.options must be a dictionary/hash when used '
                             'with DOCUMENTATION.extends_documentation_fragment')
                    )

                if self.object_name.startswith('_') and not os.path.islink(self.object_path):
                    deprecated = True
                    if 'deprecated' not in doc or not doc.get('deprecated'):
                        self.reporter.error(
                            path=self.object_path,
                            code=318,
                            msg='Module deprecated, but DOCUMENTATION.deprecated is missing'
                        )

                self._validate_docs_schema(doc, doc_schema(self.object_name.split('.')[0]), 'DOCUMENTATION', 305)
                self._check_version_added(doc)
                self._check_for_new_args(doc)

        if not bool(doc_info['EXAMPLES']['value']):
            self.reporter.error(
                path=self.object_path,
                code=310,
                msg='No EXAMPLES provided'
            )
        else:
            _, errors, traces = parse_yaml(doc_info['EXAMPLES']['value'],
                                           doc_info['EXAMPLES']['lineno'],
                                           self.name, 'EXAMPLES', load_all=True)
            for error in errors:
                self.reporter.error(
                    path=self.object_path,
                    code=311,
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
                    code=312,
                    msg='No RETURN provided'
                )
            else:
                self.reporter.warning(
                    path=self.object_path,
                    code=312,
                    msg='No RETURN provided'
                )
        else:
            data, errors, traces = parse_yaml(doc_info['RETURN']['value'],
                                              doc_info['RETURN']['lineno'],
                                              self.name, 'RETURN')
            if data:
                for ret_key in data:
                    self._validate_docs_schema(data[ret_key], return_schema(data[ret_key]), 'RETURN.%s' % ret_key, 319)

            for error in errors:
                self.reporter.error(
                    path=self.object_path,
                    code=313,
                    **error
                )
            for trace in traces:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=trace
                )

        if not bool(doc_info['ANSIBLE_METADATA']['value']):
            self.reporter.error(
                path=self.object_path,
                code=314,
                msg='No ANSIBLE_METADATA provided'
            )
        else:
            metadata = None
            if isinstance(doc_info['ANSIBLE_METADATA']['value'], ast.Dict):
                metadata = ast.literal_eval(
                    doc_info['ANSIBLE_METADATA']['value']
                )
            else:
                metadata, errors, traces = parse_yaml(
                    doc_info['ANSIBLE_METADATA']['value'].s,
                    doc_info['ANSIBLE_METADATA']['lineno'],
                    self.name, 'ANSIBLE_METADATA'
                )
                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code=315,
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )

            if metadata:
                self._validate_docs_schema(metadata, metadata_schema(deprecated),
                                           'ANSIBLE_METADATA', 316)

        return doc_info

    def _check_version_added(self, doc):
        if not self._is_new_module():
            return

        try:
            version_added = StrictVersion(str(doc.get('version_added', '0.0')))
        except ValueError:
            version_added = doc.get('version_added', '0.0')
            self.reporter.error(
                path=self.object_path,
                code=306,
                msg='version_added is not a valid version number: %r' % version_added
            )
            return

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = StrictVersion(should_be)

        if (version_added < strict_ansible_version or
                strict_ansible_version < version_added):
            self.reporter.error(
                path=self.object_path,
                code=307,
                msg='version_added should be %s. Currently %s' % (should_be, version_added)
            )

    def _validate_argument_spec(self):
        if not self.analyze_arg_spec:
            return
        spec = get_argument_spec(self.path)
        for arg, data in spec.items():
            if data.get('required') and data.get('default', object) != object:
                self.reporter.error(
                    path=self.object_path,
                    code=317,
                    msg=('"%s" is marked as required but specifies '
                         'a default. Arguments with a default '
                         'should not be marked as required' % arg)
                )

    def _check_for_new_args(self, doc):
        if not self.base_branch or self._is_new_module():
            return

        with CaptureStd():
            try:
                existing_doc, _, _, _ = get_docstring(self.base_module, verbose=True)
                existing_options = existing_doc.get('options', {})
            except AssertionError:
                fragment = doc['extends_documentation_fragment']
                self.reporter.warning(
                    path=self.object_path,
                    code=392,
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
                    code=391,
                    msg=('Unknown pre-existing DOCUMENTATION '
                         'error, see TRACE. Submodule refs may '
                         'need updated')
                )
                return

        try:
            mod_version_added = StrictVersion(
                str(existing_doc.get('version_added', '0.0'))
            )
        except ValueError:
            mod_version_added = StrictVersion('0.0')

        options = doc.get('options', {})

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = StrictVersion(should_be)

        for option, details in options.items():
            names = [option] + details.get('aliases', [])

            if any(name in existing_options for name in names):
                continue

            try:
                version_added = StrictVersion(
                    str(details.get('version_added', '0.0'))
                )
            except ValueError:
                version_added = details.get('version_added', '0.0')
                self.reporter.error(
                    path=self.object_path,
                    code=308,
                    msg=('version_added for new option (%s) '
                         'is not a valid version number: %r' %
                         (option, version_added))
                )
                continue
            except:
                # If there is any other exception it should have been caught
                # in schema validation, so we won't duplicate errors by
                # listing it again
                continue

            if (strict_ansible_version != mod_version_added and
                    (version_added < strict_ansible_version or
                     strict_ansible_version < version_added)):
                self.reporter.error(
                    path=self.object_path,
                    code=309,
                    msg=('version_added for new option (%s) should '
                         'be %s. Currently %s' %
                         (option, should_be, version_added))
                )

    @staticmethod
    def is_blacklisted(path):
        base_name = os.path.basename(path)
        file_name, _ = os.path.splitext(base_name)

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
                code=501,
                msg=('Official Ansible modules must have a .py '
                     'extension for python modules or a .ps1 '
                     'for powershell modules')
            )
            self._python_module_override = True

        if self._python_module() and self.ast is None:
            self.reporter.error(
                path=self.object_path,
                code=401,
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

        if self._python_module():
            doc_info = self._validate_docs()

        if self._python_module() and not self._just_docs():
            self._validate_argument_spec()
            self._check_for_sys_exit()
            self._find_blacklist_imports()
            main = self._find_main_call()
            self._find_module_utils(main)
            self._find_has_import()
            self._check_for_tabs()
            first_callable = self._get_first_callable()
            self._ensure_imports_below_docs(doc_info, first_callable)

        if self._powershell_module():
            self._find_ps_replacers()
            self._find_ps_docs_py_file()

        self._check_for_gpl3_header()
        if not self._just_docs():
            self._check_interpreter(powershell=self._powershell_module())
            self._check_type_instead_of_isinstance(
                powershell=self._powershell_module()
            )


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
                code=502,
                msg='Ansible module subdirectories must contain an __init__.py'
            )


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


def main():
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

    args = parser.parse_args()

    args.modules[:] = [m.rstrip('/') for m in args.modules]

    reporter = Reporter()
    git_cache = GitCache(args.base_branch)

    check_dirs = set()

    for module in args.modules:
        if os.path.isfile(module):
            path = module
            if args.exclude and args.exclude.search(path):
                continue
            if ModuleValidator.is_blacklisted(path):
                continue
            with ModuleValidator(path, analyze_arg_spec=args.arg_spec,
                                 base_branch=args.base_branch, git_cache=git_cache, reporter=reporter) as mv:
                mv.validate()
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
                with ModuleValidator(path, analyze_arg_spec=args.arg_spec,
                                     base_branch=args.base_branch, git_cache=git_cache, reporter=reporter) as mv:
                    mv.validate()

    for path in sorted(check_dirs):
        pv = PythonPackageValidator(path, reporter=reporter)
        pv.validate()

    if args.format == 'plain':
        sys.exit(reporter.plain(warnings=args.warnings, output=args.output))
    else:
        sys.exit(reporter.json(warnings=args.warnings, output=args.output))


class GitCache(object):
    def __init__(self, base_branch):
        self.base_branch = base_branch

        if self.base_branch:
            self.base_tree = self._git(['ls-tree', '-r', '--name-only', self.base_branch, 'lib/ansible/modules/'])
        else:
            self.base_tree = []

        self.head_tree = self._git(['ls-tree', '-r', '--name-only', 'HEAD', 'lib/ansible/modules/'])

        self.base_module_paths = dict((os.path.basename(p), p) for p in self.base_tree if os.path.splitext(p)[1] in ('.py', '.ps1'))

        self.base_module_paths.pop('__init__.py', None)

        self.head_aliased_modules = set()

        for path in self.head_tree:
            filename = os.path.basename(path)

            if filename.startswith('_') and filename != '__init__.py':
                if os.path.islink(path):
                    self.head_aliased_modules.add(os.path.basename(os.path.realpath(path)))

    @staticmethod
    def _git(args):
        cmd = ['git'] + args
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout.decode('utf-8').splitlines()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
