# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from ansible.module_utils.common.network import is_mac

testcase_is_valid_mac_addr = [
    ('A4-23-8D-F8-C9-E5', True),
    ('35:71:F4:11:0B:D8', True),
    ('b3-bd-20-59-0c-cf', True),
    ('32:61:ca:65:f1:f4', True),
    ('asdf', False),
    ('A4-23-8D-G8-C9-E5', False),
    ('A4-3-8D-F8-C9-E5', False),
    ('A4-23-88D-F8-C9-E5', False),
    ('A4-23-8D-F8-C9_E5', False),
    ('A4-23--8D-F8-C9-E5', False),
]

testcase_is_valid_ip_addr = [
    ('0.0.0.0', True),
    ('10.0.0.1', True),
    ('192.168.0.1', True),
    ('255.255.255.255', True),
    ('asdf', False),
    ('a.b.c.d', False),
    ('345.345.345.345', False),
    ('-10.0.0.1', False),
]

testcase_is_valid_ip_netmask = [
    ('240.0.0.0', True),
    ('255.224.0.0', True),
    ('255.255.248.0', True),
    ('255.255.255.255', True),
    ('asdf', False),
    ('a.b.c.d', False),
    ('192.168.0.1', False),
    ('255.0.248.0', False),
]

testcase_is_valid_ip_prefix = [
    ('0', True),
    ('16', True),
    ('24', True),
    ('32', True),
    ('asdf', False),
    ('-10', False),
    ('60', False),
    ('60s', False),
]

testcase_ip_prefix_to_netmask = {
    "params": [
        ('0', '0.0.0.0'),
        ('8', '255.0.0.0'),
        ('11', '255.224.0.0'),
        ('16', '255.255.0.0'),
        ('21', '255.255.248.0'),
        ('24', '255.255.255.0'),
        ('26', '255.255.255.192'),
        ('32', '255.255.255.255'),
        ('a', ''),
        ('60', ''),
    ],
    "ids": [
        '0',
        '8',
        '11',
        '16',
        '21',
        '24',
        '26',
        '32',
        'a',
        '60',
    ],
}

testcase_ip_netmask_to_prefix = {
    "params": [
        ('0.0.0.0', '0'),
        ('255.0.0.0', '8'),
        ('255.224.0.0', '11'),
        ('255.255.0.0', '16'),
        ('255.255.248.0', '21'),
        ('255.255.255.0', '24'),
        ('255.255.255.192', '26'),
        ('255.255.255.255', '32'),
        ('a', ''),
        ('60', ''),
    ],
    "ids": [
        '0.0.0.0',
        '255.0.0.0',
        '255.224.0.0',
        '255.255.0.0',
        '255.255.248.0',
        '255.255.255.0',
        '255.255.255.192',
        '255.255.255.255',
        'a',
        '60',
    ],
}

testcase_is_valid_ip6_addr = [
    ('::1', True),
    ('2001:DB8:0:0:8:800:200C:417A', True),
    ('2001:DB8::8:800:200C:417A', True),
    ('FF01::101', True),
    ('asdf', False),
    ('2001:DB8:0:0:8:800:200C:417A:221', False),
    ('FF01::101::2', False),
    ('2001:db8:85a3::8a2e:370k:7334', False),
]

testcase_is_valid_ip6_prefix = [
    ('0', True),
    ('56', True),
    ('78', True),
    ('128', True),
    ('asdf', False),
    ('-10', False),
    ('345', False),
    ('60s', False),
]


@pytest.mark.parametrize('mac_addr, result', testcase_is_valid_mac_addr)
def test_is_valid_mac_addr(xenserver, mac_addr, result):
    """Tests against examples of valid and invalid mac addresses."""
    assert is_mac(mac_addr) is result


@pytest.mark.parametrize('ip_addr, result', testcase_is_valid_ip_addr)
def test_is_valid_ip_addr(xenserver, ip_addr, result):
    """Tests against examples of valid and invalid ip addresses."""
    assert xenserver.is_valid_ip_addr(ip_addr) is result


@pytest.mark.parametrize('ip_netmask, result', testcase_is_valid_ip_netmask)
def test_is_valid_ip_netmask(xenserver, ip_netmask, result):
    """Tests against examples of valid and invalid ip netmasks."""
    assert xenserver.is_valid_ip_netmask(ip_netmask) is result


@pytest.mark.parametrize('ip_prefix, result', testcase_is_valid_ip_prefix)
def test_is_valid_ip_prefix(xenserver, ip_prefix, result):
    """Tests against examples of valid and invalid ip prefixes."""
    assert xenserver.is_valid_ip_prefix(ip_prefix) is result


@pytest.mark.parametrize('ip_prefix, ip_netmask', testcase_ip_prefix_to_netmask['params'], ids=testcase_ip_prefix_to_netmask['ids'])
def test_ip_prefix_to_netmask(xenserver, ip_prefix, ip_netmask):
    """Tests ip prefix to netmask conversion."""
    assert xenserver.ip_prefix_to_netmask(ip_prefix) == ip_netmask


@pytest.mark.parametrize('ip_netmask, ip_prefix', testcase_ip_netmask_to_prefix['params'], ids=testcase_ip_netmask_to_prefix['ids'])
def test_ip_netmask_to_prefix(xenserver, ip_netmask, ip_prefix):
    """Tests ip netmask to prefix conversion."""
    assert xenserver.ip_netmask_to_prefix(ip_netmask) == ip_prefix


@pytest.mark.parametrize('ip6_addr, result', testcase_is_valid_ip6_addr)
def test_is_valid_ip6_addr(xenserver, ip6_addr, result):
    """Tests against examples of valid and invalid ip6 addresses."""
    assert xenserver.is_valid_ip6_addr(ip6_addr) is result


@pytest.mark.parametrize('ip6_prefix, result', testcase_is_valid_ip6_prefix)
def test_is_valid_ip6_prefix(xenserver, ip6_prefix, result):
    """Tests against examples of valid and invalid ip6 prefixes."""
    assert xenserver.is_valid_ip6_prefix(ip6_prefix) is result
