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
module: nxos_snmp_community
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP community configs.
description:
    - Manages SNMP community configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
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
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server community TESTING7 group network-operator"]
'''


from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    command = {
        'command': command,
        'output': 'json',
    }

    return run_commands(module, command)


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
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
    data = execute_show_command('show snmp group', module)[0]
    group_list = []

    try:
        group_table = data['TABLE_role']['ROW_role']
        for group in group_table:
            group_list.append(group['role_name'])
    except (KeyError, AttributeError):
        pass

    return group_list


def get_snmp_community(module, find_filter=None):
    data = execute_show_command('show snmp community', module)[0]

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
    except (KeyError, AttributeError, TypeError):
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
    results = {'changed': False, 'commands': [], 'warnings': warnings}

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
        module.fail_json(msg="Group not on switch. Please add before moving forward")

    existing = get_snmp_community(module, community)
    args = dict(group=group, acl=acl)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    delta = dict(set(proposed.items()).difference(existing.items()))

    commands = []

    if state == 'absent':
        if existing:
            command = "no snmp-server community {0}".format(community)
            commands.append(command)
    elif state == 'present':
        if delta:
            command = config_snmp_community(dict(delta), community)
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        results['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)

        if 'configure' in cmds:
            cmds.pop(0)
        results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
