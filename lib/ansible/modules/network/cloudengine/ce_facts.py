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

DOCUMENTATION = """
---
module: ce_facts
version_added: "2.2"
author: "wangdezhuang (@CloudEngine-Ansible)"
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
        all, hardware, config, legacy, and interfaces.  Can specify a
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

# Collect only the config and default facts
- ce_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- ce_facts:
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
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: string

# hardware
ansible_net_filesystems:
  description: All file system names available on the device
  returned: when hardware is configured
  type: list
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

# legacy (pre Ansible 2.2)
fan_info:
  description: A hash of facts about fans in the remote device
  returned: when legacy is configured
  type: dict
hostname:
  description: The configured hostname of the remote device
  returned: when legacy is configured
  type: dict
interfaces_list:
  description: The list of interface names on the remote device
  returned: when legacy is configured
  type: dict
kickstart:
  description: The software version used to boot the system
  returned: when legacy is configured
  type: str
module:
  description: A hash of facts about the modules in a remote device
  returned: when legacy is configured
  type: dict
platform:
  description: The hardware platform reported by the remote device
  returned: when legacy is configured
  type: str
power_supply_info:
  description: A hash of facts about the power supplies in the remote device
  returned: when legacy is configured
  type: str
vlan_list:
  description: The list of VLAN IDs configured on the remote device
  returned: when legacy is configured
  type: list
"""
import re
import datetime
import ansible.module_utils.cloudengine
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcli import CommandRunner, AddCommandError
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.six import iteritems


def add_command(runner, command, output=None):
    """ add_command """

    try:
        runner.add_command(command, output)
    except AddCommandError:
        # AddCommandError is raised for any issue adding a command to
        # the runner.  Silently ignore the exception in this case
        raise AddCommandError


class FactsBase(object):
    """ FactsBase """

    def __init__(self, module, runner):
        self.module = module
        self.runner = runner
        self.facts = dict()
        self.commands()

    def commands(self):
        """ commands """

        raise NotImplementedError

    def transform_dict(self, data, keymap):
        """ transform_dict """

        transform = dict()
        for key, fact in keymap:
            if key in data:
                transform[fact] = data[key]
        return transform

    def transform_iterable(self, iterable, keymap):
        """ transform_iterable """

        for item in iterable:
            yield self.transform_dict(item, keymap)


class Default(FactsBase):
    """ Default """

    def commands(self):
        """ commands """

        add_command(self.runner, 'display version')

    def populate(self):
        """ populate """

        data = self.runner.get_command('display version')

        self.facts['version'] = data.split("\n")


class Config(FactsBase):
    """ Config """

    def commands(self):
        """ commands """

        add_command(self.runner,
                    'display current-configuration configuration system')

    def populate(self):
        """ populate """

        data = self.runner.get_command(
            'display current-configuration configuration system')
        self.facts['config'] = data.split("\n")


class Hardware(FactsBase):
    """ Hardware """

    def commands(self):
        """ commands """

        add_command(self.runner, 'dir')
        add_command(self.runner, 'display memory')

    def populate(self):
        """ populate """

        data = self.runner.get_command('dir', 'text')
        self.facts['filesystems'] = re.findall(
            r'^Directory of (.+)/', data, re.M)

        data = self.runner.get_command('display memory')
        temp_data = data.split(
            r"----------------------------")
        self.facts['memeory'] = temp_data[0].split("\n")


class Interfaces(FactsBase):
    """ Interfaces """

    def commands(self):
        """ commands """

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
        """ populate """

        self.facts['all_ipv4_addresses'] = list()

        data = self.runner.get_command('display interface brief')
        temp_data = data.split(
            r"InUti/OutUti: input utility rate/output utility rate")
        self.facts['interfaces'] = temp_data[1].split("\n")

        if self.ipv4:
            data = self.runner.get_command('display ip interface brief')
            if data:
                self.facts['all_ipv4_addresses'] = data.split("\n")

        if self.lldp_enabled:
            data = self.runner.get_command('display lldp neighbor brief')
            self.facts['neighbors'] = data.split("\n")


class Legacy(FactsBase):
    """ Legacy """

    def commands(self):
        """ commands """

        add_command(self.runner, 'display device')
        add_command(self.runner, 'display vlan summary')

    def populate(self):
        """ populate """

        data = self.runner.get_command('display device')
        self.facts['device'] = data.split("\n")

        data = self.runner.get_command('display vlan summary')
        self.facts['vlan'] = data.split("\n")


FACT_SUBSETS = dict(
    default=Default,
    legacy=Legacy,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ main """

    start_time = datetime.datetime.now()

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
            key = 'ansible_net_%s' % key
            ansible_facts[key] = value

    end_time = datetime.datetime.now()
    ansible_facts['execute_time'] = str(end_time - start_time)

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
