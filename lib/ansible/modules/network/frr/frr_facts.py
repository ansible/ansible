#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: frr_facts
version_added: "2.8"
author: "Nilashish Chakraborty (@NilashishC)"
short_description: Collect facts from remote devices running Free Range Routing (FRR).
description:
  - Collects a base set of device facts from a remote device that
    is running FRR.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against FRR 6.0.
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         C(all), C(hardware), C(config), and C(interfaces).
      - Specify a list of values to include a larger subset.
      - Use a value with an initial C(!) to collect all facts except that subset.
    required: false
    default: '!config'
"""

EXAMPLES = """
- name: Collect all facts from the device
  frr_facts:
    gather_subset: all

- name: Collect only the config and default facts
  frr_facts:
    gather_subset:
      - config

- name: Collect the config and hardware facts
  frr_facts:
    gather_subset:
      - config
      - hardware

- name: Do not collect hardware facts
  frr_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_version:
  description: The FRR version running on the remote device
  returned: always
  type: str
ansible_net_api:
  description: The name of the transport
  returned: always
  type: str
ansible_net_python_version:
  description: The Python version that the Ansible controller is using
  returned: always
  type: str

# hardware
ansible_net_mem_stats:
  description: The memory statistics fetched from the device
  returned: when hardware is configured
  type: dict

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
ansible_net_mpls_ldp_neighbors:
  description: The list of MPLS LDP neighbors from the remote device
  returned: when interfaces is configured and LDP daemon is running on the device
  type: dict
"""

import platform
import re

from ansible.module_utils.network.frr.frr import run_commands, get_capabilities
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None
        self._capabilities = get_capabilities(self.module)

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(commands=cmd, check_rc=False)

    def parse_facts(self, pattern, data):
        value = None
        match = re.search(pattern, data, re.M)
        if match:
            value = match.group(1)
        return value


class Default(FactsBase):

    COMMANDS = ['show version']

    def populate(self):
        super(Default, self).populate()
        self.facts.update(self.platform_facts())

    def platform_facts(self):
        platform_facts = {}

        resp = self._capabilities
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('version', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


class Hardware(FactsBase):

    COMMANDS = ['show memory']

    def _parse_daemons(self, data):
        match = re.search(r'Memory statistics for (\w+)', data, re.M)
        if match:
            return match.group(1)

    def gather_memory_facts(self, data):
        mem_details = data.split('\n\n')
        mem_stats = {}
        mem_counters = {
            'total_heap_allocated': r'Total heap allocated:(?:\s*)(.*)',
            'holding_block_headers': r'Holding block headers:(?:\s*)(.*)',
            'used_small_blocks': r'Used small blocks:(?:\s*)(.*)',
            'used_ordinary_blocks': r'Used ordinary blocks:(?:\s*)(.*)',
            'free_small_blocks': r'Free small blocks:(?:\s*)(.*)',
            'free_ordinary_blocks': r'Free ordinary blocks:(?:\s*)(.*)',
            'ordinary_blocks': r'Ordinary blocks:(?:\s*)(.*)',
            'small_blocks': r'Small blocks:(?:\s*)(.*)',
            'holding_blocks': r'Holding blocks:(?:\s*)(.*)'
        }

        for item in mem_details:
            daemon = self._parse_daemons(item)
            mem_stats[daemon] = {}
            for fact, pattern in iteritems(mem_counters):
                mem_stats[daemon][fact] = self.parse_facts(pattern, item)

        return mem_stats

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['mem_stats'] = self.gather_memory_facts(data)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            data = re.sub(r'^Building configuration...\s+Current configuration:', '', data, flags=re.MULTILINE)
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = ['show interface']

    def populate(self):
        ldp_supported = self._capabilities['supported_protocols']['ldp']

        if ldp_supported:
            self.COMMANDS.append('show mpls ldp discovery')

        super(Interfaces, self).populate()
        data = self.responses[0]

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)
            self.populate_ipv4_interfaces(interfaces)
            self.populate_ipv6_interfaces(interfaces)

        if ldp_supported:
            data = self.responses[1]
            if data:
                self.facts['mpls_ldp_neighbors'] = self.populate_mpls_ldp_neighbors(data)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^Interface (\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        counters = {
            'description': r'Description: (.+)',
            'macaddress': r'HWaddr: (\S+)',
            'type': r'Type: (\S+)',
            'vrf': r'vrf: (\S+)',
            'mtu': r'mtu (\d+)',
            'bandwidth': r'bandwidth (\d+)',
            'lineprotocol': r'line protocol is (\S+)',
            'operstatus': r'^(?:.+) is (.+),'
        }

        for key, value in iteritems(interfaces):
            intf = dict()
            for fact, pattern in iteritems(counters):
                intf[fact] = self.parse_facts(pattern, value)
            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = list()
            primary_address = addresses = []
            primary_address = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s{2,})', value, re.M)
            addresses = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s+)secondary', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    def populate_ipv6_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'inet6 (\S+)', value, re.M)
            for address in addresses:
                addr, subnet = address.split("/")
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def populate_mpls_ldp_neighbors(self, data):
        facts = {}
        entries = data.splitlines()
        for x in entries:
            if x.startswith('AF'):
                continue
            x = x.split()
            if len(x) > 0:
                ldp = {}
                ldp['neighbor'] = x[1]
                ldp['source'] = x[3]
                facts[ldp['source']] = []
                facts[ldp['source']].append(ldp)

        return facts


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
    interfaces=Interfaces
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
            module.fail_json(msg='Subset must be one of [%s], got %s' % (', '.join(VALID_SUBSETS), subset))

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
