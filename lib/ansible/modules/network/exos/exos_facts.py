#!/usr/bin/python
#
# (c) 2018 Extreme Networks Inc.
#
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
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: exos_facts
version_added: "2.7"
author: "Lance Richardson (@hlrichardson)"
short_description: Collect facts from devices running Extreme EXOS
description:
  - Collects a base set of device facts from a remote device that
    is running EXOS.  This module prepends all of the base network
    fact keys with C(ansible_net_<fact>).  The facts module will
    always collect a base set of facts from the device and can
    enable or disable collection of additional facts.
notes:
  - Tested against EXOS 22.5.1.7
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: ['!config']
"""

EXAMPLES = """
  - name: collect all facts from the device
    exos_facts:
      gather_subset: all

  - name: collect only the config and default facts
    exos_facts:
      gather_subset: config

  - name: do not collect hardware facts
    exos_facts:
      gather_subset: "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str

# hardware
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: str

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All Primary IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""
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


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=["!config"], type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset')

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    warnings = list()

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
