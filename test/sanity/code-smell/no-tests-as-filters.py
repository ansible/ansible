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

import os
import re
import sys

from collections import defaultdict

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


FILTER_RE = re.compile(r'((.+?)\s*([\w \.\'"]+)(\s*)\|(\s*)(\w+))')


def main():
    all_matches = defaultdict(list)

    for root, dirs, filenames in os.walk('.'):
        for name in filenames:
            if os.path.splitext(name)[1] not in ('.yml', '.yaml'):
                continue
            path = os.path.join(root, name)

            with open(path) as f:
                text = f.read()

            for match in FILTER_RE.findall(text):
                filter_name = match[5]

                try:
                    test_name = TEST_MAP[filter_name]
                except KeyError:
                    test_name = filter_name

                if test_name not in TESTS:
                    continue

                all_matches[path].append(match[0])

    if all_matches:
        print('Use of Ansible provided Jinja2 tests as filters is deprecated.')
        print('Please update to use `is` syntax such as `result is failed`.')

        for path, matches in all_matches.items():
            for match in matches:
                print('%s: %s' % (path, match,))
        sys.exit(1)


if __name__ == '__main__':
    main()
