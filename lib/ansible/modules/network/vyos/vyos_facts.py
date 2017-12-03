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
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: vyos_facts
version_added: "2.2"
author: "Nathaniel Case (@qalthos)"
short_description: Collect facts from remote devices running VyOS
description:
  - Collects a base set of device facts from a remote device that
    is running VyOS.  This module prepends all of the
    base network fact keys with U(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: vyos
notes:
  - Tested against VYOS 1.1.7
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, default, config, and neighbors.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: "!config"
"""

EXAMPLES = """
- name: collect all facts from the device
  vyos_facts:
    gather_subset: all

- name: collect only the config and default facts
  vyos_facts:
    gather_subset: config

- name: collect everything exception the config
  vyos_facts:
    gather_subset: "!config"
"""

RETURN = """
ansible_net_config:
  description: The running-config from the device
  returned: when config is configured
  type: str
ansible_net_commits:
  description: The set of available configuration revisions
  returned: when present
  type: list
ansible_net_hostname:
  description: The configured system hostname
  returned: always
  type: str
ansible_net_model:
  description: The device model string
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the device
  returned: always
  type: str
ansible_net_version:
  description: The version of the software running
  returned: always
  type: str
ansible_net_neighbors:
  description: The set of LLDP neighbors
  returned: when interface is configured
  type: list
ansible_net_gather_subset:
  description: The list of subsets gathered by the module
  returned: always
  type: list
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.vyos import run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


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
        'show host name',
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]

        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)

        self.facts['hostname'] = self.responses[1]

    def parse_version(self, data):
        match = re.search(r'Version:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'HW model:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'HW S/N:\s+(\S+)', data)
        if match:
            return match.group(1)


class Config(FactsBase):

    COMMANDS = [
        'show configuration commands',
        'show system commit',
    ]

    def populate(self):
        super(Config, self).populate()

        self.facts['config'] = self.responses

        commits = self.responses[1]
        entries = list()
        entry = None

        for line in commits.split('\n'):
            match = re.match(r'(\d+)\s+(.+)by(.+)via(.+)', line)
            if match:
                if entry:
                    entries.append(entry)

                entry = dict(revision=match.group(1),
                             datetime=match.group(2),
                             by=str(match.group(3)).strip(),
                             via=str(match.group(4)).strip(),
                             comment=None)
            else:
                entry['comment'] = line.strip()

        self.facts['commits'] = entries


class Neighbors(FactsBase):

    COMMANDS = [
        'show lldp neighbors',
        'show lldp neighbors detail',
    ]

    def populate(self):
        super(Neighbors, self).populate()

        all_neighbors = self.responses[0]
        if 'LLDP not configured' not in all_neighbors:
            neighbors = self.parse(
                self.responses[1]
            )
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def parse(self, data):
        parsed = list()
        values = None
        for line in data.split('\n'):
            if not line:
                continue
            elif line[0] == ' ':
                values += '\n%s' % line
            elif line.startswith('Interface'):
                if values:
                    parsed.append(values)
                values = line
        if values:
            parsed.append(values)
        return parsed

    def parse_neighbors(self, data):
        facts = dict()
        for item in data:
            interface = self.parse_interface(item)
            host = self.parse_host(item)
            port = self.parse_port(item)
            if interface not in facts:
                facts[interface] = list()
            facts[interface].append(dict(host=host, port=port))
        return facts

    def parse_interface(self, data):
        match = re.search(r'^Interface:\s+(\S+),', data)
        return match.group(1)

    def parse_host(self, data):
        match = re.search(r'SysName:\s+(.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_port(self, data):
        match = re.search(r'PortDescr:\s+(.+)$', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    neighbors=Neighbors,
    config=Config
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    argument_spec.update(vyos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

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
