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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_facts
version_added: "2.4"
author: "wangdezhuang (@QijunPan)"
short_description: Gets facts about HUAWEI CloudEngine switches.
description:
  - Collects facts from CloudEngine devices running the CloudEngine
    operating system.  Fact collection is supported over Cli
    transport.  This module prepends all of the base network fact keys
    with C(ansible_net_<fact>).  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
notes:
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
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

- name: CloudEngine facts test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Gather_subset is all"
    ce_facts:
      gather_subset: all
      provider: "{{ cli }}"

  - name: "Collect only the config facts"
    ce_facts:
      gather_subset: config
      provider: "{{ cli }}"

  - name: "Do not collect hardware facts"
    ce_facts:
      gather_subset: "!hardware"
      provider: "{{ cli }}"
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

from ansible.module_utils.network.cloudengine.ce import run_commands
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS))


class Default(FactsBase):
    """ Class default """

    COMMANDS = [
        'display version',
        'display current-configuration | include sysname'
    ]

    def populate(self):
        """ Populate method """

        super(Default, self).populate()

        data = self.responses[0]
        if data:
            version = data.split("\n")
            for item in version:
                if re.findall(r"^\d+\S\s+", item.strip()):
                    tmp_item = item.split()
                    tmp_key = tmp_item[1] + " " + tmp_item[2]
                    if len(tmp_item) > 5:
                        self.facts[tmp_key] = " ".join(tmp_item[4:])
                    else:
                        self.facts[tmp_key] = tmp_item[4]

        data = self.responses[1]
        if data:
            tmp_value = re.findall(r'sysname (.*)', data)
            self.facts['hostname'] = tmp_value[0]


class Config(FactsBase):
    """ Class config """

    COMMANDS = [
        'display current-configuration configuration system'
    ]

    def populate(self):
        """ Populate method """

        super(Config, self).populate()

        data = self.responses[0]
        if data:
            self.facts['config'] = data.split("\n")


class Hardware(FactsBase):
    """ Class hardware """

    COMMANDS = [
        'dir',
        'display memory',
        'display device'
    ]

    def populate(self):
        """ Populate method """

        super(Hardware, self).populate()

        data = self.responses[0]
        if data:
            self.facts['filesystems'] = re.findall(r'Directory of (.*)/', data)[0]
            self.facts['flash_total'] = re.findall(r'(.*) total', data)[0].replace(",", "")
            self.facts['flash_free'] = re.findall(r'total \((.*) free\)', data)[0].replace(",", "")

        data = self.responses[1]
        if data:
            memory_total = re.findall(r'Total Memory Used: (.*) Kbytes', data)[0]
            use_percent = re.findall(r'Memory Using Percentage: (.*)%', data)[0]
            memory_free = str(int(memory_total) - int(memory_total) * int(use_percent) / 100)
            self.facts['memory_total'] = memory_total + " Kb"
            self.facts['memory_free'] = memory_free + " Kb"

        data = self.responses[2]
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

    COMMANDS = [
        'display interface brief',
        'display ip interface brief',
        'display lldp neighbor brief'
    ]

    def populate(self):
        """ Populate method"""

        interface_dict = dict()
        ipv4_addr_dict = dict()
        neighbors_dict = dict()

        super(Interfaces, self).populate()

        data = self.responses[0]
        begin = False
        if data:
            interface_info = data.split("\n")
            for item in interface_info:
                if begin:
                    tmp_item = item.split()
                    interface_dict[tmp_item[0]] = tmp_item[1]

                if re.findall(r"^Interface", item.strip()):
                    begin = True

            self.facts['interfaces'] = interface_dict

        data = self.responses[1]
        if data:
            ipv4_addr = data.split("\n")
            tmp_ipv4 = ipv4_addr[11:]
            for item in tmp_ipv4:
                tmp_item = item.split()
                ipv4_addr_dict[tmp_item[0]] = tmp_item[1]
            self.facts['all_ipv4_addresses'] = ipv4_addr_dict

        data = self.responses[2]
        if data:
            neighbors = data.split("\n")
            tmp_neighbors = neighbors[2:]
            for item in tmp_neighbors:
                tmp_item = item.split()
                if len(tmp_item) > 3:
                    neighbors_dict[tmp_item[0]] = tmp_item[3]
                else:
                    neighbors_dict[tmp_item[0]] = None
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

    spec.update(ce_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

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
        # this is to maintain capability with nxos_facts 2.1
        if key.startswith('_'):
            ansible_facts[key[1:]] = value
        else:
            ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
