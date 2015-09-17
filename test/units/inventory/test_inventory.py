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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.inventory import Inventory
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


    def setUp(self):
        v = VariableManager()
        fake_loader = DictDataLoader({})

        self.i = Inventory(loader=fake_loader, variable_manager=v, host_list='')

    def test_split_patterns(self):

        for p in self.patterns:
            r = self.patterns[p]
            self.assertEqual(r, self.i._split_pattern(p))

        for p, r in self.pattern_lists:
            self.assertEqual(r, self.i._split_pattern(p))
