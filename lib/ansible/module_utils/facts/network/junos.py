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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob, q
import os
import re
import socket
import struct

from ansible.module_utils.facts.network.base import Network, NetworkCollector
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.six import iteritems


class JunosNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'junos'

    def populate(self, collected_facts=None):
        network_facts = {}
        data = self.get('show interfaces')

        network_facts['network_interfaces'] = {}
        network_facts['all_ipv4_address'] = []
        network_facts['all_ipv6_address'] = []

        if data:
            interfaces = self.parse_interfaces(data)
            network_facts['network_interfaces'] = self.populate_interfaces(interfaces)

        data = self.get('show interfaces brief')
        if data:
            interfaces = self.parse_interfaces(data)
            self.populate_ip_address(network_facts, interfaces)

        return network_facts

    def get(self, command):
        return super(JunosNetwork, self).get(command)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''

        lines = data.split('Physical interface: ')[1:]
        for line in lines:
            if len(line) == 0:
                continue
            else:
                match = re.search(r'^(\S+)', line)
                if match:
                    intf = match.group(1)
                    key = intf.strip(',')
                    parsed[key] = line.strip(intf).strip()
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['enabled'] = self.parse_enabled(value)
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            facts[key] = intf

        return facts

    def populate_ip_address(self, network_facts, interfaces):
        for key, value in iteritems(interfaces):
            ipv4_addresses = re.findall(r'inet\s*(\S+)', value, re.M)
            if len(ipv4_addresses) == 0:
                continue
            for address in ipv4_addresses:
                addr = address.split('/')[0].strip()
                network_facts['all_ipv4_address'].append(addr)


            ipv6_addresses = re.findall(r'inet6\s*(\S+)', value, re.M)
            if len(ipv6_addresses) == 0:
                continue
            for address in ipv6_addresses:
                addr = address.split('/')[0].strip()
                network_facts['all_ipv6_address'].append(addr)

    def populate_ipv6_interfaces(self, interfaces):
        ipv6_interfaces = list()
        for key, value in iteritems(interfaces):
            addresses = re.findall(r'IPv6 address:\s*(\S+)', value, re.M)
            if len(addresses) == 0:
                continue
            for address in addresses:
                addr = address.strip()
                ipv6_interfaces.append(addr)

        return ipv6_interfaces

    def parse_description(self, value):
        match = re.search(r'\nDescription: (.+)', value)
        if match:
            return match.group(1).strip("'")

    def parse_macaddress(self, value):
        match = re.search(r'Hardware address: (\S+)', value)
        if match:
            return match.group(1)

    def parse_mtu(self, value):
        match = re.search(r'MTU: (\S+)', value, re.M)
        if match:
            return match.group(1).strip(',')

    def parse_enabled(self, value):
        match = re.search(r'^(\S+)', value)
        if match:
            if match.group(1).strip(',').lower() == 'enabled':
                return True
        return False


class JunosNetworkCollector(NetworkCollector):
    _platform = 'junos'
    _fact_class = JunosNetwork
    required_facts = set(['platform'])
