# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Will Thames <will.thames@xvt.com.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.dict_transformations import (
    _camel_to_snake,
    _snake_to_camel,
    camel_dict_to_snake_dict,
    dict_merge,
    recursive_diff,
)


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


class TestCaseCamelToSnake:

    def test_camel_to_snake(self):
        for (k, v) in EXPECTED_SNAKIFICATION.items():
            assert _camel_to_snake(k) == v

    def test_reversible_camel_to_snake(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            assert _camel_to_snake(k, reversible=True) == v


class TestCaseSnakeToCamel:

    def test_snake_to_camel_reversed(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            assert _snake_to_camel(v, capitalize_first=True) == k


class TestCaseCamelToSnakeAndBack:
    def test_camel_to_snake_and_back(self):
        for (k, v) in EXPECTED_REVERSIBLE.items():
            assert _snake_to_camel(_camel_to_snake(k, reversible=True), capitalize_first=True) == k


class TestCaseCamelDictToSnakeDict:
    def test_ignore_list(self):
        camel_dict = dict(Hello=dict(One='one', Two='two'), World=dict(Three='three', Four='four'))
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list='World')
        assert snake_dict['hello'] == dict(one='one', two='two')
        assert snake_dict['world'] == dict(Three='three', Four='four')

    def test_ignore_list_nested_in_dict(self):
        """An ignored key is honoured at any depth, not just at the top level."""
        camel_dict = dict(Instance=dict(InstanceId='i-123', Tags=dict(MyKey='v', AnotherKey='v')))
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list=('Tags',))
        assert snake_dict['instance']['instance_id'] == 'i-123'
        assert snake_dict['instance']['tags'] == dict(MyKey='v', AnotherKey='v')

    def test_ignore_list_nested_in_list(self):
        """An ignored key is honoured for dicts reached through a list."""
        camel_dict = dict(Instances=[dict(InstanceId='i-123', Tags=dict(MyKey='v'))])
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list=('Tags',))
        assert snake_dict['instances'][0]['instance_id'] == 'i-123'
        assert snake_dict['instances'][0]['tags'] == dict(MyKey='v')

    def test_ignore_list_deeply_nested(self):
        """An ignored key is honoured through alternating dict and list nesting."""
        camel_dict = dict(Reservations=[dict(Instances=[dict(Tags=dict(CamelKey='v'), BlockDevices=[dict(DeviceName='xvda')])])])
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list=('Tags',))
        instance = snake_dict['reservations'][0]['instances'][0]
        assert instance['tags'] == dict(CamelKey='v')
        # keys outside the ignored sub-tree are still converted at that depth
        assert instance['block_devices'][0]['device_name'] == 'xvda'

    def test_ignore_list_multiple_keys(self):
        camel_dict = dict(Outer=dict(Tags=dict(AKey='a'), Metadata=dict(BKey='b'), Other=dict(CKey='c')))
        snake_dict = camel_dict_to_snake_dict(camel_dict, ignore_list=('Tags', 'Metadata'))
        assert snake_dict['outer']['tags'] == dict(AKey='a')
        assert snake_dict['outer']['metadata'] == dict(BKey='b')
        assert snake_dict['outer']['other'] == dict(c_key='c')


class TestCaseDictMerge:
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
        assert 'one' in result
        assert 'two' in result
        assert result['three'] == 4
        assert result['four'] == 4

        # dict assertions
        assert 'obj1' in result
        assert 'key1' in result['obj1']
        assert 'key2' in result['obj1']

        # list assertions
        # this line differs from the network_utils/common test of the function of the
        # same name as this method does not merge lists
        assert result['l1'], [2, 1]
        assert 'l2' in result
        assert result['l3'], [1]
        assert 'l4' in result

        # nested assertions
        assert 'obj1' in result
        assert result['obj1']['key1'], 2
        assert 'key2' in result['obj1']

        # bool assertions
        assert 'b1' in result
        assert 'b2' in result
        assert result['b3']
        assert result['b4']


class TestCaseAzureIncidental:

    def test_dict_merge_invalid_dict(self):
        """ if b is not a dict, return b """
        res = dict_merge({}, None)
        assert res is None

    def test_merge_sub_dicts(self):
        """merge sub dicts """
        a = {'a': {'a1': 1}}
        b = {'a': {'b1': 2}}
        c = {'a': {'a1': 1, 'b1': 2}}
        res = dict_merge(a, b)
        assert res == c


class TestCaseRecursiveDiff:
    def test_recursive_diff(self):
        a = {'foo': {'bar': [{'baz': {'qux': 'ham_sandwich'}}]}}
        c = {'foo': {'bar': [{'baz': {'qux': 'ham_sandwich'}}]}}
        b = {'foo': {'bar': [{'baz': {'qux': 'turkey_sandwich'}}]}}

        assert recursive_diff(a, b) is not None
        assert len(recursive_diff(a, b)) == 2
        assert recursive_diff(a, c) is None

    @pytest.mark.parametrize(
        'p1, p2', (
            ([1, 2], [2, 3]),
            ({1: 2}, [2, 3]),
            ([1, 2], {2: 3}),
            ({2: 3}, 'notadict'),
            ('notadict', {2: 3}),
        )
    )
    def test_recursive_diff_negative(self, p1, p2):
        with pytest.raises(TypeError, match="Unable to diff"):
            recursive_diff(p1, p2)
