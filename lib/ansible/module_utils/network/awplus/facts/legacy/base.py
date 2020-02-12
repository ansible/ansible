# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The awplus legacy fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import platform
import re
import sys

from ansible.module_utils.network.awplus.awplus import run_commands, get_capabilities
from ansible.module_utils.network.awplus.utils.utils import normalize_interface
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None

    def populate(self):
        self.responses = run_commands(
            self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):
    COMMANDS = ['show system']

    def populate(self):
        super(Default, self).populate()
        self.facts.update(self.platform_facts())
        data = self.responses[0]
        if data:
            self.facts['serialnum'] = self.parse_serialnum(data)

    def parse_serialnum(self, data):
        match = re.search(
            r'^Base\s+ (\S+)\s+ (\S+)\s+ (\S+)\s+ (\S+)\s+ (\S+)', data, re.M)
        if match:
            return match.group(5)

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
        'show file systems',
        'show system'
    ]

    def populate(self):
        warnings = list()
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)
            self.facts['filesystems_info'] = self.parse_filesystems_info(data)

        data = self.responses[1]
        if data:
            if 'Invalid input detected' in data:
                warnings.append('Unable to gather memory statistics')
            else:
                match = re.search(
                    r'Flash:\s+([0-9]*[.]?[0-9]+[A-Z]+).+Available:\s+([0-9]*[.]?[0-9]+[A-Z]+)', data)
                if match:
                    self.facts['memtotal'] = match.group(1)
                    self.facts['memfree'] = match.group(2)

    def parse_filesystems(self, data):
        return re.findall(r'\s+(\w+)\s+r[w|o]', data, re.M)

    def parse_filesystems_info(self, data):
        facts = dict()
        fs = ''
        test = ''
        for line in data.split('\n'):
            match = re.match(r'.+\s+(\w+)\s+r[w|o].+', line, re.M)
            if match:
                fs = match.group(1)
                facts[fs] = dict()
                match = re.match(
                    r'\s+([0-9]*[.]?[0-9]+[A-Z]+)\s+([0-9]*[.]?[0-9]+[A-Z]+).+', line)
                if match:
                    facts[fs]['spacetotal'] = match.group(1)
                    facts[fs]['spacefree'] = match.group(2)

        return facts


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            data = re.sub(
                r'^Building configuration...\s+Current configuration  :  \d+ bytes\n',
                '', data, flags=re.MULTILINE)
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'show interface',
        'show ip interface',
        'show ipv6 interface',
        'show lldp',
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()
        self.facts['neighbors'] = {}

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if data:
            data = self.parse_ip_interfaces(data)
            self.populate_ipv4_interfaces(data)

        data = self.responses[2]
        if data:
            data = self.parse_ip_interfaces(data)
            self.populate_ipv6_interfaces(data)

        data = self.responses[3]
        lldp_errs = ['Invalid input', 'LLDP is not enabled']

        if data and not any(err in data for err in lldp_errs):
            neighbors = self.run(['show lldp'])
            if neighbors:
                self.facts['neighbors'].update(
                    self.parse_neighbors(neighbors[0]))

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['mediatype'] = self.parse_mediatype(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = list()
            match = re.search(r'^(\w+)\s+(\S+)\s+(.+)\s+(\w+)', value, re.M)
            # address = re.findall(r'broadcast (.+)$', value, re.M)
            if '/' not in match.group(2):
                continue
            else:
                address = match.group(2)
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    def populate_ipv6_interfaces(self, data):
        for key, value in iteritems(data):
            try:
                self.facts['interfaces'][key]['ipv6'] = list()
            except KeyError:
                self.facts['interfaces'][key] = dict()
                self.facts['interfaces'][key]['ipv6'] = list()
            match = re.search(
                r'^(\w+)\s+(\S+)\s+(.+)\s+(\w+)\s+(\w+)', value, re.M)
            if '/' not in match.group(2):
                continue
            else:
                address = match.group(2)
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv4)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        for entry in neighbors.split('------------------------------------------------'):
            if entry == '':
                continue
            intf = self.parse_lldp_intf(entry)
            if intf is None:
                return facts
            intf = normalize_interface(intf)
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_lldp_host(entry)
            fact['port'] = self.parse_lldp_port(entry)
            facts[intf].append(fact)
        return facts

    def parse_ip_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                continue
            else:
                match = re.match(r'^([a-z]+[0-9]*)\s+', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

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

    def parse_description(self, data):
        match = re.search(r'\<\S+\>', data, re.M)
        descrip = ''
        if match:
            descrip += match.group(0)
            beginning = data.index(match.group(0))
            for i in range(beginning + 1, len(data)):
                descrip += data[i]
            return descrip

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is (?:.*), address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'IPv4 address (\S+)', data)
        if match:
            addr, masklen = match.group(1).split('/')
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'mtu (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'Bandwidth (.+)', data)
        if match:
            return match.group(1)

    def parse_duplex(self, data):
        match = re.search(r'configured duplex (\w+)', data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        match = re.search(r'media type is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is ([A-Z]+[a-z]*)', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (\S+)\s*$', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^Local Intf: (.+)$', data, re.M)
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
