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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
---
module: ce_facts
version_added: "2.3"
author: "JackyGao2016 (@CloudEngine-Ansible)"
short_description: Gets facts about HUAWEI CloudEngine switches
description:
  - Collects facts from CloudEngine devices running the CloudEngine
    operating system.  Fact collection is supported over Cli
    transport.  This module prepends all of the base network fact keys
    with C(ansible_net_<fact>).  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
extends_documentation_fragment: cloudengine

options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a
        list of values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

- ce_facts:
    gather_subset: all

# Collect only the config facts
- ce_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- ce_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
BIOS Version:
  description: The BIOS version running on the remote device
  returned: always
  type: str
Board Type:
  description: The board type of the remote device
  returned: always
  type: str
CPLD1 Version:
  description: The CPLD1 Version running the remote device
  returned: always
  type: str
CPLD2 Version:
  description: The CPLD2 Version running the remote device
  returned: always
  type: str
MAB Version:
  description: The MAB Version running the remote device
  returned: always
  type: str
PCB Version:
  description: The PCB Version running the remote device
  returned: always
  type: str
hostname:
  description: The hostname of the remote device
  returned: always
  type: str

# hardware
FAN:
  description: The fan state on the device
  returned: when hardware is configured
  type: str
PWR:
  description: The power state on the device
  returned: when hardware is configured
  type: str
filesystems:
  description: The filesystems on the device
  returned: when hardware is configured
  type: str
flash_free:
  description: The flash free space on the device
  returned: when hardware is configured
  type: str
flash_total:
  description: The flash total space on the device
  returned: when hardware is configured
  type: str
memory_free:
  description: The memory free space on the remote device
  returned: when hardware is configured
  type: str
memory_total:
  description: The memory total space on the remote device
  returned: when hardware is configured
  type: str

# config
config:
  description: The current system configuration on the device
  returned: when config is configured
  type: str

# interfaces
all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""

import re
import ansible.module_utils.cloudengine
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcli import CommandRunner, AddCommandError
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.six import iteritems


def add_command(runner, command, output=None):
    """ Add command operation """

    try:
        runner.add_command(command, output)
    except AddCommandError:
        # AddCommandError is raised for any issue adding a command to
        # the runner.  Silently ignore the exception in this case
        raise AddCommandError


def transform_dict(data, keymap):
    """ Get transform dict """

    transform = dict()
    for key, fact in keymap:
        if key in data:
            transform[fact] = data[key]
    return transform


def transform_iterable(iterable, keymap):
    """ Transform iterable """

    for item in iterable:
        yield transform_dict(item, keymap)


class FactsBase(object):
    """ Class FactsBase """

    def __init__(self, module, runner):
        self.ipv4 = False
        self.lldp_enabled = False
        self.module = module
        self.runner = runner
        self.facts = dict()
        self.commands()

    def commands(self):
        """ Commands method """

        raise NotImplementedError


class Default(FactsBase):
    """ Class default """

    def commands(self):
        """ Commands method """

        add_command(self.runner, 'display version')
        add_command(self.runner, 'display current-configuration | include sysname')

    def populate(self):
        """ Populate method """

        data = self.runner.get_command('display version')
        if data:
            version = data.split("\n")
            tmp_version = version[11:]
            for item in tmp_version:
                tmp_item = item.split()
                tmp_key = tmp_item[1] + " " + tmp_item[2]
                self.facts[tmp_key] = tmp_item[4]

        data = self.runner.get_command('display current-configuration | include sysname')
        if data:
            tmp_value = re.findall(r'sysname (.*)', data)
            self.facts['hostname'] = tmp_value[0]


class Config(FactsBase):
    """ Class config """

    def commands(self):
        """ Commands method """

        add_command(self.runner,
                    'display current-configuration configuration system')

    def populate(self):
        """ Populate method """

        data = self.runner.get_command(
            'display current-configuration configuration system')
        if data:
            self.facts['config'] = data.split("\n")


class Hardware(FactsBase):
    """ Class hardware """

    def commands(self):
        """ Commands method """

        add_command(self.runner, 'dir')
        add_command(self.runner, 'display memory')
        add_command(self.runner, 'display device')

    def populate(self):
        """ Populate method """

        data = self.runner.get_command('dir')
        if data:
            self.facts['filesystems'] = re.findall(r'^Directory of (.*)/', data)[0]
            self.facts['flash_total'] = re.findall(r'(.*) total', data)[0].replace(",", "")
            self.facts['flash_free'] = re.findall(r'total \((.*) free\)', data)[0].replace(",", "")

        data = self.runner.get_command('display memory')
        if data:
            memory_total = re.findall(r'Total Memory Used: (.*) Kbytes', data)[0]
            use_percent = re.findall(r'Memory Using Percentage: (.*)%', data)[0]
            memory_free = str(int(memory_total) - int(memory_total) * int(use_percent) / 100)
            self.facts['memory_total'] = memory_total + " Kb"
            self.facts['memory_free'] = memory_free + " Kb"

        data = self.runner.get_command('display device')
        if data:
            device_info = data.split("\n")
            tmp_device_info = device_info[4:-1]
            for item in tmp_device_info:
                tmp_item = item.split()
                if len(tmp_item) == 8:
                    self.facts[tmp_item[2]] = tmp_item[6]
                elif len(tmp_item) == 7:
                    self.facts[tmp_item[0]] = tmp_item[5]


class Interfaces(FactsBase):
    """ Class interfaces """

    def commands(self):
        """ Commands method """

        add_command(self.runner, 'display interface brief')

        try:
            add_command(self.runner, 'display ip interface brief')
            self.ipv4 = True
        except NetworkError:
            self.ipv4 = False

        try:
            add_command(self.runner, 'display lldp neighbor brief')
            self.lldp_enabled = True
        except NetworkError:
            self.lldp_enabled = False

    def populate(self):
        """ Populate method"""

        interface_dict = dict()
        ipv4_addr_dict = dict()
        neighbors_dict = dict()

        data = self.runner.get_command('display interface brief')
        if data:
            interface_info = data.split("\n")
            tmp_interface = interface_info[12:]
            for item in tmp_interface:
                tmp_item = item.split()
                interface_dict[tmp_item[0]] = tmp_item[1]
            self.facts['interfaces'] = interface_dict

        if self.ipv4:
            data = self.runner.get_command('display ip interface brief')
            if data:
                ipv4_addr = data.split("\n")
                tmp_ipv4 = ipv4_addr[11:]
                for item in tmp_ipv4:
                    tmp_item = item.split()
                    ipv4_addr_dict[tmp_item[0]] = tmp_item[1]
                self.facts['all_ipv4_addresses'] = ipv4_addr_dict

        if self.lldp_enabled:
            data = self.runner.get_command('display lldp neighbor brief')
            if data:
                neighbors = data.split("\n")
                tmp_neighbors = neighbors[2:]
                for item in tmp_neighbors:
                    tmp_item = item.split()
                    neighbors_dict[tmp_item[0]] = tmp_item[3]
                self.facts['neighbors'] = neighbors_dict


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ Module main """

    spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    module = NetworkModule(argument_spec=spec, supports_check_mode=True)

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

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    runner = CommandRunner(module)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module, runner))

    try:
        runner.run()
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    try:
        for inst in instances:
            inst.populate()
            facts.update(inst.facts)
    except Exception:
        raise

    ansible_facts = dict()
    for key, value in iteritems(facts):
        if key.startswith('_'):
            ansible_facts[key[1:]] = value
        else:
            ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
