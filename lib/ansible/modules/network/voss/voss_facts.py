#!/usr/bin/python
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
module: voss_facts
version_added: "2.7"
author: "Lindsay Hill (@LindsayHill)"
short_description: Collect facts from remote devices running Extreme VOSS
description:
  - Collects a base set of device facts from a remote device that
    is running VOSS. This module prepends all of the base network fact
    keys with C(ansible_net_<fact>). The facts module will always collect
    a base set of facts from the device and can enable or disable
    collection of additional facts.
notes:
  - Tested against VOSS 7.0.0
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
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- voss_facts:
    gather_subset: all

# Collect only the config and default facts
- voss_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- voss_facts:
    gather_subset:
      - "!hardware"
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
  description: All IPv6 addresses configured on the device
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

from ansible.module_utils.network.voss.voss import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = ['show sys-info']

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'SysDescr\s+: \S+ \((\S+)\)', data)
        if match:
            return match.group(1)
        return ''

    def parse_hostname(self, data):
        match = re.search(r'SysName\s+: (\S+)', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_model(self, data):
        match = re.search(r'Chassis\s+: (\S+)', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_serialnum(self, data):
        match = re.search(r'Serial#\s+: (\S+)', data)
        if match:
            return match.group(1)
        return ''


class Hardware(FactsBase):

    COMMANDS = [
        'show khi performance memory'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]

        if data:
            match = re.search(r'Free:\s+(\d+)\s+\(KB\)', data, re.M)
            if match:
                self.facts['memfree_mb'] = int(round(int(match.group(1)) / 1024, 0))
            match = re.search(r'Used:\s+(\d+)\s+\(KB\)', data, re.M)
            if match:
                memused_mb = int(round(int(match.group(1)) / 1024, 0))
                self.facts['memtotal_mb'] = self.facts.get('memfree_mb', 0) + memused_mb


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'show interfaces gigabitEthernet interface',
        'show interfaces gigabitEthernet name',
        'show ip interface',
        'show ipv6 address interface',
        'show lldp neighbor | include Port|SysName'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces_eth(interfaces)

        data = self.responses[1]
        if data:
            data = self.parse_interfaces(data)
            self.populate_interfaces_eth_additional(data)

        data = self.responses[2]
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv4_interfaces(data)

        data = self.responses[3]
        if data:
            self.populate_ipv6_interfaces(data)

        data = self.responses[4]
        if data:
            self.facts['neighbors'] = self.parse_neighbors(data)

    def populate_interfaces_eth(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            match = re.match(r'^\d+\s+(\S+)\s+\w+\s+\w+\s+(\d+)\s+([a-f\d:]+)\s+(\w+)\s+(\w+)$', value)
            if match:
                intf['mediatype'] = match.group(1)
                intf['mtu'] = match.group(2)
                intf['macaddress'] = match.group(3)
                intf['adminstatus'] = match.group(4)
                intf['operstatus'] = match.group(5)
                intf['type'] = 'Ethernet'
            facts[key] = intf
        return facts

    def populate_interfaces_eth_additional(self, interfaces):
        for key, value in iteritems(interfaces):
            # This matches when no description is set
            match = re.match(r'^\w+\s+\w+\s+(\w+)\s+(\d+)\s+\w+$', value)
            if match:
                self.facts['interfaces'][key]['description'] = ''
                self.facts['interfaces'][key]['duplex'] = match.group(1)
                self.facts['interfaces'][key]['bandwidth'] = match.group(2)
            else:
                # This matches when a description is set
                match = re.match(r'^(.+)\s+\w+\s+\w+\s+(\w+)\s+(\d+)\s+\w+$', value)
                if match:
                    self.facts['interfaces'][key]['description'] = match.group(1).strip()
                    self.facts['interfaces'][key]['duplex'] = match.group(2)
                    self.facts['interfaces'][key]['bandwidth'] = match.group(3)

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            if key not in self.facts['interfaces']:
                if re.match(r'Vlan\d+', key):
                    self.facts['interfaces'][key] = dict()
                    self.facts['interfaces'][key]['type'] = 'VLAN'
                elif re.match(r'Clip\d+', key):
                    self.facts['interfaces'][key] = dict()
                    self.facts['interfaces'][key]['type'] = 'Loopback'
            if re.match(r'Port(\d+/\d+)', key):
                key = re.split('Port', key)[1]
            self.facts['interfaces'][key]['ipv4'] = list()
            match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', value, re.M)
            if match:
                addr = match.group(1)
                subnet = match.group(2)
                ipv4 = dict(address=addr, subnet=subnet)
                self.add_ip_address(addr, 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    def populate_ipv6_interfaces(self, data):
        addresses = re.split(r'-{3,}', data)[1].lstrip()
        for line in addresses.split('\n'):
            if not line:
                break

            match = re.match(r'^([\da-f:]+)/(\d+)\s+([CV])-(\d+)\s+.+$', line)
            if match:
                address = match.group(1)
                subnet = match.group(2)
                interface_short_name = match.group(3)
                interface_id = match.group(4)
                if interface_short_name == 'C':
                    intf_type = 'Loopback'
                    interface_name = 'Clip' + interface_id
                elif interface_short_name == 'V':
                    intf_type = 'VLAN'
                    interface_name = 'Vlan' + interface_id
                else:
                    # Unknown interface type, better to gracefully ignore it for now
                    break
                ipv6 = dict(address=address, subnet=subnet)
                self.add_ip_address(address, 'ipv6')
                try:
                    self.facts['interfaces'][interface_name].setdefault('ipv6', []).append(ipv6)
                    self.facts['interfaces'][interface_name]['type'] = intf_type
                except KeyError:
                    self.facts['interfaces'][interface_name] = dict()
                    self.facts['interfaces'][interface_name]['type'] = intf_type
                    self.facts['interfaces'][interface_name].setdefault('ipv6', []).append(ipv6)
            else:
                break

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        lines = neighbors.split('Port: ')
        if not lines:
            return facts
        for line in lines:
            match = re.search(r'^(\w.*?)\s+Index.*IfName\s+(\w.*)$\s+SysName\s+:\s(\S+)', line, (re.M | re.S))
            if match:
                intf = match.group(1)
                if intf not in facts:
                    facts[intf] = list()
                fact = dict()
                fact['host'] = match.group(3)
                fact['port'] = match.group(2)
                facts[intf].append(fact)
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        interfaces = re.split(r'-{3,}', data)[1].lstrip()
        for line in interfaces.split('\n'):
            if not line or re.match('^All', line):
                break
            else:
                match = re.split(r'^(\S+)\s+', line)
                key = match[1]
                parsed[key] = match[2].strip()
        return parsed

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is (?:.*), address is (\S+)', data)
        if match:
            return match.group(1)
        return ''

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))
        return ''

    def parse_bandwidth(self, data):
        match = re.search(r'BW (\d+)', data)
        if match:
            return int(match.group(1))
        return ''

    def parse_duplex(self, data):
        match = re.search(r'(\w+) Duplex', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_mediatype(self, data):
        match = re.search(r'media type is (.+)$', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (.+)$', data, re.M)
        if match:
            return match.group(1)
        return ''

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)
        return ''


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
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
