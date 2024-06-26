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
from __future__ import annotations

import ast
import datetime
import os
import re
import sys

from io import BytesIO, TextIOWrapper

import yaml
import yaml.reader

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.yaml import SafeLoader
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.loader import AnsibleLoader


class AnsibleTextIOWrapper(TextIOWrapper):
    def write(self, s):
        super(AnsibleTextIOWrapper, self).write(to_text(s, self.encoding, errors='replace'))


def find_executable(executable, cwd=None, path=None):
    """Finds the full path to the executable specified"""
    match = None
    real_cwd = os.getcwd()

    if not cwd:
        cwd = real_cwd

    if os.path.dirname(executable):
        target = os.path.join(cwd, executable)
        if os.path.exists(target) and os.access(target, os.F_OK | os.X_OK):
            match = executable
    else:
        path = os.environ.get('PATH', os.path.defpath)

        path_dirs = path.split(os.path.pathsep)
        seen_dirs = set()

        for path_dir in path_dirs:
            if path_dir in seen_dirs:
                continue

            seen_dirs.add(path_dir)

            if os.path.abspath(path_dir) == real_cwd:
                path_dir = cwd

            candidate = os.path.join(path_dir, executable)

            if os.path.exists(candidate) and os.access(candidate, os.F_OK | os.X_OK):
                match = candidate
                break

    return match


def find_globals(g, tree):
    """Uses AST to find globals in an ast tree"""
    for child in tree:
        if hasattr(child, 'body') and isinstance(child.body, list):
            find_globals(g, child.body)
        elif isinstance(child, (ast.FunctionDef, ast.ClassDef)):
            g.add(child.name)
            continue
        elif isinstance(child, ast.Assign):
            try:
                g.add(child.targets[0].id)
            except (IndexError, AttributeError):
                pass
        elif isinstance(child, ast.Import):
            g.add(child.names[0].name)
        elif isinstance(child, ast.ImportFrom):
            for name in child.names:
                g_name = name.asname or name.name
                if g_name == '*':
                    continue
                g.add(g_name)


class CaptureStd():
    """Context manager to handle capturing stderr and stdout"""

    def __enter__(self):
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr
        sys.stdout = self.stdout = AnsibleTextIOWrapper(BytesIO(), encoding=self.sys_stdout.encoding)
        sys.stderr = self.stderr = AnsibleTextIOWrapper(BytesIO(), encoding=self.sys_stderr.encoding)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr

    def get(self):
        """Return ``(stdout, stderr)``"""

        return self.stdout.buffer.getvalue(), self.stderr.buffer.getvalue()


def get_module_name_from_filename(filename, collection):
    # Calculate the module's name so that relative imports work correctly
    if collection:
        # collection is a relative path, example: ansible_collections/my_namespace/my_collection
        # filename is a relative path, example: plugins/modules/my_module.py
        path = os.path.join(collection, filename)
    else:
        # filename is a relative path, example: lib/ansible/modules/system/ping.py
        path = os.path.relpath(filename, 'lib')

    name = os.path.splitext(path)[0].replace(os.path.sep, '.')

    return name


def parse_yaml(value, lineno, module, name, load_all=False, ansible_loader=False):
    traces = []
    errors = []
    data = None

    if load_all:
        yaml_load = yaml.load_all
    else:
        yaml_load = yaml.load

    if ansible_loader:
        loader = AnsibleLoader
    else:
        loader = SafeLoader

    try:
        data = yaml_load(value, Loader=loader)
        if load_all:
            data = list(data)
    except yaml.MarkedYAMLError as e:
        errors.append({
            'msg': '%s is not valid YAML' % name,
            'line': e.problem_mark.line + lineno,
            'column': e.problem_mark.column + 1
        })
        traces.append(e)
    except yaml.reader.ReaderError as e:
        traces.append(e)
        # TODO: Better line/column detection
        errors.append({
            'msg': ('%s is not valid YAML. Character '
                    '0x%x at position %d.' % (name, e.character, e.position)),
            'line': lineno
        })
    except yaml.YAMLError as e:
        traces.append(e)
        errors.append({
            'msg': '%s is not valid YAML: %s: %s' % (name, type(e), e),
            'line': lineno
        })

    return data, errors, traces


def is_empty(value):
    """Evaluate null like values excluding False"""
    if value is False:
        return False
    return not bool(value)


def compare_unordered_lists(a, b):
    """Safe list comparisons

    Supports:
      - unordered lists
      - unhashable elements
    """
    return len(a) == len(b) and all(x in b for x in a) and all(x in a for x in b)


class NoArgsAnsibleModule(AnsibleModule):
    """AnsibleModule that does not actually load params. This is used to get access to the
    methods within AnsibleModule without having to fake a bunch of data
    """
    def _load_params(self):
        self.params = {'_ansible_selinux_special_fs': [], '_ansible_remote_tmp': '/tmp', '_ansible_keep_remote_files': False, '_ansible_check_mode': False}


def parse_isodate(v, allow_date):
    if allow_date:
        if isinstance(v, datetime.date):
            return v
        msg = 'Expected ISO 8601 date string (YYYY-MM-DD) or YAML date'
    else:
        msg = 'Expected ISO 8601 date string (YYYY-MM-DD)'
    if not isinstance(v, string_types):
        raise ValueError(msg)
    # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
    # we have to do things manually.
    if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', v):
        raise ValueError(msg)
    try:
        return datetime.datetime.strptime(v, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(msg)
