# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import platform
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.eos.eos import run_commands, get_capabilities


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.warnings = list()
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS), check_rc=False)


class Default(FactsBase):

    SYSTEM_MAP = {
        'serialNumber': 'serialnum',
    }

    COMMANDS = [
        'show version | json',
        'show hostname | json',
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        for key, value in iteritems(self.SYSTEM_MAP):
            if key in data:
                self.facts[value] = data[key]

        self.facts.update(self.responses[1])
        self.facts.update(self.platform_facts())

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('model', 'image', 'version', 'platform', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


class Hardware(FactsBase):

    COMMANDS = [
        'dir all-filesystems',
        'show version | json'
    ]

    def populate(self):
        super(Hardware, self).populate()
        self.facts.update(self.populate_filesystems())
        self.facts.update(self.populate_memory())

    def populate_filesystems(self):
        data = self.responses[0]

        if isinstance(data, dict):
            data = data['messages'][0]

        fs = re.findall(r'^Directory of (.+)/', data, re.M)
        return dict(filesystems=fs)

    def populate_memory(self):
        values = self.responses[1]
        return dict(
            memfree_mb=int(values['memFree']) / 1024,
            memtotal_mb=int(values['memTotal']) / 1024
        )


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(FactsBase):

    INTERFACE_MAP = {
        'description': 'description',
        'physicalAddress': 'macaddress',
        'mtu': 'mtu',
        'bandwidth': 'bandwidth',
        'duplex': 'duplex',
        'lineProtocolStatus': 'lineprotocol',
        'interfaceStatus': 'operstatus',
        'forwardingModel': 'type'
    }

    COMMANDS = [
        'show interfaces | json',
        'show lldp neighbors | json'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        self.facts['interfaces'] = self.populate_interfaces(data)

        data = self.responses[1]
        if data:
            self.facts['neighbors'] = self.populate_neighbors(data['lldpNeighbors'])

    def populate_interfaces(self, data):
        facts = dict()
        for key, value in iteritems(data['interfaces']):
            intf = dict()

            for remote, local in iteritems(self.INTERFACE_MAP):
                if remote in value:
                    intf[local] = value[remote]

            if 'interfaceAddress' in value:
                intf['ipv4'] = dict()
                for entry in value['interfaceAddress']:
                    intf['ipv4']['address'] = entry['primaryIp']['address']
                    intf['ipv4']['masklen'] = entry['primaryIp']['maskLen']
                    self.add_ip_address(entry['primaryIp']['address'], 'ipv4')

            if 'interfaceAddressIp6' in value:
                intf['ipv6'] = dict()
                for entry in value['interfaceAddressIp6']['globalUnicastIp6s']:
                    intf['ipv6']['address'] = entry['address']
                    intf['ipv6']['subnet'] = entry['subnet']
                    self.add_ip_address(entry['address'], 'ipv6')

            facts[key] = intf

        return facts

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def populate_neighbors(self, neighbors):
        facts = dict()
        for value in neighbors:
            port = value['port']
            if port not in facts:
                facts[port] = list()
            lldp = dict()
            lldp['host'] = value['neighborDevice']
            lldp['port'] = value['neighborPort']
            facts[port].append(lldp)
        return facts
