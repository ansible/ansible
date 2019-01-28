#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Pica8, Inc. <simon.yang@pica8.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: picos_facts
version_added: "2.8"
author: "Pica8 (@pica8)"
short_description: Collect facts from remote devices running PicOS
description:
  - Collects selected sets of facts from a remote device that
    is running PicOS.  This module prepends all of the
    base network fact keys with U(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
#extends_documentation_fragment: picos
notes:
  - Tested against PicOS 2.11.7
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, default, config, hardware, and neighbors. Can specify a
        list of values to include a larger subset. Values can also be
        used with an initial C(M(-)) to specify that a specific subset
        should not be collected. If not supplied, use default
    required: false
'''

EXAMPLES = '''
- name: collect all facts from the device
  picos_facts:
    gather_subset: all

- name: collect only the config and default facts
  picos_facts:
    gather_subset: config

- name: collect everything except config and hardware
  picos_facts:
    gather_subset: -config,-hardware
'''

RETURN = '''
ansible_net_config:
  description: The running-config from the device
  returned: when config is configured
  type: list
ansible_net_hostname:
  description: The configured system hostname
  returned: always
  type: str
ansible_net_model:
  description: The device model string
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the device
  returned: always
  type: str
ansible_net_version:
  description: The version of PicOS
  returned: always
  type: str
ansible_net_hardware:
  description: Device hardware status
  returned: always
  type: dict
ansible_net_license:
  description: Device PicOS license info
  returned: always
  type: dict
ansible_net_gather_subset:
  description: The list of subsets gathered by the module
  returned: always
  type: list
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.picos.picos import run_command, run_commands
from ansible.module_utils.network.picos.picos import shell_pattern, cli_pattern, config_pattern, config_script_pattern


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self, command_pattern=shell_pattern):
        if command_pattern == shell_pattern:
            self.responses = run_commands(self.module, list(self.COMMANDS))
        else:
            self.responses = run_command(self.module, list(self.COMMANDS), '', command_pattern)

        if isinstance(self.responses, list):
            self.responses = ''.join(self.responses)

    def get_value(self, data, pattern):
        match = re.search(pattern, data)
        value = None
        if match:
            value = match.group(1)
        return value


class Default(FactsBase):

    COMMANDS = [
        'hostname',
        'cat /sys/class/swmon/hwinfo/serial_number',
        'version'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses.replace('\"', '').replace('\t', '')

        self.facts['hostname'] = self.get_value(data, r'(\S+)')
        self.facts['serialnum'] = self.get_value(data, r'\s+(\S+)')
        self.facts['model'] = self.get_value(data, r'Hardware Model\s*: (\S+)')
        self.facts['version'] = self.get_value(data, r'Version/Revision : (\S+)')


class Config(FactsBase):

    COMMANDS = [
        'show | display set'
    ]

    def populate(self):
        super(Config, self).populate(config_pattern)

        data = self.responses.replace('    ', '')
        config = re.findall(r'\n(set.+)\r', data)
        self.facts['config'] = config


class Hardware(FactsBase):

    COMMANDS = [
        'show system fan',
        'show system temperature',
        'show system rpsu',
        'show system cpu-usage',
        'show system memory-usage'
    ]

    def populate(self):
        super(Hardware, self).populate(cli_pattern)
        data = self.responses.replace('\"', '').replace('\t', '')

        hardware = dict()
        hardware['cpu-usage'] = self.get_value(data, r'CPU usage: (\d+%)')

        mu = re.findall(r'(\d+)', self.get_value(data, r'Mem: (.+)\r\n'))
        musg = dict()
        musg['total'] = mu[0]
        musg['used'] = mu[1]
        musg['free'] = mu[2]
        musg['shared'] = mu[3]
        musg['buffers'] = mu[4]
        musg['cached'] = mu[5]
        hardware['memory-usage'] = musg

        fan = dict()
        fan['fan 1'] = self.get_value(data, 'Fan  1 : (.+)\r\n')
        fan['fan 2'] = self.get_value(data, 'Fan  2 : (.+)\r\n')
        fan['fan 3'] = self.get_value(data, 'Fan  3 : (.+)\r\n')
        fan['fan 4'] = self.get_value(data, 'Fan  4 : (.+)\r\n')
        hardware['fan'] = fan

        rpsu = dict()
        rpsu1 = dict()
        rpsu1['status'] = self.get_value(data, r'RPSU 1: (.+)\r\n')
        if rpsu1['status'] == 'Powered on':
            rpsu1['temperature'] = self.get_value(data, r'TEMPERATURE_1 : (.+)\r\n')
            rpsu1['fan-speed'] = self.get_value(data, r'FAN_SPEED_1\s+: (.+)\r\n')
        rpsu2 = dict()
        rpsu2['status'] = self.get_value(data, r'RPSU 2: (.+)\r\n')
        if rpsu2['status'] == 'Powered on':
            rpsu2['temperature'] = self.get_value(data, r'TEMPERATURE_1 : (.+)\r\n')
            rpsu2['fan-speed'] = self.get_value(data, r'FAN_SPEED_1\s+: (.+)\r\n')
        rpsu['rpsu1'] = rpsu1
        rpsu['rpsu2'] = rpsu2
        hardware['rpsu'] = rpsu

        temperature = dict()
        temperature['board'] = self.get_value(data, r'Board\s+: (.+)\r\n')
        temperature['cpu'] = self.get_value(data, r'CPU\s+: (.+)\r\n')
        temperature['asic'] = self.get_value(data, r'ASIC\s+: (.+)\r\n')
        hardware['temperature'] = temperature

        self.facts['hardware'] = hardware


class License(FactsBase):

    COMMANDS = [
        'license -s'
    ]

    def populate(self):
        super(License, self).populate()
        data = self.responses.replace('\"', '').replace('\t', '')

        license = dict()
        license['installed'] = ('' == self.get_value(data, 'No license installed'))
        license['type'] = self.get_value(data, r'Type:\s*([0-9A-Z]+)')
        license['hardwareid'] = self.get_value(data, r'Hardware ID:\s*(\S+)')
        if license['installed']:
            license['feature'] = self.get_value(data, r'Feature:\[(.+)\],')
            license['exprdate'] = self.get_value(data, r'Support End Date:(\S+),')
        self.facts['license'] = license


FACT_SUBSETS = dict(
    default=Default,
    config=Config,
    hardware=Hardware,
    license=License
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main(testing=False):
    module = AnsibleModule(argument_spec=dict(
        gather_subset=dict(required=False, type='list')),
        supports_check_mode=True
    )
    gather_subset = module.params.get('gather_subset')

    warnings = list()
    runable_subsets = set()
    exclude_subsets = set()

    if gather_subset is None:
        gather_subset = set()
        gather_subset.add('default')

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('-'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Subset must be one of [%s], got %s' %
                             (', '.join(VALID_SUBSETS), subset))

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
