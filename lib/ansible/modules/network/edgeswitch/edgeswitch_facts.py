#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: edgeswitch_facts
version_added: "2.8"
author: "Frederic Bor (@f-bor)"
short_description: Collect facts from remote devices running Edgeswitch
description:
  - Collects a base set of device facts from a remote device that
    is running Ubiquiti Edgeswitch.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against Edgeswitch 1.7.4
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- edgeswitch_facts:
    gather_subset: all

# Collect only the config and default facts
- edgeswitch_facts:
    gather_subset:
      - config

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

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: str

# interfaces
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
"""
import re

from ansible.module_utils.network.edgeswitch.edgeswitch import run_commands
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

    COMMANDS = ['show version', 'show sysinfo']

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['hostname'] = self.parse_hostname(self.responses[1])

    def parse_version(self, data):
        match = re.search(r'Software Version\.+ (.*)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'System Name\.+ (.*)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Machine Model\.+ (.*)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number\.+ (.*)', data)
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
        'show interfaces description',
        'show interfaces status all'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        interfaces = {}

        data = self.responses[0]
        self.parse_interfaces_description(data, interfaces)

        data = self.responses[1]
        self.parse_interfaces_status(data, interfaces)

        self.facts['interfaces'] = interfaces

    def parse_interfaces_description(self, data, interfaces):
        for line in data.split('\n'):
            match = re.match(r'(\d\/\d+)\s+(\w+)\s+(\w+)', line)
            if match:
                name = match.group(1)
                interface = {}
                interface['operstatus'] = match.group(2)
                interface['lineprotocol'] = match.group(3)
                interface['description'] = line[30:]
                interfaces[name] = interface

    def parse_interfaces_status(self, data, interfaces):
        for line in data.split('\n'):
            match = re.match(r'(\d\/\d+)', line)
            if match:
                name = match.group(1)
                interface = interfaces[name]
                interface['physicalstatus'] = line[61:71].strip()
                interface['mediatype'] = line[73:91].strip()


FACT_SUBSETS = dict(
    default=Default,
    config=Config,
    interfaces=Interfaces,
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

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
