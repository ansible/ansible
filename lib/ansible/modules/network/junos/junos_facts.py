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
from __future__ import division

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'core',
    'version': '1.0',
}

DOCUMENTATION = """
---
module: junos_facts
version_added: "2.1"
author: "Nathaniel Case (@qalthos)"
short_description: Collect facts from remote devices running Junos
description:
  - Collects fact information from a remote device running the Junos
    operating system.  By default, the module will collect basic fact
    information from the device to be included with the hostvars.
    Additional fact information can be collected based on the
    configured set of arguments.
extends_documentation_fragment: junos
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
    default: "!config"
"""

EXAMPLES = """
- name: collect default set of facts
  junos_facts:

- name: collect default set of facts and configuration
  junos_facts:
    gather_subset: config
"""

RETURN = """
ansible_facts:
  description: Returns the facts collect from the device
  returned: always
  type: dict
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.junos import get_config, run_commands
from ansible.module_utils.junos import junos_argument_spec, check_args


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS))


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show chassis hardware',
    ]

    def populate(self):
        super(Default, self).populate()

        version = self.responses[0]
        self.facts['hostname'] = self.parse_hostname(version)
        self.facts['version'] = self.parse_version(version)
        self.facts['model'] = self.parse_model(version)

        hardware = self.responses[1]
        self.facts['serialnum'] = self.parse_serialnum(hardware)

    def parse_hostname(self, data):
        match = re.search(r'Hostname:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_version(self, data):
        match = re.search(r'Junos:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Model:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Chassis\s+(\w+)', data)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show system memory',
        'show system storage',
    ]

    def populate(self):
        super(Hardware, self).populate()
        memory = self.responses[0]
        self.facts['memfree_mb'] = self.parse_memfree(memory)
        self.facts['memtotal_mb'] = self.parse_memtotal(memory)
        self.facts['filesystems'] = self.parse_filesystems(self.responses[1])

    def parse_memtotal(self, data):
        match = re.search(r'Total memory:\s+(\d+)', data)
        if match:
            return int(match.group(1)) // 1024

    def parse_memfree(self, data):
        match = re.search(r'Free memory:\s+(\d+)', data)
        if match:
            return int(match.group(1)) // 1024

    def parse_filesystems(self, data):
        paths = []
        for line in data.split('\n'):
            path = line.split()[-1]
            if path.startswith('/'):
                paths.append(path)

        return paths


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=None,
    interfaces=Interfaces,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ Main entry point for AnsibleModule
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list'),
        config_format=dict(default='text', choices=['xml', 'text']),
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

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
            module.fail_json(msg='Subset must be one of [%s], got %s' %
                             (', '.join(VALID_SUBSETS), subset))

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

    if 'config' in runable_subsets:
        facts['config'] = get_config(module)
        runable_subsets.remove('config')

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

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
