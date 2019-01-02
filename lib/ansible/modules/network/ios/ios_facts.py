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
module: ios_facts
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Collect facts from remote devices running Cisco IOS
description:
  - Collects a base set of device facts from a remote device that
    is running IOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: ios
notes:
  - Tested against IOS 15.6
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
ansible_net_iostype:
  description: The operating system type (IOS or IOS-XE) running on the remote device
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
ansible_net_stacked_models:
  description: The model names of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list
ansible_net_stacked_serialnums:
  description: The serial numbers of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list

# hardware
ansible_net_filesystems:
  description: All file system names available on the device
  returned: when hardware is configured
  type: list
ansible_net_filesystems_info:
  description: A hash of all file systems containing info about each file system (e.g. free and total space)
  returned: when hardware is configured
  type: dict
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
  description:
    - A hash of all interfaces running on the system.
      Expanded with other interface related facts information like
      CDP/LLDP neighbors, Port-Channels, type (access|trunk|routed),
      access|voice vlans, trunk allowed vlans
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description:
    - The list of CDP and LLDP neighbors from the remote device. If both,
      CDP and LLDP neighbor data is present on one port, CDP is preferred.
      This information is also merged into the ansible_net_interfaces hash.
  returned: when interfaces is configured
  type: dict
ansible_net_ifvlans:
  description:
    - Switchport mode (access|trunk|routed), data and/or voice vlan,
      trunk allowed vlans per interface. This information is also merged
      into the ansible_net_interfaces hash.
  returned: when interfaces is configured
  type: dict
ansible_net_etherchannels:
  description:
    - Hash containing Etherchannel information, maps logical Port-Channel
      interface to physical member interfaces. This information is also
      merged into the ansible_net_interfaces hash.
  returned: when interfaces is configured
  type: dict
"""
import re

from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args
from ansible.module_utils.network.ios.ios import normalize_interface
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


    COMMANDS = ['show version']

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['iostype'] = self.parse_iostype(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
            self.facts['hostname'] = self.parse_hostname(data)
            self.parse_stacks(data)

    def parse_version(self, data):
        match = re.search(r'Version (\S+?)(?:,\s|\s)', data)
        if match:
            return match.group(1)

    def parse_iostype(self, data):
        match = re.search(r'\S+(X86_64_LINUX_IOSD-UNIVERSALK9-M)(\S+)', data)
        if match:
            return "IOS-XE"
        else:
            return "IOS"

    def parse_hostname(self, data):
        match = re.search(r'^(.+) uptime', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'^[Cc]isco (\S+).+bytes of .*memory', data, re.M)
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

    def parse_stacks(self, data):
        match = re.findall(r'^Model [Nn]umber\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_models'] = match

        match = re.findall(r'^System [Ss]erial [Nn]umber\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_serialnums'] = match


class Hardware(FactsBase):


    COMMANDS = [
        'dir',
        'show memory statistics'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)
            self.facts['filesystems_info'] = self.parse_filesystems_info(data)

        data = self.responses[1]
        if data:
            if 'Invalid input detected' in data:
                warnings.append('Unable to gather memory statistics')
            else:
                processor_line = [l for l in data.splitlines()
                                  if 'Processor' in l].pop()
                match = re.findall(r'\s(\d+)\s', processor_line)
                if match:
                    self.facts['memtotal_mb'] = int(match[0]) / 1024
                    self.facts['memfree_mb'] = int(match[3]) / 1024

    def parse_filesystems(self, data):
        return re.findall(r'^Directory of (\S+)/', data, re.M)

    def parse_filesystems_info(self, data):
        facts = dict()
        fs = ''
        for line in data.split('\n'):
            match = re.match(r'^Directory of (\S+)/', line)
            if match:
                fs = match.group(1)
                facts[fs] = dict()
                continue
            match = re.match(r'^(\d+) bytes total \((\d+) bytes free\)', line)
            if match:
                facts[fs]['spacetotal_kb'] = int(match.group(1)) / 1024
                facts[fs]['spacefree_kb'] = int(match.group(2)) / 1024
        return facts


class Config(FactsBase):


    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            data = re.sub(
                r'^Building configuration...\s+Current configuration : \d+ bytes\n',
                '', data, flags=re.MULTILINE)
            self.facts['config'] = data


class Interfaces(FactsBase):


    COMMANDS = [
        'show run | i interface|switchport mode|switchport trunk|switchport access|switchport voice|no switchport',
        'show lldp',
        'show cdp',
        'show etherchannel summary',
        'show interfaces',
        'show ip interface',
        'show ipv6 interface',
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()
        self.facts['neighbors'] = {}

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['ifvlans'] = self.populate_interfaces_vlans(interfaces)

        data = self.responses[1]
        lldp_errs = ['Invalid input', 'LLDP is not enabled']

        if data and not any(err in data for err in lldp_errs):
            neighbors = self.run(['show lldp neighbors detail'])
            if neighbors:
                self.facts['neighbors'].update(self.parse_neighbors(neighbors[0]))

        data = self.responses[2]
        cdp_errs = ['CDP is not enabled']

        if data and not any(err in data for err in cdp_errs):
            cdp_neighbors = self.run(['show cdp neighbors detail'])
            if cdp_neighbors:
                self.facts['neighbors'].update(self.parse_cdp_neighbors(cdp_neighbors[0]))

        data = self.responses[3]
        if data:
            data = self.parse_channels(data)
            self.facts['etherchannels'] = data

        data = self.responses[4]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)
            self.update_interfaces_channel(self.facts['interfaces'], self.facts['etherchannels'])
            self.update_interfaces_neighbors(self.facts['interfaces'], self.facts['neighbors'])
            self.update_interfaces_vlans(self.facts['interfaces'], self.facts['ifvlans'])

        data = self.responses[5]
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv4_interfaces(data)

        data = self.responses[6]
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(data)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)

            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['mediatype'] = self.parse_mediatype(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_interfaces_vlans(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['mode'] = self.parse_access_mode(value)
            intf['vlandata'] = self.parse_access_vlan(value)
            intf['vlanvoice'] = self.parse_voice_vlan(value)
            intf['vlanallowed'] = self.parse_allowed_vlans(value)

            facts[key] = intf
        return facts

    def update_interfaces_channel(self, interfaces, channelinfo):
        for intf, values in iteritems(interfaces):
            self.facts['interfaces'][intf]['channel'] = None
            intfid = self.parse_interface_id(intf)
            for chintf, members in iteritems(channelinfo):
                for memberintf in members['members']:
                    memberintfid = self.parse_interface_id(memberintf)
                    if intfid == memberintfid:
                        self.facts['interfaces'][intf]['channel'] = chintf
                        self.facts['interfaces'][intf]['channelmembers'] = members['members']

    def update_interfaces_neighbors(self, interfaces, neighbors):
        for intf, values in iteritems(interfaces):
            self.facts['interfaces'][intf]['neighbor'] = None
            intfid = self.parse_interface_id(intf)
            for nintf, neighbor in iteritems(neighbors):
                nintfid = self.parse_interface_id(nintf)
                if intfid == nintfid:
                    self.facts['interfaces'][intf]['neighbor'] = neighbor

    def update_interfaces_vlans(self, interfaces, ifvlans):
        for intf, values in iteritems(interfaces):
            for vlintf, vlaninfo in iteritems(ifvlans):
                if intf == vlintf:
                    self.facts['interfaces'][intf]['mode'] = vlaninfo['mode']
                    self.facts['interfaces'][intf]['vlandata'] = vlaninfo['vlandata']
                    self.facts['interfaces'][intf]['vlanvoice'] = vlaninfo['vlanvoice']
                    self.facts['interfaces'][intf]['vlanallowed'] = vlaninfo['vlanallowed']

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = list()
            primary_address = addresses = []
            primary_address = re.findall(r'Internet address is (.+)$', value, re.M)
            addresses = re.findall(r'Secondary address (.+)$', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    def populate_ipv6_interfaces(self, data):
        for key, value in iteritems(data):
            try:
                self.facts['interfaces'][key]['ipv6'] = list()
            except KeyError:
                self.facts['interfaces'][key] = dict()
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

    def parse_channels(self, data):
        facts = dict()
        for line in data.split('\n'):
            if line == '':
                continue
            fact = dict()
            channelid = self.parse_channel_vintf(line)
            if channelid:
                fact['members'] = list()
                for entry in line.split(' '):
                    if entry == '':
                        continue
                    members = self.parse_channel_pintf(entry)
                    if members:
                        fact['members'].append(members)
                facts[channelid] = fact
        return facts

    def parse_neighbors(self, neighbors):
        facts = dict()
        for entry in neighbors.split('------------------------------------------------'):
            if entry == '':
                continue
            intf = self.parse_lldp_intf(entry)
            if intf is None:
                return facts
            intf = normalize_interface(intf)
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_lldp_host(entry)
            fact['port'] = self.parse_lldp_port(entry)
            facts[intf].append(fact)
        return facts

    def parse_cdp_neighbors(self, neighbors):
        facts = dict()
        for entry in neighbors.split('-------------------------'):
            if entry == '':
                continue
            intf_port = self.parse_cdp_intf_port(entry)
            if intf_port is None:
                return facts
            intf, port = intf_port
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_cdp_host(entry)
            fact['platform'] = self.parse_cdp_platform(entry)
            fact['address'] = self.parse_cdp_address(entry)
            fact['capabilities'] = self.parse_cdp_capabilities(entry)
            fact['port'] = port
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
                match = re.match(r'^(interface ){0,1}(\S+)', line)
                if match:
                    key = match.group(2)
                    parsed[key] = line
        return parsed

    def parse_interface_id(self, data):
        match = re.search(r'\w+(([0-9]/){0,1}[0-9]/[0-9]+)', data, re.M)
        if match:
            return match.group(1)

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is (?:.*), address is (\S+)', data)
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
        match = re.search(r'line protocol is (\S+)\s*$', data, re.M)
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

    def parse_cdp_intf_port(self, data):
        match = re.search(r'^Interface: (.+),  Port ID \(outgoing port\): (.+)$', data, re.M)
        if match:
            return match.group(1), match.group(2)

    def parse_cdp_host(self, data):
        match = re.search(r'^Device ID: (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_cdp_platform(self, data):
        match = re.search(r'^Platform: (\S+),', data, re.M)
        if match:
            return match.group(1)

    def parse_cdp_address(self, data):
        match = re.search(r'IP address: (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_cdp_capabilities(self, data):
        match = re.search(r'Capabilities: (\S+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_access_mode(self, data):
        if 'no switchport' in data:
            return 'routed'
        else:
            match = re.search(r'switchport mode (\w+)', data)
            if match:
                return match.group(1)

    def parse_access_vlan(self, data):
        match = re.search(r'switchport access vlan (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_voice_vlan(self, data):
        match = re.search(r'switchport voice vlan (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_allowed_vlans(self, data):
        match = re.search(r'switchport trunk allowed vlan (\S+)', data)
        if match:
            parsed = []
            for i in match.group(1).split(','):
                if '-' not in i:
                    parsed.append(int(i))
                else:
                    l, h = map(int, i.split('-'))
                    parsed += range(l, h + 1)
            return parsed

    def parse_channel_vintf(self, data):
        match = re.search(r'(Po\d+)', data, re.M)
        if match:
            return match.group(1)

    def parse_channel_pintf(self, data):
        match = re.search(r'(\w+([0-9]/){0,1}[0-9]/[0-9]+)', data, re.M)
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

    argument_spec.update(ios_argument_spec)

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
