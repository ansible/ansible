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

import glob
import os
import re
import socket
import struct

from ansible.module_utils.facts.network.base import Network, NetworkCollector
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.six import iteritems


class IosxrNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'iosxr'

    def populate(self, collected_facts=None):
        network_facts = {}
        data = self.get('show interfaces')

        network_facts['network_interfaces'] = {}
        network_facts['all_ipv4_address'] = []

        if data:
            interfaces = self.parse_interfaces(data)
            network_facts['network_interfaces'] = self.populate_interfaces(interfaces)
            network_facts['all_ipv4_address'] = self.populate_ipv4_interfaces(interfaces)

        data = self.get('show ipv6 interface')
        network_facts['all_ipv6_address'] = []

        if data:
            interfaces = self.parse_interfaces(data)
            network_facts['all_ipv6_address'] = self.populate_ipv6_interfaces(interfaces)

        return network_facts

    def get(self, command):
        return super(IosxrNetwork, self).get(command)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['enabled'] = self.parse_enabled(key, value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)            
            facts[key] = intf

        return facts

    def populate_ipv4_interfaces(self, interfaces):
        ipv4_interfaces = list()
        for key, value in iteritems(interfaces):
            addresses = re.findall(r'Internet address is (\S+)', value, re.M)
            if len(addresses) == 0:
                continue
            for address in addresses:
                if address == 'Unknown':
                    continue
                addr = address.split('/')[0].strip()
                ipv4_interfaces.append(addr)

        return ipv4_interfaces

    def populate_ipv6_interfaces(self, interfaces):
        ipv6_interfaces = list()
        for key, value in iteritems(interfaces):
            if key in ['No', 'RPF'] or key.startswith('IP'):
                continue
            addresses = re.findall(r'\s+(.+), subnet', value, re.M)
            for address in addresses:
                ipv6_interfaces.append(address.strip())

        return ipv6_interfaces

    def parse_description(self, value):
        match = re.search(r'Description: (.+)$', value, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, value):
        match = re.search(r'address is (\S+)', value)
        if match:
            return match.group(1)

    def parse_mtu(self, value):
        match = re.search(r'MTU (\d+)', value)
        if match:
            return int(match.group(1))

    def parse_enabled(self, key, value):
        match = re.search(r'%s is (up|down|administratively down)' % key, value)
        if match:
            if match.group(1) == 'up':
                return True
        return False

    def get(self, command):
        resp = self.connection.get(command)
        if '% This is an unconverted command' in resp:
            raise ValueError('unconverted command: %s' % command)
        return resp

class IosxrNetworkCollector(NetworkCollector):
    _platform = 'iosxr'
    _fact_class = IosxrNetwork
    required_facts = set(['platform'])
