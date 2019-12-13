# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The asa legacy fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import platform
import re

from ansible.module_utils.network.asa.asa import run_commands, get_capabilities


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = ['show version']

    def populate(self):
        super(Default, self).populate()
        self.facts.update(self.platform_facts())
        data = self.responses[0]
        if data:
            self.facts['asatype'] = self.parse_asatype(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.parse_stacks(data)

    def parse_asatype(self, data):
        match = re.search(r'Hardware:(\s+)ASA', data)
        if match:
            return "ASA"

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number: (\S+)', data)
        if match:
            return match.group(1)

    def parse_stacks(self, data):
        match = re.findall(r'^Model [Nn]umber\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_models'] = match

        match = re.findall(r'^System [Ss]erial [Nn]umber\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_serialnums'] = match

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']
        platform_facts['system'] = device_info['network_os']

        for item in ('model', 'image', 'version', 'platform', 'hostname', 'firepower_version', 'device_mgr_version'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


class Hardware(FactsBase):

    COMMANDS = [
        'dir',
        'show memory'
    ]

    def populate(self):
        warnings = list()
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
                mem_list = [l for l in data.splitlines() if 'memory' in l]
                for each in mem_list:
                    if 'Free memory' in each:
                        match = re.search(r'Free memory.+ (\d+) .+(\d\d)', each)
                        if match:
                            self.facts['memfree_mb'] = int(match.group(1)) // 1024
                    elif 'Used memory' in each:
                        match = re.search(r'Used memory.+ (\d+) .+(\d\d)', each)
                        if match:
                            self.facts['memused_mb'] = int(match.group(1)) // 1024
                    elif 'Total memory' in each:
                        match = re.search(r'Total memory.+ (\d+) .+(\d\d)', each)
                        if match:
                            self.facts['memtotal_mb'] = int(match.group(1)) // 1024

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
            match = re.match(r'^(\d+) bytes total \((\d+) bytes free\/(\d+)% free\)', line)
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
