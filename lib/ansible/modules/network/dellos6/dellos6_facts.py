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
module: dellos6_facts
version_added: "2.2"
author: "Abirami N (@abirami-n)"
short_description: Collect facts from remote devices running Dell EMC Networking OS6
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
        all, hardware, config, and interfaces. Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    default: [ '!config' ]
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
  description: The list of fact subsets collected from the device.
  returned: always.
  type: list

# default
ansible_net_model:
  description: The model name returned from the device.
  returned: always.
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device.
  returned: always.
  type: str
ansible_net_version:
  description: The operating system version running on the remote device.
  returned: always.
  type: str
ansible_net_hostname:
  description: The configured hostname of the device.
  returned: always.
  type: str
ansible_net_image:
  description: The image file that the device is running.
  returned: always
  type: str

# hardware
ansible_net_memfree_mb:
  description: The available free memory on the remote device in MB.
  returned: When hardware is configured.
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in MB.
  returned: When hardware is configured.
  type: int

# config
ansible_net_config:
  description: The current active config from the device.
  returned: When config is configured.
  type: str

# interfaces
ansible_net_interfaces:
  description: A hash of all interfaces running on the system.
  returned: When interfaces is configured.
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device.
  returned: When interfaces is configured.
  type: dict

"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.dellos6.dellos6 import run_commands
from ansible.module_utils.network.dellos6.dellos6 import dellos6_argument_spec, check_args
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
        'show running-config | include hostname'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)
        self.facts['image'] = self.parse_image(data)
        hdata = self.responses[1]
        self.facts['hostname'] = self.parse_hostname(hdata)

    def parse_version(self, data):
        facts = dict()
        match = re.search(r'HW Version(.+)\s(\d+)', data)
        temp, temp_next = data.split('---- ----------- ----------- -------------- --------------')
        for en in temp_next.splitlines():
            if en == '':
                continue
            match_image = re.search(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', en)
            version = match_image.group(4)
            facts["Version"] = list()
            fact = dict()
            fact['HW Version'] = match.group(2)
            fact['SW Version'] = match_image.group(4)
            facts["Version"].append(fact)
        return facts

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

    COMMANDS = [
        'show memory cpu'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        match = re.findall(r'\s(\d+)\s', data)
        if match:
            self.facts['memtotal_mb'] = int(match[0]) // 1024
            self.facts['memfree_mb'] = int(match[1]) // 1024


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(FactsBase):
    COMMANDS = [
        'show interfaces',
        'show interfaces status',
        'show interfaces transceiver properties',
        'show ip int',
        'show lldp',
        'show lldp remote-device all',
        'show version'
    ]

    def populate(self):
        vlan_info = dict()
        super(Interfaces, self).populate()
        data = self.responses[0]
        interfaces = self.parse_interfaces(data)
        desc = self.responses[1]
        properties = self.responses[2]
        vlan = self.responses[3]
        version_info = self.responses[6]
        vlan_info = self.parse_vlan(vlan, version_info)
        self.facts['interfaces'] = self.populate_interfaces(interfaces, desc, properties)
        self.facts['interfaces'].update(vlan_info)
        if 'LLDP is not enabled' not in self.responses[4]:
            neighbors = self.responses[5]
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def parse_vlan(self, vlan, version_info):
        facts = dict()
        if "N11" in version_info:
            match = re.search(r'IP Address(.+)\s([0-9.]*)\n', vlan)
            mask = re.search(r'Subnet Mask(.+)\s([0-9.]*)\n', vlan)
            vlan_id_match = re.search(r'Management VLAN ID(.+)\s(\d+)', vlan)
            vlan_id = "Vl" + vlan_id_match.group(2)
            if vlan_id not in facts:
                facts[vlan_id] = list()
            fact = dict()
            fact['address'] = match.group(2)
            fact['masklen'] = mask.group(2)
            facts[vlan_id].append(fact)
        else:
            vlan_info, vlan_info_next = vlan.split('----------   -----   --------------- --------------- -------')
            for en in vlan_info_next.splitlines():
                if en == '':
                    continue
                match = re.search(r'^(\S+)\s+(\S+)\s+(\S+)', en)
                intf = match.group(1)
                if intf not in facts:
                    facts[intf] = list()
                fact = dict()
                matc = re.search(r'^([\w+\s\d]*)\s+(\S+)\s+(\S+)', en)
                fact['address'] = matc.group(2)
                fact['masklen'] = matc.group(3)
                facts[intf].append(fact)
        return facts

    def populate_interfaces(self, interfaces, desc, properties):
        facts = dict()
        for key, value in interfaces.items():
            intf = dict()
            intf['description'] = self.parse_description(key, desc)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['mediatype'] = self.parse_mediatype(key, properties)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(key, properties)
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
            fact['port'] = self.parse_lldp_port(en.split()[3])
            if (len(en.split()) > 4):
                fact['host'] = self.parse_lldp_host(en.split()[4])
            else:
                fact['host'] = "Null"
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
        if desc_next.find('Oob') > 0:
            desc_val, desc_info = desc_next.split('Oob')
        elif desc_next.find('Port') > 0:
            desc_val, desc_info = desc_next.split('Port')
        for en in desc_val.splitlines():
            if key in en:
                match = re.search(r'^(\S+)\s+(\S+)', en)
                if match.group(2) in ['Full', 'N/A']:
                    return "Null"
                else:
                    return match.group(2)

    def parse_macaddress(self, data):
        match = re.search(r'Burned In MAC Address(.+)\s([A-Z0-9.]*)\n', data)
        if match:
            return match.group(2)

    def parse_mtu(self, data):
        match = re.search(r'MTU Size(.+)\s(\d+)\n', data)
        if match:
            return int(match.group(2))

    def parse_bandwidth(self, data):
        match = re.search(r'Port Speed\s*[:\s\.]+\s(\d+)\n', data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r'Port Mode\s([A-Za-z]*)(.+)\s([A-Za-z/]*)\n', data)
        if match:
            return match.group(3)

    def parse_mediatype(self, key, properties):
        mediatype, mediatype_next = properties.split('--------- ------- --------------------- --------------------- --------------')
        flag = 1
        for en in mediatype_next.splitlines():
            if key in en:
                flag = 0
                match = re.search(r'^(\S+)\s+(\S+)\s+(\S+)', en)
                if match:
                    strval = match.group(3)
                    return strval
        if flag == 1:
            return "null"

    def parse_type(self, key, properties):
        type_val, type_val_next = properties.split('--------- ------- --------------------- --------------------- --------------')
        flag = 1
        for en in type_val_next.splitlines():
            if key in en:
                flag = 0
                match = re.search(r'^(\S+)\s+(\S+)\s+(\S+)', en)
                if match:
                    strval = match.group(2)
                    return strval
        if flag == 1:
            return "null"

    def parse_lineprotocol(self, data):
        data = data.splitlines()
        for d in data:
            match = re.search(r'^Link Status\s*[:\s\.]+\s(\S+)', d)
            if match:
                return match.group(1)

    def parse_operstatus(self, data):
        data = data.splitlines()
        for d in data:
            match = re.search(r'^Link Status\s*[:\s\.]+\s(\S+)', d)
            if match:
                return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^([A-Za-z0-9/]*)', data)
        if match:
            return match.group(1)

    def parse_lldp_host(self, data):
        match = re.search(r'^([A-Za-z0-9-]*)', data)
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
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    argument_spec.update(dellos6_argument_spec)

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
