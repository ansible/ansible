# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The exos legacy fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
import json

from ansible.module_utils.network.exos.exos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, self.COMMANDS)

    def run(self, cmd):
        return run_commands(self.module, cmd)


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show switch'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)

        data = self.responses[1]
        if data:
            self.facts['model'] = self.parse_model(data)
            self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'Image\s+: ExtremeXOS version (\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'System Type:\s+(.*$)', data, re.M)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'SysName:\s+(\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Switch\s+: \S+ (\S+)', data, re.M)
        if match:
            return match.group(1)
        # For stack, return serial number of the first switch in the stack.
        match = re.search(r'Slot-\d+\s+: \S+ (\S+)', data, re.M)
        if match:
            return match.group(1)
        # Handle unique formatting for VM
        match = re.search(r'Switch\s+: PN:\S+\s+SN:(\S+)', data, re.M)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show memory'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['memtotal_mb'] = int(round(int(self.parse_memtotal(data)) / 1024, 0))
            self.facts['memfree_mb'] = int(round(int(self.parse_memfree(data)) / 1024, 0))

    def parse_memtotal(self, data):
        match = re.search(r' Total DRAM \(KB\): (\d+)', data, re.M)
        if match:
            return match.group(1)
        # Handle unique formatting for VM
        match = re.search(r' Total \s+\(KB\): (\d+)', data, re.M)
        if match:
            return match.group(1)

    def parse_memfree(self, data):
        match = re.search(r' Free\s+\(KB\): (\d+)', data, re.M)
        if match:
            return match.group(1)


class Config(FactsBase):

    COMMANDS = ['show configuration detail']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'show switch',
        {'command': 'show port config', 'output': 'json'},
        {'command': 'show port description', 'output': 'json'},
        {'command': 'show vlan detail', 'output': 'json'},
        {'command': 'show lldp neighbors', 'output': 'json'}
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        if data:
            sysmac = self.parse_sysmac(data)

        data = self.responses[1]
        if data:
            self.facts['interfaces'] = self.populate_interfaces(data, sysmac)

        data = self.responses[2]
        if data:
            self.populate_interface_descriptions(data)

        data = self.responses[3]
        if data:
            self.populate_vlan_interfaces(data, sysmac)

        data = self.responses[4]
        if data:
            self.facts['neighbors'] = self.parse_neighbors(data)

    def parse_sysmac(self, data):
        match = re.search(r'System MAC:\s+(\S+)', data, re.M)
        if match:
            return match.group(1)

    def populate_interfaces(self, interfaces, sysmac):
        facts = dict()
        for elem in interfaces:
            intf = dict()

            if 'show_ports_config' not in elem:
                continue

            key = str(elem['show_ports_config']['port'])

            if elem['show_ports_config']['linkState'] == 2:
                # Link state is "not present", don't include
                continue

            intf['type'] = 'Ethernet'
            intf['macaddress'] = sysmac
            intf['bandwidth_configured'] = str(elem['show_ports_config']['speedCfg'])
            intf['bandwidth'] = str(elem['show_ports_config']['speedActual'])
            intf['duplex_configured'] = elem['show_ports_config']['duplexCfg']
            intf['duplex'] = elem['show_ports_config']['duplexActual']
            if elem['show_ports_config']['linkState'] == 1:
                intf['lineprotocol'] = 'up'
            else:
                intf['lineprotocol'] = 'down'
            if elem['show_ports_config']['portState'] == 1:
                intf['operstatus'] = 'up'
            else:
                intf['operstatus'] = 'admin down'

            facts[key] = intf
        return facts

    def populate_interface_descriptions(self, data):
        for elem in data:
            if 'show_ports_description' not in elem:
                continue
            key = str(elem['show_ports_description']['port'])

            if 'descriptionString' in elem['show_ports_description']:
                desc = elem['show_ports_description']['descriptionString']
                self.facts['interfaces'][key]['description'] = desc

    def populate_vlan_interfaces(self, data, sysmac):
        for elem in data:
            if 'vlanProc' in elem:
                key = elem['vlanProc']['name1']
                if key not in self.facts['interfaces']:
                    intf = dict()
                    intf['type'] = 'VLAN'
                    intf['macaddress'] = sysmac
                    self.facts['interfaces'][key] = intf

                if elem['vlanProc']['ipAddress'] != '0.0.0.0':
                    self.facts['interfaces'][key]['ipv4'] = list()
                    addr = elem['vlanProc']['ipAddress']
                    subnet = elem['vlanProc']['maskForDisplay']
                    ipv4 = dict(address=addr, subnet=subnet)
                    self.add_ip_address(addr, 'ipv4')
                    self.facts['interfaces'][key]['ipv4'].append(ipv4)

            if 'rtifIpv6Address' in elem:
                key = elem['rtifIpv6Address']['rtifName']
                if key not in self.facts['interfaces']:
                    intf = dict()
                    intf['type'] = 'VLAN'
                    intf['macaddress'] = sysmac
                    self.facts['interfaces'][key] = intf
                self.facts['interfaces'][key]['ipv6'] = list()
                addr, subnet = elem['rtifIpv6Address']['ipv6_address_mask'].split('/')
                ipv6 = dict(address=addr, subnet=subnet)
                self.add_ip_address(addr, 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            if address not in self.facts['all_ipv4_addresses']:
                self.facts['all_ipv4_addresses'].append(address)
        else:
            if address not in self.facts['all_ipv6_addresses']:
                self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, data):
        facts = dict()
        for elem in data:
            if 'lldpPortNbrInfoShort' not in elem:
                continue
            intf = str(elem['lldpPortNbrInfoShort']['port'])
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = elem['lldpPortNbrInfoShort']['nbrSysName']
            fact['port'] = str(elem['lldpPortNbrInfoShort']['nbrPortID'])
            facts[intf].append(fact)
        return facts
