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
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: qnos_facts
version_added: "2.9"
author: "Mark Yang (@QCT)"
short_description: Collect facts from remote devices running Quanta Switches
description:
  - Collects a base set of device facts from a remote device that
    is running QNOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: qnos
notes:
  - Tested against QNOS
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    type: list
    required: false
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- qnos_facts:
    gather_subset: all

# Collect only the config and default facts
- qnos_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- qnos_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_burned_in_mac:
  description: The burned in mac of the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_license:
  description: The license status of the remote device
  returned: always
  type: str
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_part_no:
  description: The part no of the remote device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: str
ansible_net_storage:
  description: The storage type of the remote device
  returned: always
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str


# hardware
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_network_chip:
  description: The network processing chip the remote device
  returned: when hardware is configured
  type: str
ansible_net_fans:
  description: The information of fans on the remote device
  returned: when hardware is configured
  type: dict
ansible_net_powers:
  description: The information of powers on the remote device in Mb
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
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""
import re

from ansible.module_utils.network.qnos.qnos import run_commands
from ansible.module_utils.network.qnos.qnos import qnos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


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

    COMMANDS = ['show version', 'show hosts']

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['part_no'] = self.parse_partno(data)
            self.facts['burned_in_mac'] = self.parse_burned_in_mac(data)
            self.facts['license'] = self.parse_license(data)
            self.facts['storage'] = self.parse_storage(data)

        data = self.responses[1]
        if data:
            self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'Software Version[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'Host name[\.]+ \s*(.+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Machine Model[\.]+ \s*(.+)', data, re.M)
        if match:
            return match.group(1)

    def parse_partno(self, data):
        match = re.search(r'Part Number[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_burned_in_mac(self, data):
        match = re.search(r'Burned In MAC Address[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_license(self, data):
        match = re.search(r'License Key Status[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_storage(self, data):
        match = re.search(r'Software Storage[\.]+ \s*(.+)', data)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show process cpu',
        'show hardware',
        'show environment'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            memalloc = self.parse_memallocate_mb(data)
            memfree = self.parse_memfree_mb(data)
            self.facts['memtotal_mb'] = (int(memalloc) + int(memfree)) / 1024
            self.facts['memfree_mb'] = int(memfree) / 1024

        data = self.responses[1]
        if data:
            network_chip = self.parse_network_processiong_device(data)
            self.facts['network_chip'] = network_chip
            data_env = self.responses[2]
            self.facts['fans'] = self.populate_fans(data, data_env)
            self.facts['powers'] = self.populate_powers(data, data_env)

    def parse_memfree_mb(self, data):
        match = re.search(r'free      \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_memallocate_mb(self, data):
        match = re.search(r'alloc     \s*(.+)', data)
        if match:
            return match.group(1)

    def parse_network_processiong_device(self, data):
        match = re.search(r'Network Processing Device[\.]+ (.+)', data)
        if match:
            return match.group(1)

    def populate_fans(self, data, data_env):
        fans = dict()
        match = re.findall(r'FAN (\d) Status', data)
        for entry in match:
            status = '-'
            direction = '-'
            match = re.search(r'FAN {0} Status[\.]+ (.+)'.format(entry), data)
            if match:
                status = match.group(1)

            match = re.search(r'FAN {0} Airflow Direction[\.]+ (.+)'.format(entry), data)
            if match:
                direction = match.group(1)

            fans[entry] = dict(status=status, direction=direction)
        return fans

    def populate_powers(self, data, data_env):
        powers = dict()
        match = re.findall(r'Switch Power\+ (\d)\.', data)
        for entry in match:
            status = '-'
            type = 'NA'
            model = 'NA'
            serial = 'NA'
            revision = 'NA'
            firmware = 'NA'
            direction = 'NA'
            match = re.search(r'(Switch Power\+ {0}[\S ]+?[\r\n][\r\n])'.format(entry), data)
            if match:
                power_info = match.group(1)
                if power_info:
                    match = re.search(r'Switch Power\+ {0}[\.]+ (.+)'.format(entry), power_info)
                    if match:
                        status = match.group(1)

                    match = re.search(r'Type[\.]+ (.+)', power_info)
                    if match:
                        type = match.group(1)

                    match = re.search(r'Model[\.]+ (.+)', power_info)
                    if match:
                        model = match.group(1)

                    match = re.search(r'Serial Number[\.]+ (.+)', power_info)
                    if match:
                        serial = match.group(1)

                    match = re.search(r'Revision Number[\.]+ (.+)', power_info)
                    if match:
                        revision = match.group(1)

                    match = re.search(r'FW Version[\.]+ (.+)', power_info)
                    if match:
                        firmware = match.group(1)

                    match = re.search(r'Airflow Direction[\.]+ (.+)', power_info)
                    if match:
                        direction = match.group(1)

            powers[entry] = dict(status=status, type=type, model=model, revision=revision, firmware=firmware, direction=direction)
        return powers


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'show interface status | begin 0/1',
        'show lldp remote-device | begin 0/1'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if data:
            self.facts['neighbors'] = self.parse_neighbors(data)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            interface_type = ''
            match = re.match(r'^(vlan \d+)|^(tunnel \d+)|^(ch\d+)|^(lb\d+)|^(\d+/\d+)', value)
            if match:
                if match.group(1):
                    interface_type = 'vlan'
                elif match.group(2):
                    interface_type = 'tunnel'
                elif match.group(3):
                    interface_type = 'port-channel'
                elif match.group(4):
                    interface_type = 'loopback'
                else:
                    interface_type = 'port'

            if interface_type not in facts:
                facts[interface_type] = list()

            intf = dict()
            intf_info = dict()
            intf_info = self.populate_interface_info(key, interface_type)
            intf[key] = intf_info
            facts[interface_type].append(intf)
        return facts

    def populate_interface_info(self, data, interface_type):
        intf_info = dict()
        commands = list()
        if interface_type == 'port':
            commands.append('show interface status {0}'.format(data))
            commands.append('show ip interface port {0}'.format(data))
            commands.append('show ipv6 interface port {0}'.format(data))
        elif interface_type == 'vlan':
            commands.append('show interface status {0}'.format(data))
            commands.append('show ip interface {0}'.format(data))
            commands.append('show ipv6 interface {0}'.format(data))
        elif interface_type == 'loopback':
            id = data.split('lb')[1]
            commands.append('show interface status loopback {0}'.format(id))
            commands.append('show ip interface loopback {0}'.format(id))
            commands.append('show ipv6 interface loopback {0}'.format(id))
        elif interface_type == 'port-channel':
            id = data.split('ch')[1]
            commands.append('show interface status port-channel {0}'.format(id))
        else:
            commands.append('show interface status {0}'.format(data))

        value = run_commands(self.module, commands, check_rc=False)
        intf_info['description'] = self.parse_description(value[0])
        intf_info['adminmode'] = self.parse_adminmode(value[0])
        intf_info['macaddress'] = self.parse_macaddress(value[0])
        intf_info['capability'] = self.parse_capability(value[0])
        intf_info['physicalmode'] = self.parse_physicalmode(value[0])
        intf_info['physicalstatus'] = self.parse_physicalstatus(value[0])
        intf_info['lacpmode'] = self.parse_lacpmode(value[0])
        intf_info['linkstatus'] = self.parse_linkstatus(value[0])
        intf_info['mediatype'] = self.parse_mediatype(value[0])

        if len(value) > 2:
            ipv4 = self.parse_ipv4(value[1])
            intf_info['ipv4'] = self.parse_ipv4(value[1])
            if ipv4:
                self.add_ip_address(ipv4, 'ipv4')

            intf_info['mtu'] = self.parse_mtu(value[1])
            intf_info['bandwidth'] = self.parse_bandwidth(value[1])
            intf_info['linkspeed'] = self.parse_linkspeed(value[1])

            intf_info['ipv6'] = self.parse_ipv6(value[2])

        return intf_info

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            for key, value in iteritems(address):
                if key == 'primary':
                    self.facts['all_ipv4_addresses'].append(value['address'])
                if key == 'secondary':
                    for entry in value:
                        self.facts['all_ipv4_addresses'].append(entry['address'])
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        lldpObjRegex = re.compile(r'^(\d+/\d+) +(\d+)+ +([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}) +(\d+/\d+) *(.+)?$')
        for entry in neighbors.split('\n'):
            if entry != '':
                lldp_value = lldpObjRegex.match(entry)
                if lldp_value:
                    intf = lldp_value.group(1)
                    if intf not in facts:
                        facts[intf] = list()
                    fact = dict()
                    fact['chassis_id'] = lldp_value.group(3)
                    fact['port'] = lldp_value.group(4)
                    fact['host'] = lldp_value.group(5)
                    facts[intf].append(fact)
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(vlan \d+|tunnel \d+|ch\d+|lb\d+|\d+/\d+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line

        return parsed

    def parse_description(self, data):
        match = re.search(r'Description[\.]+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'MAC address[\.]+ (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        parsed = dict()
        match = re.search(r'Primary IP address[\.]+ (\S+)', data)
        if match:
            addr, mask = match.group(1).split('/')
            parsed['primary'] = dict(address=addr, mask=mask)
        match = re.search(r'Secondary IP Address\(es\)[\.]+ (\S+)', data, re.M)
        if match:
            secondary = list()
            addr, mask = match.group(1).split('/')
            secondary.append(dict(address=addr, mask=mask))
            match = re.findall(r'[\r\n]\.+ (\S+)', data)
            for entry in match:
                addr, mask = entry.split('/')
                secondary.append(dict(address=addr, mask=mask))
            parsed['secondary'] = secondary
        return parsed

    def parse_ipv6(self, data):
        parsed = list()
        match = re.findall(r' (\S+)? \[TENT\]', data)
        for entry in match:
            prefix, prefix_length = entry.split('/')
            parsed.append(dict(prefix=prefix, prefix_length=prefix_length))
            self.add_ip_address(prefix, 'ipv6')
        return parsed

    def parse_mtu(self, data):
        match = re.search(r'IP MTU\.+ (\S+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'Bandwidth\.+ (\S+)', data)
        if match:
            return int(match.group(1))

    def parse_linkspeed(self, data):
        match = re.search(r'Link Speed Data Rate\.+ (\S+? \S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        match = re.search(r'Cable Type\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_linkstatus(self, data):
        match = re.search(r'Link Status\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_adminmode(self, data):
        match = re.search(r'Admin Mode\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_lacpmode(self, data):
        match = re.search(r'LACP Mode\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_capability(self, data):
        match = re.search(r'Capability Information\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_physicalmode(self, data):
        match = re.search(r'Physical Mode\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_physicalstatus(self, data):
        match = re.search(r'Physical Status\.+ (.+)$', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

warnings = list()


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    argument_spec.update(qnos_argument_spec)

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

    check_args(module, warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
