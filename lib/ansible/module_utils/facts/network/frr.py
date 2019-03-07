#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.module_utils.facts.network.base import Network, NetworkCollector
from ansible.module_utils.six import iteritems


class FrrNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'frr'

    def parse_facts(self, pattern, data):
        value = None
        match = re.search(pattern, data, re.M)
        if match:
            value = match.group(1)
        return value

    def get(self, command):
        return super(FrrNetwork, self).get(command)

    def populate(self, collected_facts=None):
        network_facts = {}
        data = self.get('show interface')
        network_facts['network_interfaces'] = {}

        network_facts['all_ipv4_address'] = []
        network_facts['all_ipv6_address'] = []

        if data:
            interfaces = self.parse_interfaces(data)
            network_facts['network_interfaces'] = self.populate_interfaces(interfaces)
            network_facts['all_ipv4_address'] = self.populate_ipv4_interfaces(interfaces)
            network_facts['all_ipv6_address'] = self.populate_ipv6_interfaces(interfaces)

        return network_facts

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^Interface (\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        counters = {
            'description': r'Description: (.+)',
            'macaddress': r'HWaddr: (\S+)',
            'type': r'Type: (\S+)',
            'vrf': r'vrf: (\S+)',
            'mtu': r'mtu (\d+)',
            'bandwidth': r'bandwidth (\d+)',
            'lineprotocol': r'line protocol is (\S+)',
            'operstatus': r'^(?:.+) is (.+),'
        }

        for key, value in iteritems(interfaces):
            intf = dict()
            for fact, pattern in iteritems(counters):
                intf[fact] = self.parse_facts(pattern, value)
            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        ipv4_interfaces = []
        for key, value in data.items():
            primary_address = addresses = []
            primary_address = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s{2,})', value, re.M)
            addresses = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s+)secondary', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                ipv4_interfaces.append(ipv4)
        return ipv4_interfaces

    def populate_ipv6_interfaces(self, data):
        ipv6_interfaces = []
        for key, value in data.items():
            addresses = re.findall(r'inet6 (\S+)', value, re.M)
            for address in addresses:
                addr, subnet = address.split("/")
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                ipv6_interfaces.append(ipv6)
        return ipv6_interfaces


class FrrNetworkCollector(NetworkCollector):
    _platform = 'frr'
    _fact_class = FrrNetwork
    required_facts = set(['platform'])
