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

from __future__ import annotations

import string
import textwrap

from unittest import mock

from ansible import constants as C
import unittest
from ansible.module_utils.common.text.converters import to_text
from units.mock.path import mock_unfrackpath_noop

from ansible.inventory.manager import InventoryManager, split_host_pattern

from units.mock.loader import DictDataLoader


class TestInventory(unittest.TestCase):

    patterns = {
        'a': ['a'],
        'a, b': ['a', 'b'],
        'a , b': ['a', 'b'],
        ' a,b ,c[1:2] ': ['a', 'b', 'c[1:2]'],
        '9a01:7f8:191:7701::9': ['9a01:7f8:191:7701::9'],
        '9a01:7f8:191:7701::9,9a01:7f8:191:7701::9': ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9'],
        '9a01:7f8:191:7701::9,9a01:7f8:191:7701::9,foo': ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9', 'foo'],
        'foo[1:2]': ['foo[1:2]'],
        'a::b': ['a::b'],
        'a:b': ['a', 'b'],
        ' a : b ': ['a', 'b'],
        'foo:bar:baz[1:2]': ['foo', 'bar', 'baz[1:2]'],
        'a,,b': ['a', 'b'],
        'a,  ,b,,c, ,': ['a', 'b', 'c'],
        ',': [],
        '': [],
    }

    pattern_lists = [
        [['a'], ['a']],
        [['a', 'b'], ['a', 'b']],
        [['a, b'], ['a', 'b']],
        [['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9,foo'],
         ['9a01:7f8:191:7701::9', '9a01:7f8:191:7701::9', 'foo']]
    ]

    # pattern_string: [ ('base_pattern', (a,b)), ['x','y','z'] ]
    # a,b are the bounds of the subscript; x..z are the results of the subscript
    # when applied to string.ascii_letters.

    subscripts = {
        'a': [('a', None), list(string.ascii_letters)],
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
        fake_loader = DictDataLoader({})

        self.i = InventoryManager(loader=fake_loader, sources=[None])

    def test_split_patterns(self):

        for p in self.patterns:
            r = self.patterns[p]
            self.assertEqual(r, split_host_pattern(p))

        for p, r in self.pattern_lists:
            self.assertEqual(r, split_host_pattern(p))

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


class TestInventoryPlugins(unittest.TestCase):

    def test_empty_inventory(self):
        inventory = self._get_inventory('')

        self.assertIn('all', inventory.groups)
        self.assertIn('ungrouped', inventory.groups)
        self.assertFalse(inventory.groups['all'].get_hosts())
        self.assertFalse(inventory.groups['ungrouped'].get_hosts())

    def test_ini(self):
        self._test_default_groups("""
            host1
            host2
            host3
            [servers]
            host3
            host4
            host5
            """)

    def test_ini_explicit_ungrouped(self):
        self._test_default_groups("""
            [ungrouped]
            host1
            host2
            host3
            [servers]
            host3
            host4
            host5
            """)

    def test_ini_variables_stringify(self):
        values = ['string', 'no', 'No', 'false', 'FALSE', [], False, 0]

        inventory_content = "host1 "
        inventory_content += ' '.join(['var%s=%s' % (i, to_text(x)) for i, x in enumerate(values)])
        inventory = self._get_inventory(inventory_content)

        variables = inventory.get_host('host1').vars
        for i in range(len(values)):
            if isinstance(values[i], str):
                self.assertIsInstance(variables['var%s' % i], str)
            else:
                self.assertIsInstance(variables['var%s' % i], type(values[i]))

    @mock.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    @mock.patch('os.path.exists', lambda x: True)
    @mock.patch('os.access', lambda x, y: True)
    def test_yaml_inventory(self, filename="test.yaml"):
        inventory_content = {filename: textwrap.dedent("""\
        ---
        all:
            hosts:
                test1:
                test2:
        """)}
        C.INVENTORY_ENABLED = ['yaml']
        fake_loader = DictDataLoader(inventory_content)
        im = InventoryManager(loader=fake_loader, sources=filename)
        self.assertTrue(im._inventory.hosts)
        self.assertIn('test1', im._inventory.hosts)
        self.assertIn('test2', im._inventory.hosts)
        self.assertIn(im._inventory.get_host('test1'), im._inventory.groups['all'].hosts)
        self.assertIn(im._inventory.get_host('test2'), im._inventory.groups['all'].hosts)
        self.assertEqual(len(im._inventory.groups['all'].hosts), 2)
        self.assertIn(im._inventory.get_host('test1'), im._inventory.groups['ungrouped'].hosts)
        self.assertIn(im._inventory.get_host('test2'), im._inventory.groups['ungrouped'].hosts)
        self.assertEqual(len(im._inventory.groups['ungrouped'].hosts), 2)

    def _get_inventory(self, inventory_content):

        fake_loader = DictDataLoader({__file__: inventory_content})

        return InventoryManager(loader=fake_loader, sources=[__file__])

    def _test_default_groups(self, inventory_content):
        inventory = self._get_inventory(inventory_content)

        self.assertIn('all', inventory.groups)
        self.assertIn('ungrouped', inventory.groups)
        all_hosts = set(host.name for host in inventory.groups['all'].get_hosts())
        self.assertEqual(set(['host1', 'host2', 'host3', 'host4', 'host5']), all_hosts)
        ungrouped_hosts = set(host.name for host in inventory.groups['ungrouped'].get_hosts())
        self.assertEqual(set(['host1', 'host2']), ungrouped_hosts)
        servers_hosts = set(host.name for host in inventory.groups['servers'].get_hosts())
        self.assertEqual(set(['host3', 'host4', 'host5']), servers_hosts)
