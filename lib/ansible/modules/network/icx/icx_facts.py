#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: icx_facts
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Collect facts from remote Ruckus ICX 7000 series switches
description:
  - Collects a base set of device facts from a remote device that
    is running ICX.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>). The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
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
    type: list
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- icx_facts:
    gather_subset: all

# Collect only the config and default facts
- icx_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- icx_facts:
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
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""


import re
from ansible.module_utils.network.icx.icx import run_commands
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

    COMMANDS = ['show version', 'show running-config | include hostname']

    def populate(self):
        super(Default, self).run(['skip'])
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
            self.facts['hostname'] = self.parse_hostname(self.responses[1])
            self.parse_stacks(data)

    def parse_version(self, data):
        match = re.search(r'SW: Version ([0-9]+.[0-9]+.[0-9a-zA-Z]+)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^hostname (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'HW: (\S+ \S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'\([0-9]+ bytes\) from \S+ (\S+)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial  #:(\S+)', data)
        if match:
            return match.group(1)

    def parse_stacks(self, data):
        match = re.findall(r'UNIT [1-9]+: SL [1-9]+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_models'] = match

        match = re.findall(r'^System [Ss]erial [Nn]umber\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_serialnums'] = match


class Hardware(FactsBase):

    COMMANDS = [
        'show memory',
        'show flash'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)
            self.facts['filesystems_info'] = self.parse_filesystems_info(self.responses[1])

        if data:
            if 'Invalid input detected' in data:
                warnings.append('Unable to gather memory statistics')
            else:
                match = re.search(r'Dynamic memory: ([0-9]+) bytes total, ([0-9]+) bytes free, ([0-9]+%) used', data)
                if match:
                    self.facts['memtotal_mb'] = int(match.group(1)) / 1024
                    self.facts['memfree_mb'] = int(match.group(2)) / 1024

    def parse_filesystems(self, data):
        return "flash"

    def parse_filesystems_info(self, data):
        facts = dict()
        fs = ''
        for line in data.split('\n'):
            match = re.match(r'^(Stack unit \S+):', line)
            if match:
                fs = match.group(1)
                facts[fs] = dict()
                continue
            match = re.match(r'\W+NAND Type: Micron NAND (\S+)', line)
            if match:
                facts[fs]['spacetotal'] = match.group(1)
            match = re.match(r'\W+Code Flash Free Space = (\S+)', line)
            if match:
                facts[fs]['spacefree'] = int(int(match.group(1)) / 1024)
                facts[fs]['spacefree'] = str(facts[fs]['spacefree']) + "Kb"
        return {"flash": facts}


class Config(FactsBase):

    COMMANDS = ['skip', 'show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[1]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'skip',
        'show interfaces',
        'show running-config',
        'show lldp',
        'show media'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()
        data = self.responses[1]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv4_interfaces(data)

        data = self.responses[2]
        if data:
            self.populate_ipv6_interfaces(data)

        data = self.responses[3]
        lldp_errs = ['Invalid input', 'LLDP is not enabled']

        if data and not any(err in data for err in lldp_errs):
            neighbors = self.run(['show lldp neighbors detail'])
            if neighbors:
                self.facts['neighbors'] = self.parse_neighbors(neighbors[0])

        data = self.responses[4]
        self.populate_mediatype(data)

        interfaceList = {}
        for iface in self.facts['interfaces']:
            if 'type' in self.facts['interfaces'][iface]:
                newName = self.facts['interfaces'][iface]['type'] + iface
            else:
                newName = iface
            interfaceList[newName] = self.facts['interfaces'][iface]
        self.facts['interfaces'] = interfaceList

    def populate_mediatype(self, data):
        lines = data.split("\n")
        for line in lines:
            match = re.match(r'Port (\S+):\W+Type\W+:\W+(.*)', line)
            if match:
                self.facts['interfaces'][match.group(1)]["mediatype"] = match.group(2)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)
            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = dict()
            primary_address = addresses = []
            primary_address = re.findall(r'Internet address is (\S+/\S+), .*$', value, re.M)
            addresses = re.findall(r'Secondary address (.+)$', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'] = ipv4

    def populate_ipv6_interfaces(self, data):
        parts = data.split("\n")
        for line in parts:
            match = re.match(r'\W*interface \S+ (\S+)', line)
            if match:
                key = match.group(1)
                try:
                    self.facts['interfaces'][key]['ipv6'] = list()
                except KeyError:
                    self.facts['interfaces'][key] = dict()
                    self.facts['interfaces'][key]['ipv6'] = list()
                self.facts['interfaces'][key]['ipv6'] = {}
                continue
            match = re.match(r'\W+ipv6 address (\S+)/(\S+)', line)
            if match:
                self.add_ip_address(match.group(1), "ipv6")
                self.facts['interfaces'][key]['ipv6']["address"] = match.group(1)
                self.facts['interfaces'][key]['ipv6']["subnet"] = match.group(2)

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
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'\S+Ethernet(\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r'Port name is ([ \S]+)', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is \S+, address is (\S+)', data)
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
        match = re.search(r'Configured speed (\S+), actual (\S+)', data)
        if match:
            return match.group(1)

    def parse_duplex(self, data):
        match = re.search(r'configured duplex (\S+), actual (\S+)', data, re.M)
        if match:
            return match.group(2)

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

warnings = list()


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

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
