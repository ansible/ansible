#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: eos_lldp
version_added: "2.5"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage LLDP configuration on Arista EOS network devices
description:
  - This module provides declarative management of LLDP service
    on Arista EOS network devices.
notes:
  - Tested against EOS 4.15
options:
  state:
    description:
      - State of the LLDP configuration. If value is I(present) lldp will be enabled
        else if it is I(absent) it will be disabled.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: Enable LLDP service
  eos_lldp:
    state: present

- name: Disable LLDP service
  eos_lldp:
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - lldp run
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.eos import get_config, load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec


def has_lldp(module):
    config = get_config(module, flags=['| section lldp'])

    is_lldp_enable = False
    if "no lldp run" not in config:
        is_lldp_enable = True

    return is_lldp_enable


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        state=dict(default='present',
                   choices=['present', 'absent',
                            'enabled', 'disabled'])
    )

    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    HAS_LLDP = has_lldp(module)

    commands = []

    if module.params['state'] == 'absent' and HAS_LLDP:
        commands.append('no lldp run')
    elif module.params['state'] == 'present' and not HAS_LLDP:
        commands.append('lldp run')

    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
