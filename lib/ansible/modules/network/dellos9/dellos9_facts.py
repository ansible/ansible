#!/usr/bin/python
#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2016 Dell Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: dellos9_facts
version_added: "2.2"
author: "Dhivya P (@dhivyap)"
short_description: Collect facts from remote devices running Dell EMC Networking OS9
description:
  - Collects a base set of device facts from a remote device that
    is running OS9.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: dellos9
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    default: [ '!config' ]
notes:
  - This module requires OS9 version 9.10.0.1P13 or above.

  - This module requires an increase of the SSH connection rate limit.
    Use the following command I(ip ssh connection-rate-limit 60)
    to configure the same. This can be also be done with the M(dellos9_config) module.
"""

EXAMPLES = """
# Collect all facts from the device
- dellos9_facts:
    gather_subset: all

# Collect only the config and default facts
- dellos9_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- dellos9_facts:
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
  type: str
ansible_net_image:
  description: The image file the device is running
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
try:
    from itertools import izip
except ImportError:
    izip = zip

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.dellos9.dellos9 import run_commands
from ansible.module_utils.network.dellos9.dellos9 import dellos9_argument_spec, check_args
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show inventory',
        'show running-config | grep hostname'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        self.facts['version'] = self.parse_version(data)
        self.facts['model'] = self.parse_model(data)
        self.facts['image'] = self.parse_image(data)

        data = self.responses[1]
        self.facts['serialnum'] = self.parse_serialnum(data)

        data = self.responses[2]
        self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'Software Version:\s*(.+)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^hostname (.+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'^System Type:\s*(.+)', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'image file is "(.+)"', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        for line in data.split('\n'):
            if line.startswith('*'):
                match = re.search(
                    r'\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line, re.M)
                if match:
                    return match.group(3)


class Hardware(FactsBase):

    COMMANDS = [
        'show file-systems',
        'show memory | except Processor'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.responses[1]
        match = re.findall(r'\s(\d+)\s', data)
        if match:
            self.facts['memtotal_mb'] = int(match[0]) // 1024
            self.facts['memfree_mb'] = int(match[2]) // 1024

    def parse_filesystems(self, data):
        return re.findall(r'\s(\S+):$', data, re.M)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(FactsBase):

    COMMANDS = [
        'show interfaces',
        'show ipv6 interface',
        'show lldp neighbors detail',
        'show inventory'
    ]

    def populate(self):
        super(Interfaces, self).populate()
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        interfaces = self.parse_interfaces(data)

        for key in list(interfaces.keys()):
            if "ManagementEthernet" in key:
                temp_parsed = interfaces[key]
                del interfaces[key]
                interfaces.update(self.parse_mgmt_interfaces(temp_parsed))

        for key in list(interfaces.keys()):
            if "Vlan" in key:
                temp_parsed = interfaces[key]
                del interfaces[key]
                interfaces.update(self.parse_vlan_interfaces(temp_parsed))

        self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if len(data) > 0:
            data = self.parse_ipv6_interfaces(data)
            self.populate_ipv6_interfaces(data)

        data = self.responses[3]
        if 'LLDP' in self.get_protocol_list(data):
            neighbors = self.responses[2]
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def get_protocol_list(self, data):
        start = False
        protocol_list = list()
        for line in data.split('\n'):
            match = re.search(r'Software Protocol Configured\s*', line)
            if match:
                start = True
                continue
            if start:
                line = line.strip()
                if line.isalnum():
                    protocol_list.append(line)
        return protocol_list

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in interfaces.items():
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
        for key, value in data.items():
            if key in self.facts['interfaces']:
                self.facts['interfaces'][key]['ipv6'] = list()
                addresses = re.findall(r'\s+(.+), subnet', value, re.M)
                subnets = re.findall(r', subnet is (\S+)', value, re.M)
                for addr, subnet in izip(addresses, subnets):
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

        for entry in neighbors.split(
                '========================================================================'):
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
        newline_count = 0
        interface_start = True

        for line in data.split('\n'):
            if interface_start:
                newline_count = 0
            if len(line) == 0:
                newline_count += 1
                if newline_count == 2:
                    interface_start = True
                continue
            else:
                match = re.match(r'^(\S+) (\S+)', line)
                if match and interface_start:
                    interface_start = False
                    key = match.group(0)
                    parsed[key] = line
                else:
                    parsed[key] += '\n%s' % line
        return parsed

    def parse_mgmt_interfaces(self, data):
        parsed = dict()
        interface_start = True
        for line in data.split('\n'):
            match = re.match(r'^(\S+) (\S+)', line)
            if "Time since" in line:
                interface_start = True
                parsed[key] += '\n%s' % line
                continue
            elif match and interface_start:
                interface_start = False
                key = match.group(0)
                parsed[key] = line
            else:
                parsed[key] += '\n%s' % line
        return parsed

    def parse_vlan_interfaces(self, data):
        parsed = dict()
        interface_start = True
        line_before_end = False
        for line in data.split('\n'):
            match = re.match(r'^(\S+) (\S+)', line)
            match_endline = re.match(r'^\s*\d+ packets, \d+ bytes$', line)

            if "Output Statistics" in line:
                line_before_end = True
                parsed[key] += '\n%s' % line
            elif match_endline and line_before_end:
                line_before_end = False
                interface_start = True
                parsed[key] += '\n%s' % line
            elif match and interface_start:
                interface_start = False
                key = match.group(0)
                parsed[key] = line
            else:
                parsed[key] += '\n%s' % line
        return parsed

    def parse_ipv6_interfaces(self, data):
        parsed = dict()
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(\S+) (\S+)', line)
                if match:
                    key = match.group(0)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'address is (\S+)', data)
        if match:
            if match.group(1) != "not":
                return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Internet address is (\S+)', data)
        if match:
            if match.group(1) != "not":
                addr, masklen = match.group(1).split('/')
                return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'LineSpeed (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'(\w+) duplex', data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        media = re.search(r'(.+) media present, (.+)', data, re.M)
        if media:
            match = re.search(r'type is (.+)$', media.group(0), re.M)
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (\w+[ ]?\w*)\(?.*\)?$', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^\sLocal Interface (\S+\s\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_host(self, data):
        match = re.search(r'Remote System Name: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_port(self, data):
        match = re.search(r'Remote Port ID: (.+)$', data, re.M)
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
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    argument_spec.update(dellos9_argument_spec)

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

    warnings = list()
    check_args(module, warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
