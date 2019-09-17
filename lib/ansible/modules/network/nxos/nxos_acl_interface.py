#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_acl_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages applying ACLs to interfaces.
description:
  - Manages applying ACLs to interfaces.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
options:
  name:
    description:
      - Case sensitive name of the access list (ACL).
    required: true
  interface:
    description:
      - Full name of interface, e.g. I(Ethernet1/1).
    required: true
  direction:
    description:
      - Direction ACL to be applied in on the interface.
    required: true
    choices: ['ingress', 'egress']
  state:
    description:
      - Specify desired state of the resource.
    required: false
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
- name: apply egress acl to ethernet1/41
  nxos_acl_interface:
    name: ANSIBLE
    interface: ethernet1/41
    direction: egress
    state: present
'''

RETURN = '''
acl_applied_to:
    description: list of interfaces the ACL is applied to
    returned: always
    type: list
    sample: [{"acl_type": "Router ACL", "direction": "egress",
            "interface": "Ethernet1/41", "name": "ANSIBLE"}]
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/41", "ip access-group ANSIBLE out"]
'''
import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def check_for_acl_int_present(module, name, intf, direction):
    # Need to Capitalize the interface name as the nxos
    # output has capitalization
    command = [{
        'command': 'show running-config aclmgr | section {0}'.format(intf.title()),
        'output': 'text',
    }]
    body = run_commands(module, command)

    if direction == 'ingress':
        mdir = 'in'
    elif direction == 'egress':
        mdir = 'out'

    match = re.search('ip access-group {0} {1}'.format(name, mdir), str(body[0]))
    return bool(match)


def apply_acl(proposed):
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


def remove_acl(proposed):
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    argument_spec = dict(
        name=dict(required=False, type='str'),
        interface=dict(required=True),
        direction=dict(required=True, choices=['egress', 'ingress']),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    results = dict(changed=False, warnings=warnings)

    state = module.params['state']
    name = module.params['name']
    interface = module.params['interface'].lower()
    direction = module.params['direction'].lower()

    proposed = dict(name=name, interface=interface, direction=direction)

    existing = check_for_acl_int_present(module, name, interface, direction)

    cmds = []
    commands = []
    if state == 'present':
        if not existing:
            command = apply_acl(proposed)
            if command:
                commands.append(command)

    elif state == 'absent':
        if existing:
            command = remove_acl(proposed)
            if command:
                commands.append(command)

    if commands:
        cmds = flatten_list(commands)
        if cmds:
            if module.check_mode:
                module.exit_json(changed=True, commands=cmds)
            else:
                load_config(module, cmds)
                results['changed'] = True
                if 'configure' in cmds:
                    cmds.pop(0)
    else:
        cmds = []

    results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
