#!/usr/bin/python
#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# Copyright (c) 2016 Dell Inc.
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
module: dellos6_facts
version_added: "2.2"
author: "Abirami N(@abirami-n)"
short_description: Collect facts from remote devices running Dell OS6
description:
  - Collects a base set of device facts from a remote device that
    is running OS6.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: dellos6
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
# Collect all facts from the device
- dellos6_facts:
    gather_subset: all

# Collect only the config and default facts
- dellos6_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- dellos6_facts:
    gather_subset:
      - "!interfaces"
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

from ansible.module_utils.netcli import CommandRunner
from ansible.module_utils.network import NetworkModule
import ansible.module_utils.dellos6

class FactsBase(object):

    def __init__(self, runner):
        self.runner = runner
        self.facts = dict()

        self.commands()

class Default(FactsBase):

    def commands(self):
        self.runner.add_command('show version')
        self.runner.add_command('show running-config | include hostname')

    def populate(self):
        data = self.runner.get_command('show version')
        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)
        self.facts['image'] = self.parse_image(data)
        hdata =self.runner.get_command('show running-config | include hostname')
        self.facts['hostname'] = self.parse_hostname(hdata)

    def parse_version(self, data):
        match = re.search(r'HW Version(.+)\s(\d+)', data)
        if match:
            return match.group(2)

    def parse_hostname(self, data):
        match = re.search(r'\S+\s(\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'System Model ID(.+)\s([A-Z0-9]*)\n', data, re.M)
        if match:
            return match.group(2)

    def parse_image(self, data):
        match = re.search(r'Image File(.+)\s([A-Z0-9a-z_.]*)\n', data)
        if match:
            return match.group(2)

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number(.+)\s([A-Z0-9]*)\n', data)
        if match:
            return match.group(2)


class Hardware(FactsBase):

    def commands(self):
        self.runner.add_command('show memory cpu')

    def populate(self):

        data = self.runner.get_command('show memory cpu')
        match = re.findall('\s(\d+)\s', data)
        if match:
            self.facts['memtotal_mb'] = int(match[0]) / 1024
            self.facts['memfree_mb'] = int(match[1]) / 1024


class Config(FactsBase):

    def commands(self):
        self.runner.add_command('show running-config')

    def populate(self):
        self.facts['config'] = self.runner.get_command('show running-config')


class Interfaces(FactsBase):
    def commands(self):
        self.runner.add_command('show interfaces')
        self.runner.add_command('show interfaces status')
        self.runner.add_command('show interfaces transceiver properties')
        self.runner.add_command('show ip int')
        self.runner.add_command('show lldp')
        self.runner.add_command('show lldp remote-device all')

    def populate(self):
        vlan_info = dict()
        data = self.runner.get_command('show interfaces')
        interfaces = self.parse_interfaces(data)
        desc = self.runner.get_command('show interfaces status')
        properties = self.runner.get_command('show interfaces transceiver properties')
        vlan = self.runner.get_command('show ip int')
        vlan_info = self.parse_vlan(vlan)
        self.facts['interfaces'] = self.populate_interfaces(interfaces,desc,properties)
        self.facts['interfaces'].update(vlan_info)
        if 'LLDP is not enabled' not in self.runner.get_command('show lldp'):
            neighbors = self.runner.get_command('show lldp remote-device all')
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def parse_vlan(self,vlan):
        facts =dict()
        vlan_info, vlan_info_next = vlan.split('----------   -----   --------------- --------------- -------')
        for en in vlan_info_next.splitlines():
            if en == '':
                continue
            match = re.search('^(\S+)\s+(\S+)\s+(\S+)', en)
            intf = match.group(1)
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            matc=re.search('^([\w+\s\d]*)\s+(\S+)\s+(\S+)',en)
            fact['address'] = matc.group(2)
            fact['masklen'] = matc.group(3)
            facts[intf].append(fact)
        return facts                                         

    def populate_interfaces(self, interfaces, desc, properties):
        facts = dict()
        for key, value in interfaces.iteritems():
            intf = dict()
            intf['description'] = self.parse_description(key,desc)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['mediatype'] = self.parse_mediatype(key,properties)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(key,properties)
            facts[key] = intf
        return facts

    def parse_neighbors(self, neighbors):
        facts = dict()
        neighbor, neighbor_next = neighbors.split('--------- ------- ------------------- ----------------- -----------------')
        for en in neighbor_next.splitlines():
            if en == '':
                continue
            intf = self.parse_lldp_intf(en.split()[0])
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['host'] = self.parse_lldp_host(en.split()[4])
            fact['port'] = self.parse_lldp_port(en.split()[3])
            facts[intf].append(fact)

        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            else:
                match = re.match(r'Interface Name(.+)\s([A-Za-z0-9/]*)', line)
                if match:
                    key = match.group(2)
                    parsed[key] = line
                else:
                    parsed[key] += '\n%s' % line
        return parsed

    def parse_description(self, key, desc):
        desc, desc_next = desc.split('--------- --------------- ------ ------- ---- ------ ----- -- -------------------')
        desc_val, desc_info = desc_next.split('Oob')
        for en in desc_val.splitlines():
            if key in en:
                match = re.search('^(\S+)\s+(\S+)', en)
                if match.group(2) in ['Full','N/A']:
                    return "Null"
                else:
                    return match.group(2)

    def parse_macaddress(self, data):
        match = re.search(r'Burned MAC Address(.+)\s([A-Z0-9.]*)\n', data)
        if match:
            return match.group(2)

    def parse_mtu(self, data):
        match = re.search(r'MTU Size(.+)\s(\d+)\n', data)
        if match:
            return int(match.group(2))

    def parse_bandwidth(self, data):
        match = re.search(r'Port Speed(.+)\s(\d+)\n', data)
        if match:
            return int(match.group(2))

    def parse_duplex(self, data):
        match = re.search(r'Port Mode\s([A-Za-z]*)(.+)\s([A-Za-z/]*)\n', data)
        if match:
            return match.group(3)

    def parse_mediatype(self, key, properties):
        mediatype, mediatype_next = properties.split('--------- ------- --------------------- --------------------- --------------')
        flag=1
        for en in mediatype_next.splitlines():
            if key in en:
                flag=0
                match = re.search('^(\S+)\s+(\S+)\s+(\S+)',en)
                if match:
                    strval = match.group(3)
                    return match.group(3)
        if flag==1:
            return "null"
          
    def parse_type(self, key, properties):
        type_val, type_val_next = properties.split('--------- ------- --------------------- --------------------- --------------')
        flag=1
        for en in type_val_next.splitlines():
            if key in en:
                flag=0
                match = re.search('^(\S+)\s+(\S+)\s+(\S+)',en)
                if match:
                    strval = match.group(2)
                    return match.group(2)
        if flag==1:
            return "null"

    def parse_lineprotocol(self, data):
        match = re.search(r'Link Status.*\s(\S+)\s+(\S+)\n', data)
        if match:
            strval= match.group(2)
            return strval.strip('/')

    def parse_operstatus(self, data):
        match = re.search(r'Link Status.*\s(\S+)\s+(\S+)\n', data)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^([A-Za-z0-9/]*)', data)
        if match:
            return match.group(1)

    def parse_lldp_host(self, data):
        match = re.search(r'^([A-Za-z0-9]*)', data)
        if match:
            return match.group(1)

    def parse_lldp_port(self, data):
        match = re.search(r'^([A-Za-z0-9/]*)', data)
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
    runner.run()

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

