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


class EosNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'eos'

    def populate(self, collected_facts=None):
        network_facts = {}

        all_ipv4_addresses = list()
        all_ipv6_addresses = list()

        interfaces = self.get('show interfaces | json')
        network_facts['network_interfaces'] = {}

        for key, value in iteritems(interfaces['interfaces']):
            name = value['name']

            obj = {}
            obj['description'] = value['description']
            obj['enabled'] = value['interface_status'] != 'disabled'
            obj['mtu'] = value['mtu']
            obj['mac'] = value['physical_address']

            network_facts['network_interfaces'][name] = obj

            for item in value['interface_address']:
                addr = item.get('primaryIp', {}).get('address')
                if addr:
                    all_ipv4_addresses.append(addr)

        network_facts['all_ipv4_addresses'] = all_ipv4_addresses
        network_facts['all_ipv6_addresses'] = all_ipv6_addresses

        return network_facts

    def get(self, command):
        resp = self.connection.get(command)
        if '% This is an unconverted command' in resp:
            raise ValueError('unconverted command: %s' % command)
        return self.transform(self.module.from_json(resp))

    def convert(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower().replace('-', '_')

    def transform(self, output):
        obj = {}
        for key, val in iteritems(output):
            key = self.convert(key)
            if isinstance(val, dict):
                obj[key] = self.transform(val)
            elif isinstance(val, list):
                items = list()
                for item in val:
                    if isinstance(val, dict):
                        items.append(self.transform(item))
                    else:
                        items = val
                obj[key] = items
            else:
                obj[key] = val
        return obj


class EosNetworkCollector(NetworkCollector):
    _platform = 'eos'
    _fact_class = EosNetwork
    required_facts = set(['platform'])
