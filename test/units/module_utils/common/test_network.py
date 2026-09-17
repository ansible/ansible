# -*- coding: utf-8 -*-
# (c) 2017 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.network import (
    to_bits,
    to_masklen,
    to_netmask,
    to_subnet,
    to_ipv6_network,
    is_mac,
    is_masklen,
    is_netmask
)


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


def test_is_mac():
    assert is_mac('52:54:00:e1:44:e0')
    assert is_mac('52-54-00-e1-44-e0')
    assert is_mac('AA:BB:CC:DD:EE:FF')
    assert not is_mac('foo')
    assert not is_mac('52:54:00:e1:44')
    # mixed separators are not valid
    assert not is_mac('52:54-00:e1:44:e0')
    # by default a trailing newline is accepted (regex '$' matches before a final newline)
    assert is_mac('52:54:00:e1:44:e0\n')
    # strict=True anchors with \Z, so a trailing newline is rejected
    assert not is_mac('52:54:00:e1:44:e0\n', strict=True)
    # strict=True still accepts a well-formed address
    assert is_mac('52:54:00:e1:44:e0', strict=True)


def test_is_masklen():
    assert is_masklen(32)
    assert not is_masklen(33)
    assert not is_masklen('foo')


def test_is_netmask():
    assert is_netmask('255.255.255.255')
    assert is_netmask('0.0.0.0')
    assert is_netmask('255.255.255.0')
    assert is_netmask('255.255.254.0')
    assert not is_netmask(24)
    assert not is_netmask('foo')
    # individually valid octets that are not a contiguous mask
    assert not is_netmask('255.255.0.255')
    assert not is_netmask('254.255.255.0')
    assert not is_netmask('0.255.0.0')
    assert not is_netmask('0.0.0.255')
    # inet_aton-style legacy forms must stay rejected (they break to_masklen)
    assert not is_netmask('0xffffff00')
    assert not is_netmask('0377.0377.0377.0')
    assert not is_netmask('4294967040')
    assert not is_netmask('255.255.0')


def test_to_ipv6_network():
    assert '2001:db8::' == to_ipv6_network('2001:db8::')
    assert '2001:0db8:85a3::' == to_ipv6_network('2001:0db8:85a3:0000:0000:8a2e:0370:7334')
    assert '2001:0db8:85a3::' == to_ipv6_network('2001:0db8:85a3:0:0:8a2e:0370:7334')


def test_to_bits():
    assert to_bits('0') == '00000000'
    assert to_bits('1') == '00000001'
    assert to_bits('2') == '00000010'
    assert to_bits('1337') == '10100111001'
    assert to_bits('127.0.0.1') == '01111111000000000000000000000001'
    assert to_bits('255.255.255.255') == '11111111111111111111111111111111'
    assert to_bits('255.255.255.0') == '11111111111111111111111100000000'
