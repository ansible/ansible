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

import sys
import pytest

from units.compat import unittest
from ansible.errors import AnsibleFilterError
from ansible.plugins.filter.ipaddr import (ipaddr, next_nth_usable, ipsubnet,
                                           previous_nth_usable, network_in_usable, network_in_network,
                                           cidr_merge, ipmath)
netaddr = pytest.importorskip('netaddr')


class TestIpFilter(unittest.TestCase):
    def test_netmask(self):
        address = '1.1.1.1/24'
        self.assertEqual(ipaddr(address, 'netmask'), '255.255.255.0')
        address = '1.1.1.1/25'
        self.assertEqual(ipaddr(address, 'netmask'), '255.255.255.128')
        address = '1.12.1.34/32'
        self.assertEqual(ipaddr(address, 'netmask'), '255.255.255.255')

    def test_network(self):
        address = '1.12.1.34/32'
        self.assertEqual(ipaddr(address, 'network'), '1.12.1.34')
        address = '1.12.1.34/255.255.255.255'
        self.assertEqual(ipaddr(address, 'network'), '1.12.1.34')
        address = '1.12.1.34'
        self.assertEqual(ipaddr(address, 'network'), '1.12.1.34')
        address = '1.12.1.35/31'
        self.assertEqual(ipaddr(address, 'network'), '1.12.1.34')
        address = '1.12.1.34/24'
        self.assertEqual(ipaddr(address, 'network'), '1.12.1.0')

    def test_broadcast(self):
        address = '1.12.1.34/24'
        self.assertEqual(ipaddr(address, 'broadcast'), '1.12.1.255')
        address = '1.12.1.34/16'
        self.assertEqual(ipaddr(address, 'broadcast'), '1.12.255.255')
        address = '1.12.1.34/27'
        self.assertEqual(ipaddr(address, 'broadcast'), '1.12.1.63')
        address = '1.12.1.34/32'
        self.assertEqual(ipaddr(address, 'broadcast'), None)
        address = '1.12.1.35/31'
        self.assertEqual(ipaddr(address, 'broadcast'), None)

    def test_first_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.1')
        address = '1.12.1.36/24'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.1')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'first_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.33')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.33')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.36')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'first_usable'), '1.12.1.36')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'first_usable'), None)

    def test_last_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.254')
        address = '1.12.1.36/24'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.254')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.46')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.46')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.37')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'last_usable'), '1.12.1.37')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'last_usable'), None)

    def test_wildcard(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.255')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.127')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.15')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.15')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.1')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.1')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.0')
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'wildcard'), '0.0.0.255')

    def test_size_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'size_usable'), 254)
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'size_usable'), 126)
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'size_usable'), 14)
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'size_usable'), 14)
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'size_usable'), 2)
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'size_usable'), 2)
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'size_usable'), 0)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'size_usable'), 254)

    def test_range_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.1-1.12.1.254')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.1-1.12.1.126')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.33-1.12.1.46')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.33-1.12.1.46')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.36-1.12.1.37')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.36-1.12.1.37')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'range_usable'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'range_usable'), '1.12.1.1-1.12.1.254')

    def test_address_prefix(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'address/prefix'), None)
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'address/prefix'), None)
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'address/prefix'), '1.12.1.36/28')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'address/prefix'), '1.12.1.36/28')
        # address = '1.12.1.36/31'
        # self.assertEqual(ipaddr(address, 'address/prefix'), '1.12.1.36/31') - unfixable?
        # address = '1.12.1.37/31'
        # self.assertEqual(ipaddr(address, 'address/prefix'), '1.12.1.37/31') - unfixable?
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'address/prefix'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'address/prefix'), '1.12.1.254/24')

    def test_ip_prefix(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'ip/prefix'), None)
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'ip/prefix'), None)
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'ip/prefix'), '1.12.1.36/28')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'ip/prefix'), '1.12.1.36/28')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'ip/prefix'), '1.12.1.36/31')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'ip/prefix'), '1.12.1.37/31')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'ip/prefix'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'ip/prefix'), '1.12.1.254/24')

    def test_ip_netmask(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'ip_netmask'), None)
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'ip_netmask'), None)
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'ip_netmask'), '1.12.1.36 255.255.255.240')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'ip_netmask'), '1.12.1.36 255.255.255.240')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'ip_netmask'), '1.12.1.36 255.255.255.254')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'ip_netmask'), '1.12.1.37 255.255.255.254')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'ip_netmask'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'ip_netmask'), '1.12.1.254 255.255.255.0')

    '''
    def test_ip_wildcard(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), None)
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), None)
        #address = '1.12.1.34'
        #self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), '1.12.1.36 0.0.0.15')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), '1.12.1.36 0.0.0.15')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), '1.12.1.36 0.0.0.1')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), '1.12.1.37 0.0.0.1')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'ip_wildcard'), '1.12.1.254 0.0.0.255')
    '''
    def test_network_id(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.0')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.0')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.32')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.32')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.36')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.36')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.36')
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'network_id'), '1.12.1.0')

    def test_network_prefix(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.0/24')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.0/25')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.32/28')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.32/28')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.36/31')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.36/31')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.36/32')
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'network/prefix'), '1.12.1.0/24')

    def test_network_netmask(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.0 255.255.255.0')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.0 255.255.255.128')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.32 255.255.255.240')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.32 255.255.255.240')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.36 255.255.255.254')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.36 255.255.255.254')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.36 255.255.255.255')
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'network_netmask'), '1.12.1.0 255.255.255.0')

    def test_network_wildcard(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.0 0.0.0.255')
        address = '1.12.1.0/25'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.0 0.0.0.127')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.32 0.0.0.15')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.32 0.0.0.15')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.36 0.0.0.1')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.36 0.0.0.1')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.36 0.0.0.0')
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'network_wildcard'), '1.12.1.0 0.0.0.255')

    def test_next_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'next_usable'), '1.12.1.1')
        address = '1.12.1.36/24'
        self.assertEqual(ipaddr(address, 'next_usable'), '1.12.1.37')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'next_usable'), '1.12.1.37')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'next_usable'), '1.12.1.37')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'next_usable'), '1.12.1.37')
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'next_usable'), None)
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'next_usable'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'next_usable'), None)

    def test_previous_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(ipaddr(address, 'previous_usable'), None)
        address = '1.12.1.36/24'
        self.assertEqual(ipaddr(address, 'previous_usable'), '1.12.1.35')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(ipaddr(address, 'previous_usable'), '1.12.1.35')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(ipaddr(address, 'previous_usable'), '1.12.1.35')
        address = '1.12.1.36/31'
        self.assertEqual(ipaddr(address, 'previous_usable'), None)
        address = '1.12.1.37/31'
        self.assertEqual(ipaddr(address, 'previous_usable'), '1.12.1.36')
        address = '1.12.1.36/32'
        self.assertEqual(ipaddr(address, 'previous_usable'), None)
        address = '1.12.1.254/24'
        self.assertEqual(ipaddr(address, 'previous_usable'), '1.12.1.253')

    def test_next_nth_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(next_nth_usable(address, 5), '1.12.1.5')
        address = '1.12.1.36/24'
        self.assertEqual(next_nth_usable(address, 10), '1.12.1.46')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(next_nth_usable(address, 4), '1.12.1.40')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(next_nth_usable(address, 4), '1.12.1.40')
        address = '1.12.1.36/31'
        self.assertEqual(next_nth_usable(address, 1), '1.12.1.37')
        address = '1.12.1.37/31'
        self.assertEqual(next_nth_usable(address, 1), None)
        address = '1.12.1.36/32'
        self.assertEqual(next_nth_usable(address, 1), None)
        address = '1.12.1.254/24'
        self.assertEqual(next_nth_usable(address, 2), None)

    def test_previous_nth_usable(self):
        address = '1.12.1.0/24'
        self.assertEqual(previous_nth_usable(address, 5), None)
        address = '1.12.1.36/24'
        self.assertEqual(previous_nth_usable(address, 10), '1.12.1.26')
        # address = '1.12.1.34'
        # self.assertFalse(ipaddr(address, 'last_usable'), 'Not a network address')
        address = '1.12.1.36/28'
        self.assertEqual(previous_nth_usable(address, 2), '1.12.1.34')
        address = '1.12.1.36/255.255.255.240'
        self.assertEqual(previous_nth_usable(address, 2), '1.12.1.34')
        address = '1.12.1.36/31'
        self.assertEqual(previous_nth_usable(address, 1), None)
        address = '1.12.1.37/31'
        self.assertEqual(previous_nth_usable(address, 1), '1.12.1.36')
        address = '1.12.1.36/32'
        self.assertEqual(previous_nth_usable(address, 1), None)
        address = '1.12.1.254/24'
        self.assertEqual(previous_nth_usable(address, 2), '1.12.1.252')

    def test_network_in_usable(self):
        subnet = '1.12.1.0/24'
        address = '1.12.1.10'
        self.assertEqual(network_in_usable(subnet, address), True)
        subnet = '1.12.1.0/24'
        address = '1.12.0.10'
        self.assertEqual(network_in_usable(subnet, address), False)
        subnet = '1.12.1.32/28'
        address = '1.12.1.36'
        self.assertEqual(network_in_usable(subnet, address), True)
        subnet = '1.12.1.32/28'
        address = '1.12.1.36/31'
        self.assertEqual(network_in_usable(subnet, address), True)
        subnet = '1.12.1.32/28'
        address = '1.12.1.48/31'
        self.assertEqual(network_in_usable(subnet, address), False)
        subnet = '1.12.1.32/255.255.255.240'
        address = '1.12.1.31'
        self.assertEqual(network_in_usable(subnet, address), False)
        subnet = '1.12.1.36/31'
        address = '1.12.1.36'
        self.assertEqual(network_in_usable(subnet, address), True)
        subnet = '1.12.1.37/31'
        address = '1.12.1.35'
        self.assertEqual(network_in_usable(subnet, address), False)
        subnet = '1.12.1.36/32'
        address = '1.12.1.36'
        self.assertEqual(network_in_usable(subnet, address), True)
        subnet = '1.12.1.0/24'
        address = '1.12.2.0'
        self.assertEqual(network_in_usable(subnet, address), False)

    def test_network_in_network(self):
        subnet = '1.12.1.0/24'
        address = '1.12.1.0'
        self.assertEqual(network_in_network(subnet, address), True)
        subnet = '1.12.1.0/24'
        address = '1.12.0.10'
        self.assertEqual(network_in_network(subnet, address), False)
        subnet = '1.12.1.32/28'
        address = '1.12.1.32/28'
        self.assertEqual(network_in_network(subnet, address), True)
        subnet = '1.12.1.32/28'
        address = '1.12.1.47'
        self.assertEqual(network_in_network(subnet, address), True)
        subnet = '1.12.1.32/28'
        address = '1.12.1.48/31'
        self.assertEqual(network_in_network(subnet, address), False)
        subnet = '1.12.1.32/255.255.255.240'
        address = '1.12.1.31'
        self.assertEqual(network_in_network(subnet, address), False)
        subnet = '1.12.1.36/31'
        address = '1.12.1.36'
        self.assertEqual(network_in_network(subnet, address), True)
        subnet = '1.12.1.37/31'
        address = '1.12.1.35'
        self.assertEqual(network_in_network(subnet, address), False)
        subnet = '1.12.1.36/32'
        address = '1.12.1.36'
        self.assertEqual(network_in_network(subnet, address), True)
        subnet = '1.12.1.0/24'
        address = '1.12.2.0'
        self.assertEqual(network_in_network(subnet, address), False)

    def test_cidr_merge(self):
        self.assertEqual(cidr_merge([]), [])
        self.assertEqual(cidr_merge([], 'span'), None)
        subnets = ['1.12.1.0/24']
        self.assertEqual(cidr_merge(subnets), subnets)
        self.assertEqual(cidr_merge(subnets, 'span'), subnets[0])
        subnets = ['1.12.1.0/25', '1.12.1.128/25']
        self.assertEqual(cidr_merge(subnets), ['1.12.1.0/24'])
        self.assertEqual(cidr_merge(subnets, 'span'), '1.12.1.0/24')
        subnets = ['1.12.1.0/25', '1.12.1.128/25', '1.12.2.0/24']
        self.assertEqual(cidr_merge(subnets), ['1.12.1.0/24', '1.12.2.0/24'])
        self.assertEqual(cidr_merge(subnets, 'span'), '1.12.0.0/22')
        subnets = ['1.12.1.1', '1.12.1.255']
        self.assertEqual(cidr_merge(subnets), ['1.12.1.1/32', '1.12.1.255/32'])
        self.assertEqual(cidr_merge(subnets, 'span'), '1.12.1.0/24')

    def test_ipmath(self):
        self.assertEqual(ipmath('192.168.1.5', 5), '192.168.1.10')
        self.assertEqual(ipmath('192.168.1.5', -5), '192.168.1.0')
        self.assertEqual(ipmath('192.168.0.5', -10), '192.167.255.251')

        self.assertEqual(ipmath('192.168.1.1/24', 5), '192.168.1.6')
        self.assertEqual(ipmath('192.168.1.6/24', -5), '192.168.1.1')
        self.assertEqual(ipmath('192.168.2.6/24', -10), '192.168.1.252')

        self.assertEqual(ipmath('2001::1', 8), '2001::9')
        self.assertEqual(ipmath('2001::1', 9), '2001::a')
        self.assertEqual(ipmath('2001::1', 10), '2001::b')
        self.assertEqual(ipmath('2001::5', -3), '2001::2')
        self.assertEqual(
            ipmath('2001::5', -10),
            '2000:ffff:ffff:ffff:ffff:ffff:ffff:fffb'
        )

        expected = 'You must pass a valid IP address; invalid_ip is invalid'
        with self.assertRaises(AnsibleFilterError) as exc:
            ipmath('invalid_ip', 8)
        self.assertEqual(exc.exception.message, expected)

        expected = (
            'You must pass an integer for arithmetic; '
            'some_number is not a valid integer'
        )
        with self.assertRaises(AnsibleFilterError) as exc:
            ipmath('1.2.3.4', 'some_number')
        self.assertEqual(exc.exception.message, expected)

    def test_ipsubnet(self):
        test_cases = (
            (('1.1.1.1/24', '30'), '64'),
            (('1.1.1.1/25', '24'), '0'),
            (('1.12.1.34/32', '1.12.1.34/24'), '35'),
            (('192.168.50.0/24', '192.168.0.0/16'), '51'),
            (('192.168.144.5', '192.168.0.0/16'), '36870'),
            (('192.168.144.5', '192.168.144.5/24'), '6'),
            (('192.168.144.5/32', '192.168.144.0/24'), '6'),
            (('192.168.144.16/30', '192.168.144.0/24'), '5'),
            (('192.168.144.5', ), '192.168.144.5/32'),
            (('192.168.0.0/16', ), '192.168.0.0/16'),
            (('192.168.144.5', ), '192.168.144.5/32'),
            (('192.168.0.0/16', '20'), '16'),
            (('192.168.0.0/16', '20', '0'), '192.168.0.0/20'),
            (('192.168.0.0/16', '20', '-1'), '192.168.240.0/20'),
            (('192.168.0.0/16', '20', '5'), '192.168.80.0/20'),
            (('192.168.0.0/16', '20', '-5'), '192.168.176.0/20'),
            (('192.168.144.5', '20'), '192.168.144.0/20'),
            (('192.168.144.5', '18', '0'), '192.168.128.0/18'),
            (('192.168.144.5', '18', '-1'), '192.168.144.4/31'),
            (('192.168.144.5', '18', '5'), '192.168.144.0/23'),
            (('192.168.144.5', '18', '-5'), '192.168.144.0/27'),
            (('span', 'test', 'error'), False),
            (('test', ), False),
            (('192.168.144.5', '500000', '-5'), False),
            (('192.168.144.5', '18', '500000'), False),
            (('200000', '18', '-5'), '0.3.13.64/27'),
        )
        for args, res in test_cases:
            self._test_ipsubnet(args, res)

    def _test_ipsubnet(self, ipsubnet_args, expected_result):
        if ipsubnet_args == ('1.1.1.1/25', '24') and expected_result == '0' and sys.version_info >= (3, 7):
            return  # fails in netaddr on Python 3.7+

        self.assertEqual(ipsubnet(*ipsubnet_args), expected_result)

        with self.assertRaisesRegexp(AnsibleFilterError, 'You must pass a valid subnet or IP address; invalid_subnet is invalid'):
            ipsubnet('192.168.144.5', 'invalid_subnet')

        with self.assertRaisesRegexp(AnsibleFilterError, '192.168.144.0/30 is not in the subnet 192.168.144.4/30'):
            ipsubnet('192.168.144.1/30', '192.168.144.5/30')
