# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.facts.network import generic_bsd


def mock_get_bin_path(command):
    cmds = {
        'ifconfig': 'fake/ifconfig',
        'route': 'fake/route',
    }
    return cmds.get(command, None)


NETBSD_IFCONFIG_A_OUT_7_1 = r'''
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 33624
        inet 127.0.0.1 netmask 0xff000000
        inet6 ::1 prefixlen 128
        inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1
re0: flags=8843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        capabilities=3f80<TSO4,IP4CSUM_Rx,IP4CSUM_Tx,TCP4CSUM_Rx,TCP4CSUM_Tx>
        capabilities=3f80<UDP4CSUM_Rx,UDP4CSUM_Tx>
        enabled=0
        ec_capabilities=3<VLAN_MTU,VLAN_HWTAGGING>
        ec_enabled=0
        address: 52:54:00:63:55:af
        media: Ethernet autoselect (100baseTX full-duplex)
        status: active
        inet 192.168.122.205 netmask 0xffffff00 broadcast 192.168.122.255
        inet6 fe80::5054:ff:fe63:55af%re0 prefixlen 64 scopeid 0x2
'''

NETBSD_IFCONFIG_A_OUT_POST_7_1 = r'''
lo0: flags=0x8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 33624
        inet 127.0.0.1/8 flags 0x0
        inet6 ::1/128 flags 0x20<NODAD>
        inet6 fe80::1%lo0/64 flags 0x0 scopeid 0x1
re0: flags=0x8843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        capabilities=3f80<TSO4,IP4CSUM_Rx,IP4CSUM_Tx,TCP4CSUM_Rx,TCP4CSUM_Tx>
        capabilities=3f80<UDP4CSUM_Rx,UDP4CSUM_Tx>
        enabled=0
        ec_capabilities=3<VLAN_MTU,VLAN_HWTAGGING>
        ec_enabled=0
        address: 52:54:00:63:55:af
        media: Ethernet autoselect (100baseTX full-duplex)
        status: active
        inet 192.168.122.205/24 broadcast 192.168.122.255 flags 0x0
        inet6 fe80::5054:ff:fe63:55af%re0/64 flags 0x0 scopeid 0x2
'''

NETBSD_EXPECTED = {'all_ipv4_addresses': ['192.168.122.205'],
                   'all_ipv6_addresses': ['fe80::5054:ff:fe63:55af%re0'],
                   'default_ipv4': {},
                   'default_ipv6': {},
                   'interfaces': ['lo0', 're0'],
                   'lo0': {'device': 'lo0',
                           'flags': ['UP', 'LOOPBACK', 'RUNNING', 'MULTICAST'],
                           'ipv4': [{'address': '127.0.0.1',
                                     'broadcast': '127.255.255.255',
                                     'netmask': '255.0.0.0',
                                     'network': '127.0.0.0'}],
                           'ipv6': [{'address': '::1', 'prefix': '128'},
                                    {'address': 'fe80::1%lo0', 'prefix': '64', 'scope': '0x1'}],
                           'macaddress': 'unknown',
                           'mtu': '33624',
                           'type': 'loopback'},
                   're0': {'device': 're0',
                           'flags': ['UP', 'BROADCAST', 'RUNNING', 'SIMPLEX', 'MULTICAST'],
                           'ipv4': [{'address': '192.168.122.205',
                                     'broadcast': '192.168.122.255',
                                     'netmask': '255.255.255.0',
                                     'network': '192.168.122.0'}],
                           'ipv6': [{'address': 'fe80::5054:ff:fe63:55af%re0',
                                     'prefix': '64',
                                     'scope': '0x2'}],
                           'macaddress': 'unknown',
                           'media': 'Ethernet',
                           'media_options': [],
                           'media_select': 'autoselect',
                           'media_type': '100baseTX',
                           'mtu': '1500',
                           'status': 'active',
                           'type': 'ether'}}


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "mock_run_command": [
                    (0, "Foo", ""),
                    (0, "Foo", ""),
                    (0, NETBSD_IFCONFIG_A_OUT_7_1, ""),
                ],
            },
            NETBSD_EXPECTED,
            id="old-ifconfig",
        ),
        pytest.param(
            {
                "mock_run_command": [
                    (0, "Foo", ""),
                    (0, "Foo", ""),
                    (0, NETBSD_IFCONFIG_A_OUT_POST_7_1, ""),
                ],
            },
            NETBSD_EXPECTED,
            id="post-7-1-ifconfig",
        ),
    ],
)
def test_generic_bsd_ifconfig(mocker, test_input, expected):
    module = mocker.MagicMock()
    mocker.patch.object(module, "get_bin_path", side_effect=mock_get_bin_path)
    mocker.patch.object(
        module, "run_command", side_effect=test_input["mock_run_command"]
    )

    bsd_net = generic_bsd.GenericBsdIfconfigNetwork(module)
    res = bsd_net.populate()
    assert res == expected


def test_compare_old_new_ifconfig(mocker):
    old_ifconfig_module = mocker.MagicMock()
    mocker.patch.object(old_ifconfig_module, "get_bin_path", side_effect=mock_get_bin_path)
    mocker.patch.object(
        old_ifconfig_module,
        "run_command",
        side_effect=[
            (0, "Foo", ""),
            (0, "Foo", ""),
            (0, NETBSD_IFCONFIG_A_OUT_7_1, ""),
        ],
    )
    old_bsd_net = generic_bsd.GenericBsdIfconfigNetwork(old_ifconfig_module)
    old_res = old_bsd_net.populate()

    new_ifconfig_module = mocker.MagicMock()
    mocker.patch.object(new_ifconfig_module, "get_bin_path", side_effect=mock_get_bin_path)
    mocker.patch.object(
        new_ifconfig_module,
        "run_command",
        side_effect=[
            (0, "Foo", ""),
            (0, "Foo", ""),
            (0, NETBSD_IFCONFIG_A_OUT_POST_7_1, ""),
        ],
    )
    new_bsd_net = generic_bsd.GenericBsdIfconfigNetwork(new_ifconfig_module)
    new_res = new_bsd_net.populate()
    assert old_res == new_res


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            "inet 192.168.7.113 netmask 0xffffff00 broadcast 192.168.7.255",
            (
                {
                    'ipv4': [
                        {
                            'address': '192.168.7.113',
                            'netmask': '255.255.255.0',
                            'network': '192.168.7.0',
                            'broadcast': '192.168.7.255',
                        }
                    ]
                },
                {'all_ipv4_addresses': ['192.168.7.113']},
            ),
            id="ifconfig-output-1",
        ),
        pytest.param(
            "inet 10.109.188.206 --> 10.109.188.206 netmask 0xffffe000",
            (
                {
                    'ipv4': [
                        {
                            'address': '10.109.188.206',
                            'netmask': '255.255.224.0',
                            'network': '10.109.160.0',
                            'broadcast': '10.109.191.255',
                        }
                    ]
                },
                {'all_ipv4_addresses': ['10.109.188.206']},
            ),
            id="ifconfig-output-2",
        ),
    ],
)
def test_ensure_correct_netmask_parsing(test_input, expected):
    n = generic_bsd.GenericBsdIfconfigNetwork(None)
    words = test_input.split()
    current_if = {"ipv4": []}
    ips = {"all_ipv4_addresses": []}
    n.parse_inet_line(words, current_if, ips)
    assert current_if == expected[0]
    assert ips == expected[1]
