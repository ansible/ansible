# -*- coding: utf-8 -*-
# (c) 2017, Will Thames <will.thames@xvt.com.au>
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

from ansible.compat.tests import unittest
from ansible.module_utils.common.dict_transformations import _camel_to_snake, _snake_to_camel, camel_dict_to_snake_dict, dict_merge

EXPECTED_SNAKIFICATION = {
    'alllower': 'alllower',
    'TwoWords': 'two_words',
    'AllUpperAtEND': 'all_upper_at_end',
    'AllUpperButPLURALs': 'all_upper_but_plurals',
    'TargetGroupARNs': 'target_group_arns',
    'HTTPEndpoints': 'http_endpoints',
    'PLURALs': 'plurals'
}

EXPECTED_REVERSIBLE = {
    'TwoWords': 'two_words',
    'AllUpperAtEND': 'all_upper_at_e_n_d',
    'AllUpperButPLURALs': 'all_upper_but_p_l_u_r_a_ls',
    'TargetGroupARNs': 'target_group_a_r_ns',
    'HTTPEndpoints': 'h_t_t_p_endpoints',
    'PLURALs': 'p_l_u_r_a_ls'
}


class CamelToSnakeTestCase(unittest.TestCase):

    def test_camel_to_snake(self):
        for (k, v) in EXPECTED_SNAKIFICATION.items():
            self.assertEqual(_camel_to_snake(k), v)

    def test_reversible_camel_to_snake(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            self.assertEqual(_camel_to_snake(k, reversible=True), v)


class SnakeToCamelTestCase(unittest.TestCase):

    def test_snake_to_camel_reversed(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            self.assertEqual(_snake_to_camel(v, capitalize_first=True), k)


class CamelToSnakeAndBackTestCase(unittest.TestCase):
    def test_camel_to_snake_and_back(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            self.assertEqual(_snake_to_camel(_camel_to_snake(k, reversible=True), capitalize_first=True), k)


class CamelDictToSnakeDictTestCase(unittest.TestCase):
    def test_ignore_list(self):
        camel_dict = dict(Hello=dict(One='one', Two='two'), World=dict(Three='three', Four='four'))
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list='World')
        self.assertEqual(snake_dict['hello'], dict(one='one', two='two'))
        self.assertEqual(snake_dict['world'], dict(Three='three', Four='four'))


class DictMergeTestCase(unittest.TestCase):
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
        self.assertTrue('one' in result)
        self.assertTrue('two' in result)
        self.assertEqual(result['three'], 4)
        self.assertEqual(result['four'], 4)

        # dict assertions
        self.assertTrue('obj1' in result)
        self.assertTrue('key1' in result['obj1'])
        self.assertTrue('key2' in result['obj1'])

        # list assertions
        # this line differs from the network_utils/common test of the function of the
        # same name as this method does not merge lists
        self.assertEqual(result['l1'], [2, 1])
        self.assertTrue('l2' in result)
        self.assertEqual(result['l3'], [1])
        self.assertTrue('l4' in result)

        # nested assertions
        self.assertTrue('obj1' in result)
        self.assertEqual(result['obj1']['key1'], 2)
        self.assertTrue('key2' in result['obj1'])

        # bool assertions
        self.assertTrue('b1' in result)
        self.assertTrue('b2' in result)
        self.assertTrue(result['b3'])
        self.assertTrue(result['b4'])
