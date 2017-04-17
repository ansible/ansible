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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_snmp_community
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP community configs.
description:
    - Manages SNMP community configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
options:
    community:
        description:
            - Case-sensitive community string.
        required: true
    access:
        description:
            - Access type for community.
        required: false
        default: null
        choices: ['ro','rw']
    group:
        description:
            - Group to which the community belongs.
        required: false
        default: null
    acl:
        description:
            - ACL name to filter snmp requests.
        required: false
        default: 1
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure snmp community is configured
- nxos_snmp_community:
    community: TESTING7
    group: network-operator
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "network-operator"}
existing:
    description: k/v pairs of existing snmp community
    returned: always
    type: dict
    sample:  {}
end_state:
    description: k/v pairs of snmp community after module execution
    returned: always
    type: dict
    sample:  {"acl": "None", "group": "network-operator"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server community TESTING7 group network-operator"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


import re
import re


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = run_commands(module, cmds)

    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_snmp_groups(module):
    command = 'show snmp group'
    data = execute_show_command(command, module)[0]

    group_list = []

    try:
        group_table = data['TABLE_role']['ROW_role']
        for group in group_table:
            group_list.append(group['role_name'])
    except (KeyError, AttributeError):
        return group_list

    return group_list


def get_snmp_community(module, find_filter=None):
    command = 'show snmp community'
    data = execute_show_command(command, module)[0]

    community_dict = {}

    community_map = {
        'grouporaccess': 'group',
        'aclfilter': 'acl'
    }

    try:
        community_table = data['TABLE_snmp_community']['ROW_snmp_community']
        for each in community_table:
            community = apply_key_map(community_map, each)
            key = each['community_name']
            community_dict[key] = community
    except (KeyError, AttributeError):
        return community_dict

    if find_filter:
        find = community_dict.get(find_filter, None)

    if find_filter is None or find is None:
        return {}
    else:
        fix_find = {}
        for (key, value) in find.items():
            if isinstance(value, str):
                fix_find[key] = value.strip()
            else:
                fix_find[key] = value
        return fix_find


def config_snmp_community(delta, community):
    CMDS = {
        'group': 'snmp-server community {0} group {group}',
        'acl': 'snmp-server community {0} use-acl {acl}'
    }
    commands = []
    for k, v in delta.items():
        cmd = CMDS.get(k).format(community, **delta)
        if cmd:
            commands.append(cmd)
            cmd = None
    return commands


def main():
    argument_spec = dict(
        community=dict(required=True, type='str'),
        access=dict(choices=['ro', 'rw']),
        group=dict(type='str'),
        acl=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                required_one_of=[['access', 'group']],
                                mutually_exclusive=[['access', 'group']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    access = module.params['access']
    group = module.params['group']
    community = module.params['community']
    acl = module.params['acl']
    state = module.params['state']

    if access:
        if access == 'ro':
            group = 'network-operator'
        elif access == 'rw':
            group = 'network-admin'

    # group check - ensure group being configured exists on the device
    configured_groups = get_snmp_groups(module)

    if group not in configured_groups:
        module.fail_json(msg="group not on switch."
                             "please add before moving forward")

    existing = get_snmp_community(module, community)
    args = dict(group=group, acl=acl)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    delta = dict(set(proposed.items()).difference(existing.items()))

    changed = False
    end_state = existing
    commands = []

    if state == 'absent':
        if existing:
            command = "no snmp-server community {0}".format(community)
            commands.append(command)
        cmds = flatten_list(commands)
    elif state == 'present':
        if delta:
            command = config_snmp_community(dict(delta), community)
            commands.append(command)
        cmds = flatten_list(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_snmp_community(module, community)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == '__main__':
    main()

