# -*- coding: utf-8 -*-
#
# (c) 2017 Red Hat, Inc.
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
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest

from ansible.module_utils.network.common.utils import to_list, sort_list
from ansible.module_utils.network.common.utils import dict_diff, dict_merge
from ansible.module_utils.network.common.utils import conditional, Template
from ansible.module_utils.network.common.utils import to_masklen, to_netmask, to_subnet
from ansible.module_utils.network.common.utils import is_masklen, is_netmask


class TestModuleUtilsNetworkCommon(unittest.TestCase):

    def test_to_list(self):
        for scalar in ('string', 1, True, False, None):
            self.assertTrue(isinstance(to_list(scalar), list))

        for container in ([1, 2, 3], {'one': 1}):
            self.assertTrue(isinstance(to_list(container), list))

        test_list = [1, 2, 3]
        self.assertNotEqual(id(test_list), id(to_list(test_list)))

    def test_sort(self):
        data = [3, 1, 2]
        self.assertEqual([1, 2, 3], sort_list(data))

        string_data = '123'
        self.assertEqual(string_data, sort_list(string_data))

    def test_dict_diff(self):
        base = dict(obj2=dict(), b1=True, b2=False, b3=False,
                    one=1, two=2, three=3, obj1=dict(key1=1, key2=2),
                    l1=[1, 3], l2=[1, 2, 3], l4=[4],
                    nested=dict(n1=dict(n2=2)))

        other = dict(b1=True, b2=False, b3=True, b4=True,
                     one=1, three=4, four=4, obj1=dict(key1=2),
                     l1=[2, 1], l2=[3, 2, 1], l3=[1],
                     nested=dict(n1=dict(n2=2, n3=3)))

        result = dict_diff(base, other)

        # string assertions
        self.assertNotIn('one', result)
        self.assertNotIn('two', result)
        self.assertEqual(result['three'], 4)
        self.assertEqual(result['four'], 4)

        # dict assertions
        self.assertIn('obj1', result)
        self.assertIn('key1', result['obj1'])
        self.assertNotIn('key2', result['obj1'])

        # list assertions
        self.assertEqual(result['l1'], [2, 1])
        self.assertNotIn('l2', result)
        self.assertEqual(result['l3'], [1])
        self.assertNotIn('l4', result)

        # nested assertions
        self.assertIn('obj1', result)
        self.assertEqual(result['obj1']['key1'], 2)
        self.assertNotIn('key2', result['obj1'])

        # bool assertions
        self.assertNotIn('b1', result)
        self.assertNotIn('b2', result)
        self.assertTrue(result['b3'])
        self.assertTrue(result['b4'])

    def test_dict_merge(self):
        base = dict(obj2=dict(), b1=True, b2=False, b3=False,
                    one=1, two=2, three=3, obj1=dict(key1=1, key2=2),
                    l1=[1, 3], l2=[1, 2, 3], l4=[4],
                    nested=dict(n1=dict(n2=2)))

        other = dict(b1=True, b2=False, b3=True, b4=True,
                     one=1, three=4, four=4, obj1=dict(key1=2),
                     l1=[2, 1], l2=[3, 2, 1], l3=[1],
                     nested=dict(n1=dict(n2=2, n3=3)))

        result = dict_merge(base, other)

        # string assertions
        self.assertIn('one', result)
        self.assertIn('two', result)
        self.assertEqual(result['three'], 4)
        self.assertEqual(result['four'], 4)

        # dict assertions
        self.assertIn('obj1', result)
        self.assertIn('key1', result['obj1'])
        self.assertIn('key2', result['obj1'])

        # list assertions
        self.assertEqual(result['l1'], [1, 2, 3])
        self.assertIn('l2', result)
        self.assertEqual(result['l3'], [1])
        self.assertIn('l4', result)

        # nested assertions
        self.assertIn('obj1', result)
        self.assertEqual(result['obj1']['key1'], 2)
        self.assertIn('key2', result['obj1'])

        # bool assertions
        self.assertIn('b1', result)
        self.assertIn('b2', result)
        self.assertTrue(result['b3'])
        self.assertTrue(result['b4'])

    def test_conditional(self):
        self.assertTrue(conditional(10, 10))
        self.assertTrue(conditional('10', '10'))
        self.assertTrue(conditional('foo', 'foo'))
        self.assertTrue(conditional(True, True))
        self.assertTrue(conditional(False, False))
        self.assertTrue(conditional(None, None))
        self.assertTrue(conditional("ge(1)", 1))
        self.assertTrue(conditional("gt(1)", 2))
        self.assertTrue(conditional("le(2)", 2))
        self.assertTrue(conditional("lt(3)", 2))
        self.assertTrue(conditional("eq(1)", 1))
        self.assertTrue(conditional("neq(0)", 1))
        self.assertTrue(conditional("min(1)", 1))
        self.assertTrue(conditional("max(1)", 1))
        self.assertTrue(conditional("exactly(1)", 1))

    def test_template(self):
        tmpl = Template()
        self.assertEqual('foo', tmpl('{{ test }}', {'test': 'foo'}))

    def test_to_masklen(self):
        self.assertEqual(24, to_masklen('255.255.255.0'))

    def test_to_masklen_invalid(self):
        with self.assertRaises(ValueError):
            to_masklen('255')

    def test_to_netmask(self):
        self.assertEqual('255.0.0.0', to_netmask(8))
        self.assertEqual('255.0.0.0', to_netmask('8'))

    def test_to_netmask_invalid(self):
        with self.assertRaises(ValueError):
            to_netmask(128)

    def test_to_subnet(self):
        result = to_subnet('192.168.1.1', 24)
        self.assertEqual('192.168.1.0/24', result)

        result = to_subnet('192.168.1.1', 24, dotted_notation=True)
        self.assertEqual('192.168.1.0 255.255.255.0', result)

    def test_to_subnet_invalid(self):
        with self.assertRaises(ValueError):
            to_subnet('foo', 'bar')

    def test_is_masklen(self):
        self.assertTrue(is_masklen(32))
        self.assertFalse(is_masklen(33))
        self.assertFalse(is_masklen('foo'))

    def test_is_netmask(self):
        self.assertTrue(is_netmask('255.255.255.255'))
        self.assertFalse(is_netmask(24))
        self.assertFalse(is_netmask('foo'))


