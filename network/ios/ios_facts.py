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
module: ios_facts
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Collect facts from remote devices running IOS
description:
  - Collects a base set of device facts from a remote device that
    is running IOS.  The M(ios_facts) module prepends all of the
    base network fact keys with U(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: ios
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument inlcude
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial M(!) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- ios_facts:
    gather_subset: all

# Collect only the config and default facts
- ios_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- ios_facts:
    gather_subset:
      - "!interfaces"
"""

RETURN = """
ansible_net_config:
  description: The running-config from the device
  returned: when config is configured
  type: str
ansible_net_interfaces:
  description: The interfaces on the device
  returned: when interfaces is configured
  type: dict
ansible_net_filesystems:
  description: A list of the filesystems on the device
  returned: when hardware is configured
  type: list
ansible_net_hostname:
  description: The configured system hostname
  returned: always
  type: str
ansible_net_image:
  desription: The image the system booted from
  returned: always
  type: str
ansible_net_module:
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
ansible_net_gather_subset:
  description: The list of subsets gathered by the module
  returned: always
  type: list
ansible_net_all_ipv4_addresses:
  description: The list of all IPv4 addresses configured on the device
  returned: when interface is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: The list of all ipv6 addresses configured on the device
  returned: when interface is configured
  type: list
ansible_net_neighbors:
  description: The set of LLDP neighbors
  returned: when interface is configured
  type: list
ansible_net_memfree_mb:
  description: The amount of free processor memory
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total amount of available processor memory
  returned: when hardware is configured
  type: int
"""
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcmd import CommandRunner
from ansible.module_utils.ios import NetworkModule


class FactsBase(object):

    def __init__(self, runner):
        self.runner = runner
        self.facts = dict()

        self.commands()

class Default(FactsBase):

    def commands(self):
        self.runner.add_command('show version')

    def populate(self):
        data = self.runner.get_command('show version')

        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)
        self.facts['image'] = self.parse_image(data)
        self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'Version (\S+),', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^(.+) uptime', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'^Cisco (.+) \(revision', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'image file is "(.+)"', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'board ID (\S+)', data)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    def commands(self):
        self.runner.add_command('dir all-filesystems | include Directory')
        self.runner.add_command('show version')
        self.runner.add_command('show memory statistics | include Processor')

    def populate(self):
        data = self.runner.get_command('dir all-filesystems | include Directory')
        self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.runner.get_command('show memory statistics | include Processor')
        match = re.findall('\s(\d+)\s', data)
        if match:
            self.facts['memtotal_mb'] = int(match[0])/1024
            self.facts['memfree_mb'] = int(match[1])/1024

    def parse_filesystems(self, data):
        return re.findall(r'^Directory of (\S+)/', data, re.M)


class Config(FactsBase):

    def commands(self):
        self.runner.add_command('show running-config')

    def populate(self):
        self.facts['config'] = self.runner.get_command('show running-config')


class Interfaces(FactsBase):

    def commands(self):
        self.runner.add_command('show interfaces')
        self.runner.add_command('show ipv6 interface')
        self.runner.add_command('show lldp')
        self.runner.add_command('show lldp neighbors detail')

    def populate(self):
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.runner.get_command('show interfaces')
        interfaces = self.parse_interfaces(data)
        self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.runner.get_command('show ipv6 interface')
        if len(data) > 0:
            data = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(data)

        if 'LLDP is not enabled' not in self.runner.get_command('show lldp'):
            neighbors = self.runner.get_command('show lldp neighbors detail')
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in interfaces.iteritems():
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)

            ipv4 = self.parse_ipv4(value)
            intf['ipv4'] = self.parse_ipv4(value)
            if ipv4:
                self.add_ip_address(ipv4['address'], 'ipv4')

            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['mediatype'] = self.parse_mediatype(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv6_interfaces(self, data):
        for key, value in data.iteritems():
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'\s+(.+), subnet', value, re.M)
            subnets = re.findall(r', subnet is (.+)$', value, re.M)
            for addr, subnet in itertools.izip(addresses, subnets):
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        for entry in neighbors.split('------------------------------------------------'):
            if entry == '':
                continue
            intf = self.parse_lldp_intf(entry)
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_lldp_host(entry)
            fact['port'] = self.parse_lldp_port(entry)
            facts[intf].append(fact)
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Internet address is (\S+)', data)
        if match:
            addr, masklen = match.group(1).split('/')
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'BW (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'(\w+) Duplex', data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        match = re.search(r'media type is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^Local Intf: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_host(self, data):
        match = re.search(r'System Name: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_port(self, data):
        match = re.search(r'Port id: (.+)$', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
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

    runner.run_commands()

    try:
        for inst in instances:
            inst.populate()
            facts.update(inst.facts)
    except Exception:
        module.exit_json(out=module.from_json(runner.items))

    ansible_facts = dict()
    for key, value in facts.iteritems():
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()

