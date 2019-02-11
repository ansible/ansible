#!/usr/bin/python
#
# (c) 2018 Extreme Networks Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: slxos_lldp
version_added: "2.7"
author: "Matthew Stone (@bigmstone)"
short_description: Manage LLDP configuration on Extreme Networks SLX-OS network devices.
description:
  - This module provides declarative management of LLDP service
    on Extreme SLX-OS network devices.
notes:
  - Tested against SLX-OS 17s.1.02
options:
  state:
    description:
      - State of the LLDP configuration. If value is I(present) lldp will be enabled
        else if it is I(absent) it will be disabled.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP service
  slxos_lldp:
    state: present

- name: Disable LLDP service
  slxos_lldp:
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
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.network.slxos.slxos import (
    load_config,
    get_config
)

PROTOCOL = "protocol lldp"


def has_lldp(module):
    config = get_config(module)
    netcfg = CustomNetworkConfig(indent=1, contents=config)
    parents = [PROTOCOL]
    body = netcfg.get_section(parents)

    for line in body.split('\n'):
        l = line.strip()
        match = re.search(r'disable', l, re.M)
        if match:
            return False

    return True


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    HAS_LLDP = has_lldp(module)

    warnings = list()

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    commands = []

    if module.params['state'] == 'absent' and HAS_LLDP:
        commands.append('protocol lldp')
        commands.append('disable')
    elif module.params['state'] == 'present' and not HAS_LLDP:
        commands.append('protocol lldp')
        commands.append('no disable')

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
