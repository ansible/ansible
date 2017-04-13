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

import ast
import sys

from io import BytesIO, TextIOWrapper

import yaml
import yaml.reader


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
        sys.stdout = self.stdout = TextIOWrapper(BytesIO(), encoding=self.sys_stdout.encoding)
        sys.stderr = self.stderr = TextIOWrapper(BytesIO(), encoding=self.sys_stderr.encoding)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr

    def get(self):
        """Return ``(stdout, stderr)``"""

        return self.stdout.getvalue(), self.stderr.getvalue()


def parse_yaml(value, lineno, module, name, load_all=False):
    traces = []
    errors = []
    data = None

    if load_all:
        loader = yaml.safe_load_all
    else:
        loader = yaml.safe_load

    try:
        data = loader(value)
        if load_all:
            data = list(data)
    except yaml.MarkedYAMLError as e:
        e.problem_mark.line += lineno - 1
        e.problem_mark.name = '%s.%s' % (module, name)
        errors.append('%s is not valid YAML. Line %d column %d' %
                      (name, e.problem_mark.line + 1,
                       e.problem_mark.column + 1))
        traces.append(e)
    except yaml.reader.ReaderError as e:
        traces.append(e)
        errors.append('%s is not valid YAML. Character '
                      '0x%x at position %d.' %
                      (name, e.character, e.position))
    except yaml.YAMLError as e:
        traces.append(e)
        errors.append('%s is not valid YAML: %s: %s' % (name, type(e), e))

    return data, errors, traces
