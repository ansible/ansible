#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ordnance_facts
version_added: "2.3"
author: "Alexander Turner (alex.turner@ordnance.io)"
short_description: Collect facts from Ordnance Virtual Routers over SSH
description:
  - Collects a base set of device facts from an Ordnance Virtual
    router over SSH. This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
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
---
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: RouterName
    password: ordnance
    transport: cli

---
# Collect all facts from the device
- ordnance_facts:
    gather_subset: all
    provider: "{{ cli }}"

# Collect only the config and default facts
- ordnance_facts:
    gather_subset:
      - config
    provider: "{{ cli }}"

# Do not collect hardware facts
- ordnance_facts:
    gather_subset:
      - "!hardware"
    provider: "{{ cli }}"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the virtual router
  returned: always
  type: list

# config
ansible_net_config:
  description: The current active config from the virtual router
  returned: when config is configured
  type: str

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the virtual router
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the virtual router
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the virtual router
  returned: when interfaces is configured
  type: dict
"""
import re
import traceback

from ansible.module_utils.network.common.network import NetworkModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip
from ansible.module_utils._text import to_native


class FactsBase(object):

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.failed_commands = list()

    def run(self, cmd):
        try:
            return self.module.cli(cmd)[0]
        except:
            self.failed_commands.append(cmd)


class Config(FactsBase):

    def populate(self):
        data = self.run('show running-config')
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    def populate(self):
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.run('show interfaces')
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.run('show ipv6 interface')
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(data)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)

            ipv4 = self.parse_ipv4(value)
            intf['ipv4'] = self.parse_ipv4(value)
            if ipv4:
                self.add_ip_address(ipv4['address'], 'ipv4')

            intf['duplex'] = self.parse_duplex(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv6_interfaces(self, data):
        for key, value in iteritems(data):
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'\s+(.+), subnet', value, re.M)
            subnets = re.findall(r', subnet is (.+)$', value, re.M)
            for addr, subnet in zip(addresses, subnets):
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
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

    def parse_duplex(self, data):
        match = re.search(r'(\w+) Duplex', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

FACT_SUBSETS = dict(
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

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    failed_commands = list()

    try:
        for inst in instances:
            inst.populate()
            failed_commands.extend(inst.failed_commands)
            facts.update(inst.facts)
    except Exception as exc:
        module.fail_json(msg=to_native(exc), exception=traceback.format_exc())

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, failed_commands=failed_commands)


if __name__ == '__main__':
    main()
