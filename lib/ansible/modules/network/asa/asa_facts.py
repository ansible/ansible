#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: asa_facts
version_added: "2.4.0"
author: "Narate Pokasub (@npokasub)"
short_description: Collect facts from remote devices running Cisco ASA
description:
  - Collects a base set of device facts from a remote device that
    is running Cisco ASA.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: asa
notes:
  - Tested against ASAv 9.8.1
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
- asa_facts:
    gather_subset: all

# Collect only the config and default facts
- asa_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- asa_facts:
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
  type: string
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: string
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: string
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

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: string

# interfaces
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
"""

import re

from ansible.module_utils.network.asa.asa import run_commands
from ansible.module_utils.network.asa.asa import asa_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

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
            self.facts['hostname'] = self.parse_hostname(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
            self.facts['serialnum'] = self.parse_serialnum(data)
            self.parse_stacks(data)

    def parse_version(self, data):
        match = re.search(r'Version (\S+?)(?:,\s|\s)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^(.+) up', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Model Id:(?:\W+)(\S+)', data)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'image file is "(.+)"', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number: (\S+)', data)
        if match:
            return match.group(1)

    def parse_stacks(self, data):
        match = re.findall(r'^Model number\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_models'] = match

        match = re.findall(r'^System serial number\s+: (\S+)', data, re.M)
        if match:
            self.facts['stacked_serialnums'] = match

class Hardware(FactsBase):

    COMMANDS = [
        'dir'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)

    def parse_filesystems(self, data):
        return re.findall(r'^Directory of (\S+)/', data, re.M)

class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data

class Interfaces(FactsBase):

    COMMANDS = [
        'show interface',
        'show ipv6 interface brief'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)
 
    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['interface-type'] = self.parse_type(value)
            intf['ipv4_addr'] = self.parse_ipv4_addr(value)
            intf['ipv4_subnet'] = self.parse_ipv4_subnet(value)

            facts[key] = intf
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif (line[0] == '\t') or (line[0] == ' '):
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^(?=.*\bInterface\b)(?:\S+ )(\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = re.match(r'^(?=.*\bInterface\b)(?:\S+ )(.*\S+)', line).group(1)
        return parsed

    def parse_ipv4_addr(self, data):
        match = re.search(r'IP address (.+),', data)
        if match:
            return match.group(1)

    def parse_ipv4_subnet(self, data):
        match = re.search(r'subnet mask (.+)', data)
        if match:
            return match.group(1)

    def parse_description(self, data):
        match = re.search(r'Description: (.+)$', data, re.M)
        if match:
            return match.group(1)
        else:
            return "not set"

    def parse_macaddress(self, data):
        match = re.search(r'MAC address (.+),', data)
        if match:
            return match.group(1)

    def parse_mtu(self, data):
        match = re.search(r'MTU (\S+)', data)
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

    argument_spec.update(asa_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, 
                           supports_check_mode=True)

    warnings = list()
    check_args(module)

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
