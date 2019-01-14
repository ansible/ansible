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


class VyosNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'vyos'

    def populate(self, collected_facts=None):
        network_facts = {}

        data = self.get('show interfaces detail')
        network_facts['network_interfaces'] = {}
        network_facts['all_ipv4_address'] = []
        network_facts['all_ipv6_address'] = []

        if data:
            interfaces = self.parse_interfaces(data)

        if interfaces:
            network_facts['network_interfaces'] = self.populate_interfaces(interfaces)
            self.populate_address(interfaces, network_facts)

        return network_facts

    def get(self, command):
        return super(VyosNetwork, self).get(command)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        lines = re.split(r'\n[eth|lo]', data)

        if len(lines) > 0:
            for line in lines:
                if len(line) == 0:
                    continue
                elif line[0] == ' ':
                    parsed[key] += '\n%s' % line
                else:
                    l = ''
                    if line.lower().startswith('eth'):
                        l = line.strip()
                    elif line.lower().startswith('lo'):
                        l = line.strip()
                    elif line.lower().startswith('th'):
                        l = 'e' + line.strip()
                    elif line.lower().startswith('o'):
                        l = 'l' + line.strip()
                    if l:
                        m = re.match(r'^(\S+)', l).group(1)
                        key = m.strip(':')
                        parsed[key] = l.strip(m).strip()

        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['enabled'] = self.parse_enabled(value)
            facts[key] = intf
        return facts

    def populate_address(self, interfaces, network_facts):
        for key, value in iteritems(interfaces):
            ipv4_match = re.search(r'inet (\S+)', value)
            if ipv4_match:
                network_facts['all_ipv4_address'].append(ipv4_match.group(1).split('/')[0])
            ipv6_match = re.search(r'inet6 (\S+)', value)
            if ipv6_match:
                network_facts['all_ipv6_address'].append(ipv6_match.group(1).split('/')[0])

    def parse_description(self, data):
        match = re.search(r'Description: (.+)\n', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'link/(?:loopback|ether) (\S+)', data)
        if match:
            return match.group(1)

    def parse_enabled(self, data):
        match = re.search(r'state (\S+)', data)
        if match:
            state = match.group(1)
            if state.lower() == 'up':
                return True
            elif state.lower() == 'unknown':
                return 'unknown'
        return False

    def parse_mtu(self, data):
        match = re.search(r'mtu (\d+)', data)
        if match:
            return int(match.group(1))


class VyosNetworkCollector(NetworkCollector):
    _platform = 'vyos'
    _fact_class = VyosNetwork
    required_facts = set(['platform'])
