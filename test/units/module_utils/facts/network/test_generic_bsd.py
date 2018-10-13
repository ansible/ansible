# -*- coding: utf-8 -*-
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
#

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from units.compat.mock import Mock
from units.compat import unittest

from ansible.module_utils.facts.network import generic_bsd


def get_bin_path(command):
    if command == 'ifconfig':
        return 'fake/ifconfig'
    elif command == 'route':
        return 'fake/route'
    return None


netbsd_ifconfig_a_out_7_1 = r'''
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

netbsd_ifconfig_a_out_post_7_1 = r'''
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


def run_command_old_ifconfig(command):
    if command == 'fake/route':
        return 0, 'Foo', ''
    if command == ['fake/ifconfig', '-a']:
        return 0, netbsd_ifconfig_a_out_7_1, ''
    return 1, '', ''


def run_command_post_7_1_ifconfig(command):
    if command == 'fake/route':
        return 0, 'Foo', ''
    if command == ['fake/ifconfig', '-a']:
        return 0, netbsd_ifconfig_a_out_post_7_1, ''
    return 1, '', ''


class TestGenericBsdNetworkNetBSD(unittest.TestCase):
    gather_subset = ['all']

    def setUp(self):
        self.maxDiff = None
        self.longMessage = True

    # TODO: extract module run_command/get_bin_path usage to methods I can mock without mocking all of run_command
    def test(self):
        module = self._mock_module()
        module.get_bin_path.side_effect = get_bin_path
        module.run_command.side_effect = run_command_old_ifconfig

        bsd_net = generic_bsd.GenericBsdIfconfigNetwork(module)

        res = bsd_net.populate()
        self.assertDictEqual(res, NETBSD_EXPECTED)

    def test_ifconfig_post_7_1(self):
        module = self._mock_module()
        module.get_bin_path.side_effect = get_bin_path
        module.run_command.side_effect = run_command_post_7_1_ifconfig

        bsd_net = generic_bsd.GenericBsdIfconfigNetwork(module)

        res = bsd_net.populate()
        self.assertDictEqual(res, NETBSD_EXPECTED)

    def test_netbsd_ifconfig_old_and_new(self):
        module_new = self._mock_module()
        module_new.get_bin_path.side_effect = get_bin_path
        module_new.run_command.side_effect = run_command_post_7_1_ifconfig

        bsd_net_new = generic_bsd.GenericBsdIfconfigNetwork(module_new)
        res_new = bsd_net_new.populate()

        module_old = self._mock_module()
        module_old.get_bin_path.side_effect = get_bin_path
        module_old.run_command.side_effect = run_command_old_ifconfig

        bsd_net_old = generic_bsd.GenericBsdIfconfigNetwork(module_old)
        res_old = bsd_net_old.populate()

        self.assertDictEqual(res_old, res_new)
        self.assertDictEqual(res_old, NETBSD_EXPECTED)
        self.assertDictEqual(res_new, NETBSD_EXPECTED)

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 5,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value=None)
        return mock_module
