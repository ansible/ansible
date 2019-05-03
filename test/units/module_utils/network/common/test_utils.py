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
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.network.common.utils import to_list, sort_list
from ansible.module_utils.network.common.utils import dict_diff, dict_merge
from ansible.module_utils.network.common.utils import conditional, Template
from ansible.module_utils.common.network import (
    to_masklen, to_netmask, to_subnet, to_ipv6_network, to_ipv6_subnet, is_masklen, is_netmask
)


def test_to_list():
    for scalar in ('string', 1, True, False, None):
        assert isinstance(to_list(scalar), list)

    for container in ([1, 2, 3], {'one': 1}):
        assert isinstance(to_list(container), list)

    test_list = [1, 2, 3]
    assert id(test_list) != id(to_list(test_list))


def test_sort():
    data = [3, 1, 2]
    assert [1, 2, 3] == sort_list(data)

    string_data = '123'
    assert string_data == sort_list(string_data)


def test_dict_diff():
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
    assert 'one' not in result
    assert 'two' not in result
    assert result['three'] == 4
    assert result['four'] == 4

    # dict assertions
    assert 'obj1' in result
    assert 'key1' in result['obj1']
    assert 'key2' not in result['obj1']

    # list assertions
    assert result['l1'] == [2, 1]
    assert 'l2' not in result
    assert result['l3'] == [1]
    assert 'l4' not in result

    # nested assertions
    assert 'obj1' in result
    assert result['obj1']['key1'] == 2
    assert 'key2' not in result['obj1']

    # bool assertions
    assert 'b1' not in result
    assert 'b2' not in result
    assert result['b3']
    assert result['b4']


def test_dict_merge():
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
    assert result['l1'] == [1, 2, 3]
    assert 'l2' in result
    assert result['l3'] == [1]
    assert 'l4' in result

    # nested assertions
    assert 'obj1' in result
    assert result['obj1']['key1'] == 2
    assert 'key2' in result['obj1']

    # bool assertions
    assert 'b1' in result
    assert 'b2' in result
    assert result['b3']
    assert result['b4']


def test_conditional():
    assert conditional(10, 10)
    assert conditional('10', '10')
    assert conditional('foo', 'foo')
    assert conditional(True, True)
    assert conditional(False, False)
    assert conditional(None, None)
    assert conditional("ge(1)", 1)
    assert conditional("gt(1)", 2)
    assert conditional("le(2)", 2)
    assert conditional("lt(3)", 2)
    assert conditional("eq(1)", 1)
    assert conditional("neq(0)", 1)
    assert conditional("min(1)", 1)
    assert conditional("max(1)", 1)
    assert conditional("exactly(1)", 1)


def test_template():
    tmpl = Template()
    assert 'foo' == tmpl('{{ test }}', {'test': 'foo'})


def test_to_masklen():
    assert 24 == to_masklen('255.255.255.0')


def test_to_masklen_invalid():
    with pytest.raises(ValueError):
        to_masklen('255')


def test_to_netmask():
    assert '255.0.0.0' == to_netmask(8)
    assert '255.0.0.0' == to_netmask('8')


def test_to_netmask_invalid():
    with pytest.raises(ValueError):
        to_netmask(128)


def test_to_subnet():
    result = to_subnet('192.168.1.1', 24)
    assert '192.168.1.0/24' == result

    result = to_subnet('192.168.1.1', 24, dotted_notation=True)
    assert '192.168.1.0 255.255.255.0' == result


def test_to_subnet_invalid():
    with pytest.raises(ValueError):
        to_subnet('foo', 'bar')


def test_is_masklen():
    assert is_masklen(32)
    assert not is_masklen(33)
    assert not is_masklen('foo')


def test_is_netmask():
    assert is_netmask('255.255.255.255')
    assert not is_netmask(24)
    assert not is_netmask('foo')


def test_to_ipv6_network():
    assert '2001:db8::' == to_ipv6_network('2001:db8::')
    assert '2001:0db8:85a3::' == to_ipv6_network('2001:0db8:85a3:0000:0000:8a2e:0370:7334')
    assert '2001:0db8:85a3::' == to_ipv6_network('2001:0db8:85a3:0:0:8a2e:0370:7334')


def test_to_ipv6_subnet():
    assert '2001:db8::' == to_ipv6_subnet('2001:db8::')
    assert '2001:0db8:85a3:4242::' == to_ipv6_subnet('2001:0db8:85a3:4242:0000:8a2e:0370:7334')
    assert '2001:0db8:85a3:4242::' == to_ipv6_subnet('2001:0db8:85a3:4242:0:8a2e:0370:7334')
