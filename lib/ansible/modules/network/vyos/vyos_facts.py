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
module: vyos_facts
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Collect facts from remote devices running OS
description:
  - Collects a base set of device facts from a remote device that
    is running VyOS.  This module prepends all of the
    base network fact keys with U(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: vyos
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: vyos
    password: vyos
    transport: cli

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

import ansible.module_utils.vyos
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.netcli import CommandRunner
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    def __init__(self, runner):
        self.runner = runner
        self.facts = dict()

        self.commands()

    def commands(self):
        raise NotImplementedError


class Default(FactsBase):

    def commands(self):
        self.runner.add_command('show version')
        self.runner.add_command('show host name')

    def populate(self):
        data = self.runner.get_command('show version')

        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)

        self.facts['hostname'] = self.runner.get_command('show host name')

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

    def commands(self):
        self.runner.add_command('show configuration commands')
        self.runner.add_command('show system commit')

    def populate(self):

        config = self.runner.get_command('show configuration commands')
        self.facts['config'] = str(config).split('\n')

        commits = self.runner.get_command('show system commit')
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

    def commands(self):
        self.runner.add_command('show lldp neighbors')
        self.runner.add_command('show lldp neighbors detail')

    def populate(self):
        all_neighbors = self.runner.get_command('show lldp neighbors')
        if 'LLDP not configured' not in all_neighbors:
            neighbors = self.parse(
                self.runner.get_command('show lldp neighbors detail')
            )
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def parse(self, data):
        parsed = list()
        values = None
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                values += '\n%s' % line
            elif line.startswith('Interface'):
                if values:
                    parsed.append(values)
                values = line
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
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    runner = CommandRunner(module)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](runner))

    runner.run()

    try:
        for inst in instances:
            inst.populate()
            facts.update(inst.facts)
    except Exception:
        exc = get_exception()
        module.fail_json(msg='unknown failure', output=runner.items, exc=str(exc))

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
