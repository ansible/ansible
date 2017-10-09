#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Lenovo, Inc.
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
# Module to Collect facts from Lenovo Switches running lenovo ENOS commands
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: enos_facts
version_added: "2.5"
author: "Anil Kumar Muraleedharan (Anil)"
short_description: Collect facts from remote devices running Lenovo ENOS
description:
  - Collects a base set of device facts from a remote Lenovo device
    running on ENOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: enos_facts
notes:
  - Tested against ENOS 8.4.1.68
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
'''
EXAMPLES = '''

Tasks: The following are examples of using the module enos_facts.
These are written in the main.yml file of the tasks directory.
---
- name: Test Enos Facts
  enos_facts: provider={{ cli }}
  with_items: "{{enos_facts_data}}"

vars:
cli:
  host: "{{ inventory_hostname }}"
  port: 22
  username: admin
  password: admin
  transport: cli
  timeout: 30
  authorize: True
  auth_pass:

---
# Collect all facts from the device
- enos_facts:
    gather_subset: all
    provider: "{{ cli }}"
    with_items: "{{enos_facts_data}}"

# Collect only the config and default facts
- enos_facts:
    gather_subset:
      - config
    provider: "{{ cli }}"
    with_items: "{{enos_facts_data}}"

# Do not collect hardware facts
- enos_facts:
    gather_subset:
      - "!hardware"
    provider: "{{ cli }}"
    with_items: "{{enos_facts_data}}"

'''
RETURN = '''
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
# default
ansible_net_model:
  description: The model name returned from the Lenovo ENOS device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the Lenovo ENOS device
  returned: always
  type: str
ansible_net_version:
  description: The ENOS operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: string
ansible_net_image:
  description: Indicates the active image for the device
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
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system.
    This gives information on description, mac address, mtu, speed,
    duplex and operstatus
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
'''

import re

from enos import run_commands, enos_argument_spec, check_args
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None
        self.PERSISTENT_COMMAND_TIMEOUT = 60

    def populate(self):
        self.responses = run_commands(self.module, self.COMMANDS,
                                      check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = ['show version', 'show run']

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        data_run = self.responses[1]
        # file = open('Anil.txt', "a")
        # file.write(data_run)
        # file.close()
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
        if data_run:
            self.facts['hostname'] = self.parse_hostname(data_run)

    def parse_version(self, data):
        match = re.search(r'^Software Version (.*?) ', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_hostname(self, data_run):
        for line in data_run.split('\n'):
            line = line.strip()
            match = re.match(r'hostname (.*?)', line, re.M | re.I)
            if match:
                hosts = line.split()
                hostname = hosts[1].strip('\"')
                return hostname
        else:
            return "NA"

    def parse_model(self, data):
        # match = re.search(r'^Cisco (.+) \(revision', data, re.M)
        match = re.search(r'^Lenovo RackSwitch (\S+)', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'(.*) image1(.*)', data, re.M | re.I)
        if match:
            return "Image1"
        else:
            return "Image2"

    def parse_serialnum(self, data):
        # match = re.search(r'board ID (\S+)', data)
        match = re.search(r'^Switch Serial No:  (\S+)', data, re.M | re.I)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show system memory'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        # file = open('Sunil.txt', "a")
        # file.write(data)
        # file.close()
        if data:
            self.facts['memtotal_mb'] = self.parse_memtotal(data)
            self.facts['memfree_mb'] = self.parse_memfree(data)

    def parse_memtotal(self, data):
        match = re.search(r'^MemTotal:\s*(.*) kB', data, re.M | re.I)
        if match:
            return int(match.group(1))/1024

    def parse_memfree(self, data):
        match = re.search(r'^MemFree:\s*(.*) kB', data, re.M | re.I)
        if match:
            return int(match.group(1))/1024

        # if data:
        #    self.facts['filesystems'] = self.parse_filesystems(data)

    # def parse_filesystems(self, data):
        # return re.findall(r'^Directory of (\S+)/', data, re.M)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = ['show interface status']

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data1 = self.responses[0]
        data2 = self.run(['show lldp port \r\n'])
        data2 = to_text(data2, errors='surrogate_or_strict').strip()
        data2 = data2.replace(r"\n", "\n")
        lines1 = None
        lines2 = None
        if data1:
            lines1 = self.parse_interfaces(data1)
        if data2:
            lines2 = self.parse_interfaces(data2)
        if lines1 is not None and lines2 is not None:
            if len(lines1) == len(lines2):
                self.facts['interfaces'] = self.populate_interfaces(lines1,
                                                                    lines2)

        data3 = self.run(['show lldp remote-device port \r\n'])
        data3 = to_text(data3, errors='surrogate_or_strict').strip()
        data3 = data3.replace(r"\n", "\n")

        lines3 = None
        if data3:
            lines3 = self.parse_neighbors(data3)
        # file = open('Data3.txt', "a")
        # file.write(str(line3))
        # file.close()
        if lines3 is not None:
            self.facts['neighbors'] = self.populate_neighbors(lines3)

        data4 = self.run(['show interface ip \r\n'])
        data4 = data4[0].split('\n')
        # data4= to_text(data4, errors='surrogate_or_strict').strip()
        # data4 = data4.replace(r"\n", "\n")
        lines4 = None
        if data4:
            lines4 = self.parse_ipaddresses(data4)
            # for line in lines4:
            #    file = open('Data4.txt', "a")
            #    file.write(line)
            #    file.close()
            ipv4_interfaces = self.populate_ipv4_interfaces(lines4)
            self.facts['all_ipv4_addresses'] = ipv4_interfaces
            ipv6_interfaces = self.populate_ipv6_interfaces(lines4)
            self.facts['all_ipv6_addresses'] = ipv6_interfaces

    # Anil
    def parse_ipaddresses(self, data4):
        parsed = list()
        for line in data4:
            # file = open('data4.txt', "a")
            if len(line) == 0:
                continue
            else:
                line = line.strip()
                if len(line) == 0:
                    continue
                # file.write(line)
                match = re.search(r'IP4', line, re.M | re.I)
                if match:
                    key = match.group()
                    parsed.append(line)
                match = re.search(r'IP6', line, re.M | re.I)
                if match:
                    key = match.group()
                    parsed.append(line)
            # file.close()
        return parsed

    # Anil
    def set_ipv4_interfaces(self, line4):
        ipv4_addresses = list()
        for line in line4:
            ipv4Split = line.split()
            # file = open('Data4.txt', "a")
            # file.write(str(ipv4Split))
            # file.close()
            if ipv4Split[1] == "IP4":
                ipv4_addresses.append(ipv4Split[2])
        return ipv4_addresses

    # Anil
    def populate_ipv6_interfaces(self, line4):
        ipv6_addresses = list()
        for line in line4:
            ipv6Split = line.split()
            if ipv6Split[1] == "IP6":
                ipv6_addresses.append(ipv6Split[2])
        return ipv6_addresses

    # Anil
    def populate_neighbors(self, lines3):
        neighbors = dict()
        for line in lines3:
            neighborSplit = line.split("|")
            innerData = dict()
            innerData['Remote Chassis ID'] = neighborSplit[2].strip()
            innerData['Remote Port'] = neighborSplit[3].strip()
            sysName = neighborSplit[4].strip()
            if sysName is not None:
                innerData['Remote System Name'] = neighborSplit[4].strip()
            else:
                innerData['Remote System Name'] = "NA"
            neighbors[neighborSplit[0].strip()] = innerData
        return neighbors

    # Anil
    def populate_interfaces(self, lines1, lines2):
        interfaces = dict()
        for line1, line2 in zip(lines1, lines2):
            line = line1 + "  " + line2
            intfSplit = line.split()
            innerData = dict()
            innerData['description'] = intfSplit[6].strip()
            innerData['macaddress'] = intfSplit[8].strip()
            innerData['mtu'] = intfSplit[9].strip()
            innerData['speed'] = intfSplit[1].strip()
            innerData['duplex'] = intfSplit[2].strip()
            innerData['operstatus'] = intfSplit[5].strip()
            interfaces[intfSplit[0].strip()] = innerData
    return interfaces

    # Anil
    def parse_neighbors(self, neighbors):
        parsed = list()
        for line in neighbors.split('\n'):
            if len(line) == 0:
                continue
            else:
                line = line.strip()
                match = re.match(r'^([0-9]+)', line)
                if match:
                    key = match.group(1)
                    parsed.append(line)
                match = re.match(r'^(MGT+)', line)
                if match:
                    key = match.group(1)
                    parsed.append(line)
        return parsed

    # Anil
    def parse_interfaces(self, data):
        parsed = list()
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            else:
                line = line.strip()
                match = re.match(r'^([0-9]+)', line)
                if match:
                    key = match.group(1)
                    parsed.append(line)
                match = re.match(r'^(MGT+)', line)
                if match:
                    key = match.group(1)
                    parsed.append(line)
        return parsed

FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

PERSISTENT_COMMAND_TIMEOUT = 60


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    argument_spec.update(enos_argument_spec)

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
    check_args(module, warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
