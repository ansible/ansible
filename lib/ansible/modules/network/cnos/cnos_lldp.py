#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo.
# (c) 2017, Ansible by Red Hat, inc
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
# Module to work on Link Aggregation with Lenovo Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_lldp
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage LLDP configuration on Lenovo CNOS network devices.
description:
  - This module provides declarative management of LLDP service
    on Lenovc CNOS network devices.
notes:
  - Tested against CNOS 10.9.1
options:
  state:
    description:
      - State of the LLDP configuration. If value is I(present) lldp will be
         enabled else if it is I(absent) it will be disabled.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP service
  cnos_lldp:
    state: present

- name: Disable LLDP service
  cnos_lldp:
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to
            manage the device.
  type: list
  sample:
    - lldp timer 1024
    - lldp trap-interval 330
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils.network.cnos.cnos import debugOutput, run_commands
from ansible.module_utils.connection import exec_command


def get_ethernet_range(module):
    output = run_commands(module, ['show interface brief'])[0].split('\n')
    maxport = None
    last_interface = None
    for line in output:
        if line.startswith('Ethernet1/'):
            last_interface = line.split(' ')[0]
    if last_interface is not None:
        eths = last_interface.split('/')
        maxport = eths[1]
    return maxport


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    warnings = list()
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    maxport = get_ethernet_range(module)
    commands = []
    prime_cmd = 'interface ethernet 1/1-' + maxport

    if module.params['state'] == 'absent':
        commands.append(prime_cmd)
        commands.append('no lldp receive')
        commands.append('no lldp transmit')
        commands.append('exit')
        commands.append('interface mgmt 0')
        commands.append('no lldp receive')
        commands.append('no lldp transmit')
        commands.append('exit')
    elif module.params['state'] == 'present':
        commands.append(prime_cmd)
        commands.append('lldp receive')
        commands.append('lldp transmit')
        commands.append('exit')
        commands.append('interface mgmt 0')
        commands.append('lldp receive')
        commands.append('lldp transmit')
        commands.append('exit')

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
