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
module: eos_facts
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Collect facts from remote devices running Arista EOS
description:
  - Collects a base set of device facts from a remote device that
    is running eos.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: eos
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

# Collect all facts from the device
- eos_facts:
    gather_subset: all
    provider: "{{ cli }}"

# Collect only the config and default facts
- eos_facts:
    gather_subset:
      - config
    provider: "{{ cli }}"

# Do not collect hardware facts
- eos_facts:
    gather_subset:
      - "!hardware"
    provider: "{{ cli }}"
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
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: str
ansible_net_fqdn:
  description: The fully qualified domain name of the device
  returned: always
  type: str

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
"""
import re

from ansible.module_utils.netcli import CommandRunner, AddCommandError
from ansible.module_utils.six import iteritems
from ansible.module_utils.eos import NetworkModule


def add_command(runner, command, output=None):
    try:
        runner.add_command(command, output)
    except AddCommandError:
        # AddCommandError is raised for any issue adding a command to
        # the runner.  Silently ignore the exception in this case
        pass


class FactsBase(object):

    def __init__(self, runner):
        self.runner = runner
        self.facts = dict()

        self.load_commands()

    def load_commands(self):
        raise NotImplementedError


class Default(FactsBase):

    SYSTEM_MAP = {
        'version': 'version',
        'serialNumber': 'serialnum',
        'modelName': 'model'
    }

    def load_commands(self):
        add_command(self.runner, 'show version', output='json')
        add_command(self.runner, 'show hostname', output='json')
        add_command(self.runner, 'bash timeout 5 cat /mnt/flash/boot-config')

    def populate(self):
        data = self.runner.get_command('show version', 'json')
        for key, value in iteritems(self.SYSTEM_MAP):
            if key in data:
                self.facts[value] = data[key]

        self.facts.update(self.runner.get_command('show hostname', 'json'))
        self.facts.update(self.parse_image())

    def parse_image(self):
        data = self.runner.get_command('bash timeout 5 cat /mnt/flash/boot-config')
        if isinstance(data, dict):
            data = data['messages'][0]
        match = re.search(r'SWI=(.+)$', data, re.M)
        if match:
            value = match.group(1)
        else:
            value = None
        return dict(image=value)

class Hardware(FactsBase):

    def load_commands(self):
        add_command(self.runner, 'dir all-filesystems', output='text')
        add_command(self.runner, 'show version', output='json')

    def populate(self):
        self.facts.update(self.populate_filesystems())
        self.facts.update(self.populate_memory())

    def populate_filesystems(self):
        data = self.runner.get_command('dir all-filesystems', 'text')
        fs = re.findall(r'^Directory of (.+)/', data, re.M)
        return dict(filesystems=fs)

    def populate_memory(self):
        values = self.runner.get_command('show version', 'json')
        return dict(
            memfree_mb=int(values['memFree']) / 1024,
            memtotal_mb=int(values['memTotal']) / 1024
        )

class Config(FactsBase):

    def load_commands(self):
        add_command(self.runner, 'show running-config', output='text')

    def populate(self):
        self.facts['config'] = self.runner.get_command('show running-config')


class Interfaces(FactsBase):

    INTERFACE_MAP = {
        'description': 'description',
        'physicalAddress': 'macaddress',
        'mtu': 'mtu',
        'bandwidth': 'bandwidth',
        'duplex': 'duplex',
        'lineProtocolStatus': 'lineprotocol',
        'interfaceStatus': 'operstatus',
        'forwardingModel': 'type'
    }

    def load_commands(self):
        add_command(self.runner, 'show interfaces', output='json')
        add_command(self.runner, 'show lldp neighbors', output='json')

    def populate(self):
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.runner.get_command('show interfaces', 'json')
        self.facts['interfaces'] = self.populate_interfaces(data)

        data = self.runner.get_command('show lldp neighbors', 'json')
        self.facts['neighbors'] = self.populate_neighbors(data['lldpNeighbors'])

    def populate_interfaces(self, data):
        facts = dict()
        for key, value in iteritems(data['interfaces']):
            intf = dict()

            for remote, local in iteritems(self.INTERFACE_MAP):
                if remote in value:
                    intf[local] = value[remote]

            if 'interfaceAddress' in value:
                intf['ipv4'] = dict()
                for entry in value['interfaceAddress']:
                    intf['ipv4']['address'] = entry['primaryIp']['address']
                    intf['ipv4']['masklen'] = entry['primaryIp']['maskLen']
                    self.add_ip_address(entry['primaryIp']['address'], 'ipv4')

            if 'interfaceAddressIp6' in value:
                intf['ipv6'] = dict()
                for entry in value['interfaceAddressIp6']['globalUnicastIp6s']:
                    intf['ipv6']['address'] = entry['address']
                    intf['ipv6']['subnet'] = entry['subnet']
                    self.add_ip_address(entry['address'], 'ipv6')

            facts[key] = intf

        return facts

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def populate_neighbors(self, neighbors):
        facts = dict()
        for value in neighbors:
            port = value['port']
            if port not in facts:
                facts[port] = list()
            lldp = dict()
            lldp['host'] = value['neighborDevice']
            lldp['port'] = value['neighborPort']
            facts[port].append(lldp)
        return facts


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
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
        module.exit_json(out=module.from_json(runner.items))

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
