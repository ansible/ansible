# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, A10 Networks Inc.
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import json
import platform

from ansible.module_utils.network.a10.acos import run_commands
from ansible.module_utils.network.a10.acos import get_capabilities
from ansible.module_utils.six import iteritems


class FactsBase(object):

    def __init__(self, module):
        self.module = module
        self.warnings = []
        self.facts = {}
        self.capabilities = get_capabilities(self.module)

    def populate(self):
        pass

    def transform_dict(self, data, keymap):
        transform = {}
        for key, fact in keymap:
            if key in data:
                transform[fact] = data[key]
        return transform

    def transform_iterable(self, iterable, keymap):
        for item in iterable:
            yield self.transform_dict(item, keymap)


class Default(FactsBase):

    def populate(self):
        COMMANDS = []
        COMMANDS.append('show license')
        COMMANDS.append('show bootimage | include primary')
        COMMANDS.append('show hardware | include Serial')
        COMMANDS.append('show version | include ACOS')
        COMMANDS.append('show hardware | include Thunder')
        responses = run_commands(self.module, commands=COMMANDS,
                                 check_rc=False)
        self.facts['api'] = 'cliConf'
        self.facts['hostid'] = self.get_value(responses[0])
        self.facts['image'] = self.parse_image(responses[1])
        self.facts['python_version'] = platform.python_version()
        self.facts['serialnum'] = self.get_value(responses[2])
        self.facts['version'] = responses[3].strip()
        self.facts['model'] = responses[4].strip()

    def parse_model(self, value):
        match = re.search(r'Virtualization type: (\S+)', value)
        if match:
            return match.group(1).strip()
        return ''

    def parse_image(self, value):
        value = value.strip()
        match = re.search(r'Hard Disk primary \s*(\S+)', value)
        if match:
            return match.group(1).strip()

    def parse_hostname(self, hostname):
        hostname = hostname.strip().replace("\n", "")
        if len(hostname) > 0:
            hostname = json.loads(hostname)
            if 'hostname' in hostname and 'value' in hostname['hostname']:
                return hostname['hostname']['value']
        return ''

    def get_value(self, value):
        value = value.strip()
        value = value[value.find(':') + 1:]
        return value.strip()


class Hardware(FactsBase):

    def parse_memory(self, data):
        # Example - Memory 8071 Mbyte, Free Memory 3816 Mbyte
        total_mem, free_mem = data.strip().split(',')
        total_mem = total_mem[total_mem.find('y') + 1:].strip()
        free_mem = free_mem[free_mem.find('y') + 1:].strip()
        return total_mem, free_mem

    def populate(self):
        COMMANDS = []
        COMMANDS.append('show version | section Memory')
        responses = run_commands(self.module, commands=COMMANDS,
                                 check_rc=False)
        memory_info = self.parse_memory(responses[0])
        self.facts['memtotal_mb'], self.facts['memfree_mb'] = memory_info


class Interfaces(FactsBase):

    ipv4_addr_list = []
    ipv6_addr_list = []

    def populate(self):
        self.facts['interfaces'] = {}
        self.facts['all_ipv4_addresses'] = []
        self.facts['all_ipv6_addresses'] = []
        COMMANDS = []
        COMMANDS.append('show interfaces')
        responses = run_commands(self.module, commands=COMMANDS,
                                 check_rc=False)

        data = responses[0].strip().split('\n\n  ')
        all_interface_list = {}
        for data_obj in data:
            interfaces = self.parse_interface_key(data_obj)
            all_interface_list.update(self.populate_interfaces(interfaces))
        self.facts['interfaces'].update(all_interface_list)
        self.facts['all_ipv4_addresses'] = self.ipv4_addr_list
        self.facts['all_ipv6_addresses'] = self.ipv6_addr_list

    def parse_interface_key(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r"^((?:\S+\s+){1}\S+).*", line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            iface = dict()
            iface['name'] = self.parse_interface_name(value)
            iface['macaddress'] = self.parse_macaddress(value)
            iface['mtu'] = self.parse_mtu(value)
            iface['duplex'] = self.parse_duplex(value)
            iface['operstatus'] = self.parse_operstatus(value)
            iface['ipv4'] = self.parse_ipv4(value)
            iface['ipv6'] = self.parse_ipv6(value)

            facts[key] = iface
        return facts

    def parse_interface_name(self, data):
        match = re.search(r'Interface name is (\S+)', data)
        if match:
            return match.group(1)
        return ''

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is (?:.*), Address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        addr_list = []
        match1 = re.findall(r'Internet address is (\S+)', data)
        match2 = re.findall(r'Subnet mask is (\S+)', data)
        if match1 and match2 and len(match1) == len(match2):
            for i in range(len(match1)):
                addr_pair = dict()
                addr_pair['address'] = match1[i].replace(',', '')
                self.ipv4_addr_list.append(addr_pair['address'])
                addr_pair['subnet'] = sum(
                    bin(int(x)).count('1') for x in match2[i].split('.'))
                addr_list.append(addr_pair)
        return addr_list

    def parse_ipv6(self, data):
        addr_list = []
        match1 = re.findall(r'IPv6 address is (\S+) Prefix (\S+)', data)
        for item in match1:
            addr_dict = dict()
            addr_dict['address'] = item[0]
            self.ipv6_addr_list.append(addr_dict['address'])
            addr_dict['prefix'] = item[1]
            addr_list.append(addr_dict)
        return addr_list

    def parse_mtu(self, data):
        match = re.search(r'MTU is (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'BW (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'Duplex (\w+)', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
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


class Config(FactsBase):

    def populate(self):
        responses = run_commands(self.module, commands=['show running-config'],
                                 check_rc=False)
        self.facts['config'] = responses[0]
