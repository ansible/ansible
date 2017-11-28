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

# Purpose:
# The purpose of this script is to convert uses of tests as filters to proper jinja test syntax
# as part of https://github.com/ansible/proposals/issues/83

# Notes:
# This script is imperfect, but was close enough to "fix" all integration tests
# with the exception of:
#
# 1. One file needed manual remediation, where \\\\ was ultimately replace with \\ in 8 locations.
# 2. Multiple filter pipeline is unsupported. Example:
#        var|string|search('foo')
#    Which should be converted to:
#        var|string is search('foo')

import argparse
import os
import re

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
NOT_RE = re.compile(r'( ?)not ')
ASSERT_SPACE_RE = re.compile(r'- ([\'"])\s+')

parser = argparse.ArgumentParser()
parser.add_argument(
    'path',
    help='Path to a directory that will be recursively walked. All .yml and .yaml files will be evaluated '
         'and uses of tests as filters will be conveted to proper jinja test syntax files to have test syntax '
         'fixed'
)
args = parser.parse_args()

for root, dirs, filenames in os.walk(args.path):
    for name in filenames:
        if os.path.splitext(name)[1] not in ('.yml', '.yaml'):
            continue
        path = os.path.join(root, name)

        print(path)
        with open(path) as f:
            text = f.read()

        for match in FILTER_RE.findall(text):
            filter_name = match[5]

            is_not = match[2].strip(' "\'').startswith('not ')

            try:
                test_name = TEST_MAP[filter_name]
            except KeyError:
                test_name = filter_name

            if test_name not in TESTS:
                continue

            if is_not:
                before = NOT_RE.sub(r'\1', match[2]).rstrip()
                text = re.sub(
                    re.escape(match[0]),
                    '%s %s is not %s' % (match[1], before, test_name,),
                    text
                )
            else:
                text = re.sub(
                    re.escape(match[0]),
                    '%s %s is %s' % (match[1], match[2].rstrip(), test_name,),
                    text
                )

        with open(path, 'w+') as f:
            f.write(text)
