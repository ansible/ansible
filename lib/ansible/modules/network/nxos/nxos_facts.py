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
module: nxos_facts
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Gets facts about NX-OS switches
description:
  - Collects facts from Cisco Nexus devices running the NX-OS operating
    system.  Fact collection is supported over both Cli and Nxapi
    transports.  This module prepends all of the base network fact keys
    with C(ansible_net_<fact>).  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, legacy, and interfaces.  Can specify a
        list of values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
    version_added: "2.2"
"""

EXAMPLES = """
- nxos_facts:
    gather_subset: all

# Collect only the config and default facts
- nxos_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- nxos_facts:
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
  type: string
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: string

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
  description: The list of LLDP/CDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict

# legacy (pre Ansible 2.2)
fan_info:
  description: A hash of facts about fans in the remote device
  returned: when legacy is configured
  type: dict
hostname:
  description: The configured hostname of the remote device
  returned: when legacy is configured
  type: dict
interfaces_list:
  description: The list of interface names on the remote device
  returned: when legacy is configured
  type: dict
kickstart:
  description: The software version used to boot the system
  returned: when legacy is configured
  type: str
module:
  description: A hash of facts about the modules in a remote device
  returned: when legacy is configured
  type: dict
platform:
  description: The hardware platform reported by the remote device
  returned: when legacy is configured
  type: str
power_supply_info:
  description: A hash of facts about the power supplies in the remote device
  returned: when legacy is configured
  type: str
vlan_list:
  description: The list of VLAN IDs configured on the remote device
  returned: when legacy is configured
  type: list
"""
import re

from ansible.module_utils.network.nxos.nxos import run_commands, get_config
from ansible.module_utils.network.nxos.nxos import get_capabilities, get_interface_type
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types, iteritems


class FactsBase(object):

    def __init__(self, module):
        self.module = module
        self.warnings = list()
        self.facts = dict()

    def populate(self):
        pass

    def run(self, command, output='text'):
        command_string = command
        command = {
            'command': command,
            'output': output
        }
        resp = run_commands(self.module, [command], check_rc=False)
        try:
            return resp[0]
        except IndexError:
            self.warnings.append('command %s failed, facts for this command will not be populated' % command_string)
            return None

    def transform_dict(self, data, keymap):
        transform = dict()
        for key, fact in keymap:
            if key in data:
                transform[fact] = data[key]
        return transform

    def transform_iterable(self, iterable, keymap):
        for item in iterable:
            yield self.transform_dict(item, keymap)


class Default(FactsBase):

    def populate(self):
        data = self.run('show version')
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
            self.facts['hostname'] = self.parse_hostname(data)

    def parse_version(self, data):
        match = re.search(r'\s+system:\s+version (\S+)', data, re.M)
        if match:
            return match.group(1)
        else:
            match = re.search(r'\s+kickstart:\s+version (\S+)', data, re.M)
            if match:
                return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Processor Board ID\s+(\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Hardware\n\s+cisco\s+(\S+\s+\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'\s+system image file is:\s+(\S+)', data, re.M)
        if match:
            return match.group(1)
        else:
            match = re.search(r'\s+kickstart image file is:\s+(\S+)', data, re.M)
            if match:
                return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'\s+Device name:\s+(\S+)', data, re.M)
        if match:
            return match.group(1)


class Config(FactsBase):

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = get_config(self.module)


class Hardware(FactsBase):

    def populate(self):
        data = self.run('dir')
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.run('show system resources')
        if data:
            self.facts['memtotal_mb'] = self.parse_memtotal_mb(data)
            self.facts['memfree_mb'] = self.parse_memfree_mb(data)

    def parse_filesystems(self, data):
        return re.findall(r'^Usage for (\S+)//', data, re.M)

    def parse_memtotal_mb(self, data):
        match = re.search(r'(\S+)K(\s+|)total', data, re.M)
        if match:
            memtotal = match.group(1)
            return int(memtotal) / 1024

    def parse_memfree_mb(self, data):
        match = re.search(r'(\S+)K(\s+|)free', data, re.M)
        if match:
            memfree = match.group(1)
            return int(memfree) / 1024


class Interfaces(FactsBase):

    INTERFACE_IPV4_MAP = frozenset([
        ('eth_ip_addr', 'address'),
        ('eth_ip_mask', 'masklen')
    ])

    INTERFACE_SVI_IPV4_MAP = frozenset([
        ('svi_ip_addr', 'address'),
        ('svi_ip_mask', 'masklen')
    ])

    INTERFACE_IPV6_MAP = frozenset([
        ('addr', 'address'),
        ('prefix', 'subnet')
    ])

    def ipv6_structure_op_supported(self):
        data = get_capabilities(self.module)
        if data:
            nxos_os_version = data['device_info']['network_os_version']
            unsupported_versions = ['I2', 'F1', 'A8']
            for ver in unsupported_versions:
                if ver in nxos_os_version:
                    return False
            return True

    def populate(self):
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.run('show interface')
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.run('show ipv6 interface') if self.ipv6_structure_op_supported() else None
        if data:
            interfaces = self.parse_interfaces(data)
            self.populate_ipv6_interfaces(interfaces)

        data = self.run('show lldp neighbors')
        if data:
            self.facts['neighbors'] = self.populate_neighbors(data)

        data = self.run('show cdp neighbors detail')
        if data:
            self.facts['neighbors'] = self.populate_neighbors_cdp(data)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line.startswith('admin') or line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(\S+)', line)
                if match:
                    key = match.group(1)
                    if not key.startswith('admin') or not key.startswith('IPv6 Interface'):
                        parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            if get_interface_type(key) == 'svi':
                intf['state'] = self.parse_state(key, value, intf_type='svi')
                intf['macaddress'] = self.parse_macaddress(value, intf_type='svi')
                intf['mtu'] = self.parse_mtu(value, intf_type='svi')
                intf['bandwidth'] = self.parse_bandwidth(value, intf_type='svi')
                intf['type'] = self.parse_type(value, intf_type='svi')
                if 'Internet Address' in value:
                    intf['ipv4'] = self.parse_ipv4_address(value, intf_type='svi')
                facts[key] = intf
            else:
                intf['state'] = self.parse_state(key, value)
                intf['description'] = self.parse_description(value)
                intf['macaddress'] = self.parse_macaddress(value)
                intf['mode'] = self.parse_mode(value)
                intf['mtu'] = self.parse_mtu(value)
                intf['bandwidth'] = self.parse_bandwidth(value)
                intf['duplex'] = self.parse_duplex(value)
                intf['speed'] = self.parse_speed(value)
                intf['type'] = self.parse_type(value)
                if 'Internet Address' in value:
                    intf['ipv4'] = self.parse_ipv4_address(value)
                facts[key] = intf

        return facts

    def parse_state(self, key, value, intf_type='ethernet'):
        match = None
        if intf_type == 'svi':
            match = re.search(r'line protocol is (\S+)', value, re.M)
        else:
            match = re.search(r'%s is (\S+)' % key, value, re.M)

        if match:
            return match.group(1)

    def parse_macaddress(self, value, intf_type='ethernet'):
        match = None
        if intf_type == 'svi':
            match = re.search(r'address is  (\S+)', value, re.M)
        else:
            match = re.search(r'address: (\S+)', value, re.M)

        if match:
            return match.group(1)

    def parse_mtu(self, value, intf_type='ethernet'):
        match = re.search(r'MTU (\S+)', value, re.M)
        if match:
            return match.group(1)

    def parse_bandwidth(self, value, intf_type='ethernet'):
        match = re.search(r'BW (\S+)', value, re.M)
        if match:
            return match.group(1)

    def parse_type(self, value, intf_type='ethernet'):
        match = None
        if intf_type == 'svi':
            match = re.search(r'Hardware is (\S+)', value, re.M)
        else:
            match = re.search(r'Hardware:  (\S+),', value, re.M)

        if match:
            return match.group(1)

    def parse_description(self, value, intf_type='ethernet'):
        match = re.search(r'Description: (.+)$', value, re.M)
        if match:
            return match.group(1)

    def parse_mode(self, value, intf_type='ethernet'):
        match = re.search(r'Port mode is (\S+)', value, re.M)
        if match:
            return match.group(1)

    def parse_duplex(self, value, intf_type='ethernet'):
        match = re.search(r'(\S+)-duplex', value, re.M)
        if match:
            return match.group(1)

    def parse_speed(self, value, intf_type='ethernet'):
        match = re.search(r'duplex, (.+)$', value, re.M)
        if match:
            return match.group(1)

    def parse_ipv4_address(self, value, intf_type='ethernet'):
        ipv4 = {}
        match = re.search(r'Internet Address is (.+)$', value, re.M)
        if match:
            address = match.group(1)
            addr = address.split('/')[0]
            ipv4['address'] = address.split('/')[0]
            ipv4['masklen'] = address.split('/')[1]
            self.facts['all_ipv4_addresses'].append(addr)
        return ipv4

    def populate_neighbors(self, data):
        objects = dict()
        if isinstance(data, str):
            # if there are no neighbors the show command returns
            # ERROR: No neighbour information
            if data.startswith('ERROR'):
                return dict()

            regex = re.compile(r'(\S+)\s+(\S+)\s+\d+\s+\w+\s+(\S+)')

            for item in data.split('\n')[4:-1]:
                match = regex.match(item)
                if match:
                    nbor = {'host': match.group(1), 'port': match.group(3)}
                    if match.group(2) not in objects:
                        objects[match.group(2)] = []
                    objects[match.group(2)].append(nbor)

        elif isinstance(data, dict):
            data = data['TABLE_nbor']['ROW_nbor']
            if isinstance(data, dict):
                data = [data]

            for item in data:
                local_intf = item['l_port_id']
                if local_intf not in objects:
                    objects[local_intf] = list()
                nbor = dict()
                nbor['port'] = item['port_id']
                nbor['host'] = item['chassis_id']
                objects[local_intf].append(nbor)

        return objects

    def populate_neighbors_cdp(self, data):
        facts = dict()

        for item in data.split('----------------------------------------'):
            if item == '':
                continue
            local_intf = self.parse_lldp_intf(item)
            if local_intf not in facts:
                facts[local_intf] = list()

            fact = dict()
            fact['port'] = self.parse_lldp_port(item)
            fact['sysname'] = self.parse_lldp_sysname(item)
            facts[local_intf].append(facts)

        return facts

    def parse_lldp_intf(self, data):
        match = re.search(r'Interface: (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_port(self, data):
        match = re.search(r'Port ID \(outgoing port\): (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_sysname(self, data):
        match = re.search(r'Device ID:(.+)$', data, re.M)
        if match:
            return match.group(1)

    def populate_ipv6_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['ipv6'] = self.parse_ipv6_address(value)
            facts[key] = intf

    def parse_ipv6_address(self, value):
        ipv6 = {}
        match_addr = re.search(r'IPv6 address: (\S+)', value, re.M)
        if match_addr:
            addr = match_addr.group(1)
            ipv6['address'] = addr
            self.facts['all_ipv6_addresses'].append(addr)
        match_subnet = re.search(r'IPv6 subnet:  (\S+)', value, re.M)
        if match_subnet:
            ipv6['subnet'] = match_subnet.group(1)

        return ipv6


class Legacy(FactsBase):
    # facts from nxos_facts 2.1

    VERSION_MAP = frozenset([
        ('host_name', '_hostname'),
        ('kickstart_ver_str', '_os'),
        ('chassis_id', '_platform')
    ])

    MODULE_MAP = frozenset([
        ('model', 'model'),
        ('modtype', 'type'),
        ('ports', 'ports'),
        ('status', 'status')
    ])

    FAN_MAP = frozenset([
        ('fanname', 'name'),
        ('fanmodel', 'model'),
        ('fanhwver', 'hw_ver'),
        ('fandir', 'direction'),
        ('fanstatus', 'status')
    ])

    POWERSUP_MAP = frozenset([
        ('psmodel', 'model'),
        ('psnum', 'number'),
        ('ps_status', 'status'),
        ('actual_out', 'actual_output'),
        ('actual_in', 'actual_in'),
        ('total_capa', 'total_capacity')
    ])

    def populate(self):
        data = self.run('show version', output='json')
        if data:
            self.facts.update(self.transform_dict(data, self.VERSION_MAP))

        data = self.run('show interface', output='json')
        if data:
            self.facts['_interfaces_list'] = self.parse_interfaces(data)

        data = self.run('show vlan brief', output='json')
        if data:
            self.facts['_vlan_list'] = self.parse_vlans(data)

        data = self.run('show module', output='json')
        if data:
            self.facts['_module'] = self.parse_module(data)

        data = self.run('show environment', output='json')
        if data:
            self.facts['_fan_info'] = self.parse_fan_info(data)
            self.facts['_power_supply_info'] = self.parse_power_supply_info(data)

    def parse_interfaces(self, data):
        objects = list()
        for item in data['TABLE_interface']['ROW_interface']:
            objects.append(item['interface'])
        return objects

    def parse_vlans(self, data):
        objects = list()
        data = data['TABLE_vlanbriefxbrief']['ROW_vlanbriefxbrief']
        if isinstance(data, dict):
            objects.append(data['vlanshowbr-vlanid-utf'])
        elif isinstance(data, list):
            for item in data:
                objects.append(item['vlanshowbr-vlanid-utf'])
        return objects

    def parse_module(self, data):
        data = data['TABLE_modinfo']['ROW_modinfo']
        if isinstance(data, dict):
            data = [data]
        objects = list(self.transform_iterable(data, self.MODULE_MAP))
        return objects

    def parse_fan_info(self, data):
        objects = list()
        if data.get('fandetails'):
            data = data['fandetails']['TABLE_faninfo']['ROW_faninfo']
        elif data.get('fandetails_3k'):
            data = data['fandetails_3k']['TABLE_faninfo']['ROW_faninfo']
        else:
            return objects
        objects = list(self.transform_iterable(data, self.FAN_MAP))
        return objects

    def parse_power_supply_info(self, data):
        if data.get('powersup').get('TABLE_psinfo_n3k'):
            data = data['powersup']['TABLE_psinfo_n3k']['ROW_psinfo_n3k']
        else:
            data = data['powersup']['TABLE_psinfo']['ROW_psinfo']
        objects = list(self.transform_iterable(data, self.POWERSUP_MAP))
        return objects


FACT_SUBSETS = dict(
    default=Default,
    legacy=Legacy,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    capabilities = get_capabilities(module)
    if capabilities:
        os_version = capabilities['device_info']['network_os_version']
        os_version_major = int(os_version[0])
        if os_version_major < 7 and "6.0(2)A8" not in os_version:
            module.fail_json(msg="this module requires JSON structured output support on the NX-OS device")

    warnings = list()
    check_args(module, warnings)

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
        warnings.extend(inst.warnings)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        # this is to maintain capability with nxos_facts 2.1
        if key.startswith('_'):
            ansible_facts[key[1:]] = value
        else:
            key = 'ansible_net_%s' % key
            ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
