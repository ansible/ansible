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
module: slxos_facts
version_added: "2.6"
author: "Lindsay Hill (@LindsayHill)"
short_description: Collect facts from devices running Extreme SLX-OS
description:
  - Collects a base set of device facts from a remote device that
    is running SLX-OS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against SLX-OS 17s.1.02
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
# Collect all facts from the device
- slxos_facts:
    gather_subset: all

# Collect only the config and default facts
- slxos_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- slxos_facts:
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
  type: string

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

from ansible.module_utils.network.slxos.slxos import run_commands
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
        'show inventory chassis',
        r'show running-config | include host\-name'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)

        data = self.responses[1]
        if data:
            self.facts['model'] = self.parse_model(data)
            self.facts['serialnum'] = self.parse_serialnum(data)

        data = self.responses[2]
        if data:
            self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'SLX-OS Operating System Version: (\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'SID:(\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'switch-attributes host-name (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'SN:(\S+)', data, re.M)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show process memory summary'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['memtotal_mb'] = int(round(int(self.parse_memtotal(data)) / 1024, 0))
            self.facts['memfree_mb'] = int(round(int(self.parse_memfree(data)) / 1024, 0))

    def parse_memtotal(self, data):
        match = re.search(r'Total\s*Memory: (\d+)\s', data, re.M)
        if match:
            return match.group(1)

    def parse_memfree(self, data):
        match = re.search(r'Total Free: (\d+)\s', data, re.M)
        if match:
            return match.group(1)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'show interface',
        'show ipv6 interface brief',
        r'show lldp nei detail | inc ^Local\ Interface|^Remote\ Interface|^System\ Name'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)
            self.populate_ipv4_interfaces(interfaces)

        data = self.responses[1]
        if data:
            self.populate_ipv6_interfaces(data)

        data = self.responses[2]
        if data:
            self.facts['neighbors'] = self.parse_neighbors(data)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = list()
            primary_address = addresses = []
            primary_address = re.findall(r'Primary Internet Address is (\S+)', value, re.M)
            addresses = re.findall(r'Secondary Internet Address is (\S+)', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    # Only gets primary IPv6 addresses
    def populate_ipv6_interfaces(self, data):
        interfaces = re.split('=+', data)[1].strip()
        matches = re.findall(r'(\S+ \S+) +[\w-]+.+\s+([\w:/]+/\d+)', interfaces, re.M)
        for match in matches:
            interface = match[0]
            self.facts['interfaces'][interface]['ipv6'] = list()
            address, masklen = match[1].split('/')
            ipv6 = dict(address=address, masklen=int(masklen))
            self.add_ip_address(ipv6['address'], 'ipv6')
            self.facts['interfaces'][interface]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        lines = neighbors.split('Local Interface: ')
        if len(lines) == 0:
            return facts
        for line in lines:
            match = re.search(r'(\w+ \S+)\s+\(Local Int.+?\)[\s\S]+Remote Interface: (\S+.+?) \(Remote Int.+?\)[\s\S]+System Name: (\S+)', line, re.M)
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
        for interface in data.split('\n\n'):
            match = re.match(r'^(\S+ \S+)', interface, re.M)
            if not match:
                continue
            else:
                parsed[match.group(1)] = interface
        return parsed

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is Ethernet, address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Primary Internet Address is ([^\s,]+)', data)
        if match:
            addr, masklen = match.group(1).split('/')
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+) bytes', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'LineSpeed Actual\s+:\s(.+)', data)
        if match:
            return match.group(1)

    def parse_duplex(self, data):
        match = re.search(r'Duplex: (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.match(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)


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

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
