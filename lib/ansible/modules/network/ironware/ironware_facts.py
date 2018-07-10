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
module: ironware_facts
version_added: "2.5"
author: "Paul Baker (@paulquack)"
short_description: Collect facts from devices running Extreme Ironware
description:
  - Collects a base set of device facts from a remote device that
    is running Ironware.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: ironware
notes:
  - Tested against Ironware 5.8e
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, mpls and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: ['!config','!mpls']
"""

EXAMPLES = """
# Collect all facts from the device
- ironware_facts:
    gather_subset: all

# Collect only the config and default facts
- ironware_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- ironware_facts:
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

# mpls
ansible_net_mpls_lsps:
  description: All MPLS LSPs configured on the device
  returned: When LSP is configured
  type: dict
ansible_net_mpls_vll:
  description: All VLL instances configured on the device
  returned: When MPLS VLL is configured
  type: dict
ansible_net_mpls_vll_local:
  description: All VLL-LOCAL instances configured on the device
  returned: When MPLS VLL-LOCAL is configured
  type: dict
ansible_net_mpls_vpls:
  description: All VPLS instances configured on the device
  returned: When MPLS VPLS is configured
  type: dict

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

from ansible.module_utils.network.ironware.ironware import run_commands
from ansible.module_utils.network.ironware.ironware import ironware_argument_spec, check_args
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
        self.responses = run_commands(self.module, self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show chassis'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)

        data = self.responses[1]
        if data:
            self.facts['model'] = self.parse_model(data)

    def parse_version(self, data):
        match = re.search(r'IronWare : Version (\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'^\*\*\* (.+) \*\*\*$', data, re.M)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial #: (\S+),', data)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'dir | include Directory',
        'show memory'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.responses[1]
        if data:
            self.facts['memtotal_mb'] = int(round(int(self.parse_memtotal(data)) / 1024 / 1024, 0))
            self.facts['memfree_mb'] = int(round(int(self.parse_memfree(data)) / 1024 / 1024, 0))

    def parse_filesystems(self, data):
        return re.findall(r'^Directory of (\S+)', data, re.M)

    def parse_memtotal(self, data):
        match = re.search(r'Total SDRAM\D*(\d+)\s', data, re.M)
        if match:
            return match.group(1)

    def parse_memfree(self, data):
        match = re.search(r'(Total Free Memory|Available Memory)\D*(\d+)\s', data, re.M)
        if match:
            return match.group(2)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


class MPLS(FactsBase):

    COMMANDS = [
        'show mpls lsp detail',
        'show mpls vll-local detail',
        'show mpls vll detail',
        'show mpls vpls detail'
    ]

    def populate(self):
        super(MPLS, self).populate()
        data = self.responses[0]
        if data:
            data = self.parse_mpls(data)
            self.facts['mpls_lsps'] = self.populate_lsps(data)

        data = self.responses[1]
        if data:
            data = self.parse_mpls(data)
            self.facts['mpls_vll_local'] = self.populate_vll_local(data)

        data = self.responses[2]
        if data:
            data = self.parse_mpls(data)
            self.facts['mpls_vll'] = self.populate_vll(data)

        data = self.responses[3]
        if data:
            data = self.parse_mpls(data)
            self.facts['mpls_vpls'] = self.populate_vpls(data)

    def parse_mpls(self, data):
        parsed = dict()
        for line in data.split('\n'):
            if not line:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(LSP|VLL|VPLS) ([^\s,]+)', line)
                if match:
                    key = match.group(2)
                    parsed[key] = line
        return parsed

    def populate_vpls(self, vpls):
        facts = dict()
        for key, value in iteritems(vpls):
            vpls = dict()
            vpls['endpoints'] = self.parse_vpls_endpoints(value)
            vpls['vc-id'] = self.parse_vpls_vcid(value)
            facts[key] = vpls
        return facts

    def populate_vll_local(self, vll_locals):
        facts = dict()
        for key, value in iteritems(vll_locals):
            vll = dict()
            vll['endpoints'] = self.parse_vll_endpoints(value)
            facts[key] = vll
        return facts

    def populate_vll(self, vlls):
        facts = dict()
        for key, value in iteritems(vlls):
            vll = dict()
            vll['endpoints'] = self.parse_vll_endpoints(value)
            vll['vc-id'] = self.parse_vll_vcid(value)
            vll['cos'] = self.parse_vll_cos(value)
            facts[key] = vll
        return facts

    def parse_vll_vcid(self, data):
        match = re.search(r'VC-ID (\d+),', data, re.M)
        if match:
            return match.group(1)

    def parse_vll_cos(self, data):
        match = re.search(r'COS +: +(\d+)', data, re.M)
        if match:
            return match.group(1)

    def parse_vll_endpoints(self, data):
        facts = list()
        regex = r'End-point[0-9 ]*: +(?P<tagged>tagged|untagged) +(vlan +(?P<vlan>[0-9]+) +)?(inner- vlan +(?P<innervlan>[0-9]+) +)?(?P<port>e [0-9/]+|--)'
        matches = re.finditer(regex, data, re.IGNORECASE | re.DOTALL)
        for n, match in enumerate(matches):
            f = match.groupdict()
            f['type'] = 'local'
            facts.append(f)

        regex = r'Vll-Peer +: +(?P<vllpeer>[0-9\.]+).*Tunnel LSP +: +(?P<lsp>\S+)'
        matches = re.finditer(regex, data, re.IGNORECASE | re.DOTALL)
        for n, match in enumerate(matches):
            f = match.groupdict()
            f['type'] = 'remote'
            facts.append(f)

        return facts

    def parse_vpls_vcid(self, data):
        match = re.search(r'Id (\d+),', data, re.M)
        if match:
            return match.group(1)

    def parse_vpls_endpoints(self, data):
        facts = list()
        regex = r'Vlan (?P<vlanid>[0-9]+)\s(?: +(?:L2.*)\s| +Tagged: (?P<tagged>.+)+\s| +Untagged: (?P<untagged>.+)\s)*'
        matches = re.finditer(regex, data, re.IGNORECASE)
        for n, match in enumerate(matches):
            f = match.groupdict()
            f['type'] = 'local'
            facts.append(f)

        regex = r'Peer address: (?P<vllpeer>[0-9\.]+)'
        matches = re.finditer(regex, data, re.IGNORECASE)
        for n, match in enumerate(matches):
            f = match.groupdict()
            f['type'] = 'remote'
            facts.append(f)

        return facts

    def populate_lsps(self, lsps):
        facts = dict()
        for key, value in iteritems(lsps):
            lsp = dict()
            lsp['to'] = self.parse_lsp_to(value)
            lsp['from'] = self.parse_lsp_from(value)
            lsp['adminstatus'] = self.parse_lsp_adminstatus(value)
            lsp['operstatus'] = self.parse_lsp_operstatus(value)
            lsp['pri_path'] = self.parse_lsp_pripath(value)
            lsp['sec_path'] = self.parse_lsp_secpath(value)
            lsp['frr'] = self.parse_lsp_frr(value)

            facts[key] = lsp

        return facts

    def parse_lsp_to(self, data):
        match = re.search(r'^LSP .* to (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_lsp_from(self, data):
        match = re.search(r'From: ([^\s,]+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lsp_adminstatus(self, data):
        match = re.search(r'admin: (\w+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lsp_operstatus(self, data):
        match = re.search(r'From: .* status: (\w+)', data, re.M)
        if match:
            return match.group(1)

    def parse_lsp_pripath(self, data):
        match = re.search(r'Pri\. path: ([^\s,]+), up: (\w+), active: (\w+)', data, re.M)
        if match:
            path = dict()
            path['name'] = match.group(1) if match.group(1) != 'NONE' else None
            path['up'] = True if match.group(2) == 'yes' else False
            path['active'] = True if match.group(3) == 'yes' else False
            return path

    def parse_lsp_secpath(self, data):
        match = re.search(r'Sec\. path: ([^\s,]+), active: (\w+).*\n.* status: (\w+)', data, re.M)
        if match:
            path = dict()
            path['name'] = match.group(1) if match.group(1) != 'NONE' else None
            path['up'] = True if match.group(3) == 'up' else False
            path['active'] = True if match.group(2) == 'yes' else False
            return path

    def parse_lsp_frr(self, data):
        match = re.search(r'Backup LSP: (\w+)', data, re.M)
        if match:
            path = dict()
            path['up'] = True if match.group(1) == 'UP' else False
            path['name'] = None
            if path['up']:
                match = re.search(r'bypass_lsp: (\S)', data, re.M)
                path['name'] = match.group(1) if match else None
            return path


class Interfaces(FactsBase):

    COMMANDS = [
        'show interfaces',
        'show ipv6 interface',
        'show lldp neighbors'
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
            data = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(data)

        data = self.responses[2]
        if data and 'LLDP is not running' not in data:
            self.facts['neighbors'] = self.parse_neighbors(data)

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

            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)

            facts[key] = intf
        return facts

    def populate_ipv6_interfaces(self, data):
        for key, value in iteritems(data):
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'\s([0-9a-f]+:+[0-9a-f:]+\/\d+)\s', value, re.M)
            for addr in addresses:
                address, masklen = addr.split('/')
                ipv6 = dict(address=address, masklen=int(masklen))
                self.add_ip_address(ipv6['address'], 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_neighbors(self, neighbors):
        facts = dict()
        for line in neighbors.split('\n'):
            if line == '':
                continue
            match = re.search(r'([\d\/]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line, re.M)
            if match:
                intf = match.group(1)
                if intf not in facts:
                    facts[intf] = list()
                fact = dict()
                fact['host'] = match.group(5)
                fact['port'] = match.group(3)
                facts[intf].append(fact)
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        for line in data.split('\n'):
            if not line:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(\S+Ethernet|eth )(\S+)', line)
                if match:
                    key = match.group(2)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r'Port name is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Internet address is ([^\s,]+)', data)
        if match:
            addr, masklen = match.group(1).split('/')
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'BW is (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'configured duplex \S+ actual (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        match = re.search(r'Type\s*:\s*(.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
    mpls=MPLS,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=["!config", "!mpls"], type='list')
    )

    argument_spec.update(ironware_argument_spec)

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

    check_args(module)

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
