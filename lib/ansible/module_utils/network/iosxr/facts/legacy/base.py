# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The iosxr legacy fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""


from __future__ import absolute_import, division, print_function
__metaclass__ = type


import platform
import re

from ansible.module_utils.network.iosxr.iosxr import run_commands, get_capabilities
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS), check_rc=False)


class Default(FactsBase):

    def populate(self):
        self.facts.update(self.platform_facts())

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('model', 'image', 'version', 'platform', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


class Hardware(FactsBase):

    COMMANDS = [
        'dir /all',
        'show memory summary'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.responses[1]
        match = re.search(r'Physical Memory: (\d+)M total \((\d+)', data)
        if match:
            self.facts['memtotal_mb'] = match.group(1)
            self.facts['memfree_mb'] = match.group(2)

    def parse_filesystems(self, data):
        return re.findall(r'^Directory of (\S+)', data, re.M)


class Config(FactsBase):

    COMMANDS = [
        'show running-config'
    ]

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(FactsBase):

    COMMANDS = [
        'show interfaces',
        'show ipv6 interface',
        'show lldp',
        'show lldp neighbors detail'
    ]

    def populate(self):
        super(Interfaces, self).populate()
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        interfaces = self.parse_interfaces(self.responses[0])
        self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if len(data) > 0:
            data = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(data)

        if 'LLDP is not enabled' not in self.responses[2]:
            neighbors = self.responses[3]
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)

            ipv4 = self.parse_ipv4(value)
            intf['ipv4'] = self.parse_ipv4(value)
            if ipv4:
                self.add_ip_address(ipv4['address'], 'ipv4')

            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv6_interfaces(self, data):
        for key, value in iteritems(data):
            if key in ['No', 'RPF'] or key.startswith('IP'):
                continue
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'\s+(.+), subnet', value, re.M)
            subnets = re.findall(r', subnet is (.+)$', value, re.M)
            for addr, subnet in zip(addresses, subnets):
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        nbors = neighbors.split('------------------------------------------------')
        for entry in nbors[1:]:
            if entry == '':
                continue
            intf = self.parse_lldp_intf(entry)
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_lldp_host(entry)
            fact['remote_description'] = self.parse_lldp_remote_desc(entry)
            fact['port'] = self.parse_lldp_port(entry)
            facts[intf].append(fact)
        return facts

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

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Internet address is (\S+)/(\d+)', data)
        if match:
            addr = match.group(1)
            masklen = int(match.group(2))
            return dict(address=addr, masklen=masklen)

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'BW (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'(\w+)(?: D|-d)uplex', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (.+)\s+?$', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^Local Interface: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_remote_desc(self, data):
        match = re.search(r'Port Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_host(self, data):
        match = re.search(r'System Name: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_port(self, data):
        match = re.search(r'Port id: (.+)$', data, re.M)
        if match:
            return match.group(1)
