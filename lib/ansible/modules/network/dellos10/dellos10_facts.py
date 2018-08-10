#!/usr/bin/python
#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2017 Dell Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: dellos10_facts
version_added: "2.2"
author: "Senthil Kumar Ganesan (@skg-net)"
short_description: Collect facts from remote devices running Dell EMC Networking OS10
description:
  - Collects a base set of device facts from a remote device that
    is running OS10.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: dellos10
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
"""

EXAMPLES = """
# Collect all facts from the device
- dellos10_facts:
    gather_subset: all

# Collect only the config and default facts
- dellos10_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- dellos10_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_name:
  description: The name of the OS that is running.
  returned: Always.
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_servicetag:
  description: The service tag number of the remote device.
  returned: always
  type: str
ansible_net_model:
  description: The model name returned from the device.
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str

# hardware
ansible_net_cpu_arch:
  description: CPU Architecture of the remote device.
  returned: when hardware is configured
  type: str
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
    from lxml import etree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from ansible.module_utils.network.dellos10.dellos10 import run_commands
from ansible.module_utils.network.dellos10.dellos10 import dellos10_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = []

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
        'show version | display-xml',
        'show system | display-xml',
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        xml_data = ET.fromstring(data.encode('utf8'))

        self.facts['name'] = self.parse_name(xml_data)
        self.facts['version'] = self.parse_version(xml_data)
        self.facts['model'] = self.parse_model(xml_data)
        self.facts['hostname'] = self.parse_hostname(xml_data)

        data = self.responses[1]
        xml_data = ET.fromstring(data.encode('utf8'))

        self.facts['servicetag'] = self.parse_servicetag(xml_data)

    def parse_name(self, data):
        sw_name = data.find('./data/system-sw-state/sw-version/sw-name')
        if sw_name is not None:
            return sw_name.text
        else:
            return ""

    def parse_version(self, data):
        sw_ver = data.find('./data/system-sw-state/sw-version/sw-version')
        if sw_ver is not None:
            return sw_ver.text
        else:
            return ""

    def parse_hostname(self, data):
        hostname = data.find('./data/system-state/system-status/hostname')
        if hostname is not None:
            return hostname.text
        else:
            return ""

    def parse_model(self, data):
        prod_name = data.find('./data/system-sw-state/sw-version/sw-platform')
        if prod_name is not None:
            return prod_name.text
        else:
            return ""

    def parse_servicetag(self, data):
        svc_tag = data.find('./data/system/node/unit/mfg-info/service-tag')
        if svc_tag is not None:
            return svc_tag.text
        else:
            return ""


class Hardware(FactsBase):

    COMMANDS = [
        'show version | display-xml',
        'show processes node-id 1 | grep Mem:'
    ]

    def populate(self):

        super(Hardware, self).populate()
        data = self.responses[0]

        xml_data = ET.fromstring(data.encode('utf8'))

        self.facts['cpu_arch'] = self.parse_cpu_arch(xml_data)

        data = self.responses[1]
        match = self.parse_memory(data)
        if match:
            self.facts['memtotal_mb'] = int(match[0]) // 1024
            self.facts['memfree_mb'] = int(match[2]) // 1024

    def parse_cpu_arch(self, data):
        cpu_arch = data.find('./data/system-sw-state/sw-version/cpu-arch')
        if cpu_arch is not None:
            return cpu_arch.text
        else:
            return ""

    def parse_memory(self, data):
        return re.findall(r'(\d+)', data, re.M)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(FactsBase):

    COMMANDS = [
        'show interface | display-xml',
        'show lldp neighbors | display-xml'
    ]

    def __init__(self, module):
        self.intf_facts = dict()
        self.lldp_facts = dict()
        super(Interfaces, self).__init__(module)

    def populate(self):
        super(Interfaces, self).populate()
        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        int_show_data = (self.responses[0]).splitlines()
        pattern = '?xml version'
        data = ''
        skip = True

        # The output returns multiple xml trees
        # parse them before handling.
        for line in int_show_data:
            if pattern in line:
                if skip is False:
                    xml_data = ET.fromstring(data.encode('utf8'))
                    self.populate_interfaces(xml_data)
                    data = ''
                else:
                    skip = False

            data += line

        if skip is False:
            xml_data = ET.fromstring(data.encode('utf8'))
            self.populate_interfaces(xml_data)

        self.facts['interfaces'] = self.intf_facts

        lldp_data = (self.responses[1]).splitlines()
        data = ''
        skip = True
        # The output returns multiple xml trees
        # parse them before handling.
        for line in lldp_data:
            if pattern in line:
                if skip is False:
                    xml_data = ET.fromstring(data.encode('utf8'))
                    self.populate_neighbors(xml_data)
                    data = ''
                else:
                    skip = False

            data += line

        if skip is False:
            xml_data = ET.fromstring(data.encode('utf8'))
            self.populate_neighbors(xml_data)

        self.facts['neighbors'] = self.lldp_facts

    def populate_interfaces(self, interfaces):

        for interface in interfaces.findall('./data/interfaces/interface'):
            intf = dict()
            name = self.parse_item(interface, 'name')

            intf['description'] = self.parse_item(interface, 'description')
            intf['duplex'] = self.parse_item(interface, 'duplex')
            intf['primary_ipv4'] = self.parse_primary_ipv4(interface)
            intf['secondary_ipv4'] = self.parse_secondary_ipv4(interface)
            intf['ipv6'] = self.parse_ipv6_address(interface)
            intf['mtu'] = self.parse_item(interface, 'mtu')
            intf['type'] = self.parse_item(interface, 'type')

            self.intf_facts[name] = intf

        for interface in interfaces.findall('./bulk/data/interface'):
            name = self.parse_item(interface, 'name')
            try:
                intf = self.intf_facts[name]
                intf['bandwidth'] = self.parse_item(interface, 'speed')
                intf['adminstatus'] = self.parse_item(interface, 'admin-status')
                intf['operstatus'] = self.parse_item(interface, 'oper-status')
                intf['macaddress'] = self.parse_item(interface, 'phys-address')
            except KeyError:
                # skip the reserved interfaces
                pass

        for interface in interfaces.findall('./data/ports/ports-state/port'):
            name = self.parse_item(interface, 'name')
            # media-type name interface name format phy-eth 1/1/1
            mediatype = self.parse_item(interface, 'media-type')

            typ, sname = name.split('-eth')
            name = "ethernet" + sname
            try:
                intf = self.intf_facts[name]
                intf['mediatype'] = mediatype
            except:
                # fanout
                for subport in range(1, 5):
                    name = "ethernet" + sname + ":" + str(subport)
                    try:
                        intf = self.intf_facts[name]
                        intf['mediatype'] = mediatype
                    except:
                        # valid case to handle 2x50G
                        pass

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_item(self, interface, item):
        elem = interface.find(item)
        if elem is not None:
            return elem.text
        else:
            return ""

    def parse_primary_ipv4(self, interface):
        ipv4 = interface.find('ipv4')
        ip_address = ""
        if ipv4 is not None:
            prim_ipaddr = ipv4.find('./address/primary-addr')
            if prim_ipaddr is not None:
                ip_address = prim_ipaddr.text
                self.add_ip_address(ip_address, 'ipv4')

        return ip_address

    def parse_secondary_ipv4(self, interface):
        ipv4 = interface.find('ipv4')
        ip_address = ""
        if ipv4 is not None:
            sec_ipaddr = ipv4.find('./address/secondary-addr')
            if sec_ipaddr is not None:
                ip_address = sec_ipaddr.text
                self.add_ip_address(ip_address, 'ipv4')

        return ip_address

    def parse_ipv6_address(self, interface):

        ip_address = list()

        for addr in interface.findall('./ipv6/ipv6-addresses/address'):

            ipv6_addr = addr.find('./ipv6-address')

            if ipv6_addr is not None:
                ip_address.append(ipv6_addr.text)
                self.add_ip_address(ipv6_addr.text, 'ipv6')

        return ip_address

    def populate_neighbors(self, interfaces):
        for interface in interfaces.findall('./bulk/data/interface'):
            name = interface.find('name').text
            rem_sys_name = interface.find('./lldp-rem-neighbor-info/info/rem-system-name')
            if rem_sys_name is not None:
                self.lldp_facts[name] = list()
                fact = dict()
                fact['host'] = rem_sys_name.text
                rem_sys_port = interface.find('./lldp-rem-neighbor-info/info/rem-lldp-port-id')
                fact['port'] = rem_sys_port.text
                self.lldp_facts[name].append(fact)


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

    argument_spec.update(dellos10_argument_spec)

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
