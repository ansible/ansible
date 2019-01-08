#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2017, Matt Martz <matt@sivel.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import re
import sys

from ansible.plugins.test import core, files, mathstuff

TESTS = list(core.TestModule().tests().keys()) + list(files.TestModule().tests().keys()) + list(mathstuff.TestModule().tests().keys())


TEST_MAP = {
    'version_compare': 'version',
    'is_dir': 'directory',
    'is_file': 'file',
    'is_link': 'link',
    'is_abs': 'abs',
    'is_same_file': 'same_file',
    'is_mount': 'mount',
    'issubset': 'subset',
    'issuperset': 'superset',
    'isnan': 'nan',
    'succeeded': 'successful',
    'success': 'successful',
    'change': 'changed',
    'skip': 'skipped',
}


FILTER_RE = re.compile(r'(?P<left>[\w .\'"]+)(\s*)\|(\s*)(?P<filter>\w+)')


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path) as f:
            text = f.read()

        lines = text.splitlines(True)
        previous = 0
        offset = 0
        lineno = 0

        for match in FILTER_RE.finditer(text):
            filter_name = match.group('filter')
            test_name = TEST_MAP.get(filter_name, filter_name)

            if test_name not in TESTS:
                continue

            left = match.group('left').strip()
            start = match.start('left')

            while start >= offset:
                previous = offset
                offset += len(lines[lineno])
                lineno += 1

            colno = start - previous + 1

            print('%s:%d:%d: use `%s is %s` instead of `%s | %s`' % (path, lineno, colno, left, test_name, left, filter_name))


if __name__ == '__main__':
    main()
