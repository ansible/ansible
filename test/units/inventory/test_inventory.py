# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import string

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.inventory import Inventory
from ansible.inventory.expand_hosts import expand_hostname_range
from ansible.vars import VariableManager

from units.mock.loader import DictDataLoader

class TestInventory(unittest.TestCase):

    patterns = {
        'a': ['a'],
        'a, b': ['a', 'b'],
        'a , b': ['a', 'b'],
        ' a,b ,c[1:2] ': ['a', 'b', 'c[1:2]'],
        '9a01:7f8:191:7701::9': ['9a01:7f8:191:7701::9'],
        '9a01:7f8:191:7701::9,9a01:7f8:191:7701::9': ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9'],
        '9a01:7f8:191:7701::9,9a01:7f8:191:7701::9,foo': ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9','foo'],
        'foo[1:2]': ['foo[1:2]'],
        'a::b': ['a::b'],
        'a:b': ['a', 'b'],
        ' a : b ': ['a', 'b'],
        'foo:bar:baz[1:2]': ['foo', 'bar', 'baz[1:2]'],
    }

    pattern_lists = [
        [['a'], ['a']],
        [['a', 'b'], ['a', 'b']],
        [['a, b'], ['a', 'b']],
        [['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9,foo'],
         ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9','foo']]
    ]

    # pattern_string: [ ('base_pattern', (a,b)), ['x','y','z'] ]
    # a,b are the bounds of the subscript; x..z are the results of the subscript
    # when applied to string.ascii_letters.

    subscripts = {
        'a': [('a',None), list(string.ascii_letters)],
        'a[0]': [('a', (0, None)), ['a']],
        'a[1]': [('a', (1, None)), ['b']],
        'a[2:3]': [('a', (2, 3)), ['c', 'd']],
        'a[-1]': [('a', (-1, None)), ['Z']],
        'a[-2]': [('a', (-2, None)), ['Y']],
        'a[48:]': [('a', (48, -1)), ['W', 'X', 'Y', 'Z']],
        'a[49:]': [('a', (49, -1)), ['X', 'Y', 'Z']],
        'a[1:]': [('a', (1, -1)), list(string.ascii_letters[1:])],
    }

    ranges_to_expand = {
        'a[1:2]': ['a1', 'a2'],
        'a[1:10:2]': ['a1', 'a3', 'a5', 'a7', 'a9'],
        'a[a:b]': ['aa', 'ab'],
        'a[a:i:3]': ['aa', 'ad', 'ag'],
        'a[a:b][c:d]': ['aac', 'aad', 'abc', 'abd'],
        'a[0:1][2:3]': ['a02', 'a03', 'a12', 'a13'],
        'a[a:b][2:3]': ['aa2', 'aa3', 'ab2', 'ab3'],
    }

    def setUp(self):
        v = VariableManager()
        fake_loader = DictDataLoader({})

        self.i = Inventory(loader=fake_loader, variable_manager=v, host_list='')

    def test_split_patterns(self):

        for p in self.patterns:
            r = self.patterns[p]
            self.assertEqual(r, self.i.split_host_pattern(p))

        for p, r in self.pattern_lists:
            self.assertEqual(r, self.i.split_host_pattern(p))

    def test_ranges(self):

        for s in self.subscripts:
            r = self.subscripts[s]
            self.assertEqual(r[0], self.i._split_subscript(s))
            self.assertEqual(
                r[1],
                self.i._apply_subscript(
                    list(string.ascii_letters),
                    r[0][1]
                )
            )

    def test_expand_hostname_range(self):

        for e in self.ranges_to_expand:
            r = self.ranges_to_expand[e]
            self.assertEqual(r, expand_hostname_range(e))
