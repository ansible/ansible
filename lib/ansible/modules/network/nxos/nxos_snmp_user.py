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
module: nxos_snmp_user
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP users for monitoring.
description:
    - Manages SNMP user configuration.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Authentication parameters not idempotent.
options:
    user:
        description:
            - Name of the user.
        required: true
    group:
        description:
            - Group to which the user will belong to.
              If state = present, and the user is existing,
              the group is added to the user. If the user
              is not existing, user entry is created with this
              group argument.
              If state = absent, only the group is removed from the
              user entry. However, to maintain backward compatibility,
              if the existing user belongs to only one group, and if
              group argument is same as the existing user's group,
              then the user entry also is deleted.
    authentication:
        description:
            - Authentication parameters for the user.
        choices: ['md5', 'sha']
    pwd:
        description:
            - Authentication password when using md5 or sha.
              This is not idempotent
    privacy:
        description:
            - Privacy password for the user.
              This is not idempotent
    encrypt:
        description:
            - Enables AES-128 bit encryption when using privacy password.
        type: bool
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_snmp_user:
    user: ntc
    group: network-operator
    authentication: md5
    pwd: test_password
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server user ntc network-operator auth md5 test_password"]
'''

import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module, text=False):
    command = {
        'command': command,
        'output': 'json',
    }
    if text:
        command['output'] = 'text'

    return run_commands(module, command)


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
        return group_list

    return group_list


def get_snmp_user(user, module):
    command = 'show snmp user {0}'.format(user)
    body = execute_show_command(command, module, text=True)
    body_text = body[0]

    if 'No such entry' not in body[0]:
        body = execute_show_command(command, module)

    resource = {}
    try:
        # The TABLE and ROW keys differ between NXOS platforms.
        if body[0].get('TABLE_snmp_user'):
            tablekey = 'TABLE_snmp_user'
            rowkey = 'ROW_snmp_user'
            tablegrpkey = 'TABLE_snmp_group_names'
            rowgrpkey = 'ROW_snmp_group_names'
            authkey = 'auth_protocol'
            privkey = 'priv_protocol'
            grpkey = 'group_names'
        elif body[0].get('TABLE_snmp_users'):
            tablekey = 'TABLE_snmp_users'
            rowkey = 'ROW_snmp_users'
            tablegrpkey = 'TABLE_groups'
            rowgrpkey = 'ROW_groups'
            authkey = 'auth'
            privkey = 'priv'
            grpkey = 'group'

        rt = body[0][tablekey][rowkey]
        # on some older platforms, all groups except the 1st one
        # are in list elements by themselves and they are
        # indexed by 'user'. This is due to a platform bug.
        # Get first element if rt is a list due to the bug
        # or if there is no bug, parse rt directly
        if isinstance(rt, list):
            resource_table = rt[0]
        else:
            resource_table = rt

        resource['user'] = user
        resource['authentication'] = str(resource_table[authkey]).strip()
        encrypt = str(resource_table[privkey]).strip()
        if encrypt.startswith('aes'):
            resource['encrypt'] = 'aes-128'
        else:
            resource['encrypt'] = 'none'

        groups = []
        if tablegrpkey in resource_table:
            group_table = resource_table[tablegrpkey][rowgrpkey]
            try:
                for group in group_table:
                    groups.append(str(group[grpkey]).strip())
            except TypeError:
                groups.append(str(group_table[grpkey]).strip())

            # Now for the platform bug case, get the groups
            if isinstance(rt, list):
                # remove 1st element from the list as this is parsed already
                rt.pop(0)
                # iterate through other elements indexed by
                # 'user' and add it to groups.
                for each in rt:
                    groups.append(each['user'].strip())

        # Some 'F' platforms use 'group' key instead
        elif 'group' in resource_table:
            # single group is a string, multiple groups in a list
            groups = resource_table['group']
            if isinstance(groups, str):
                groups = [groups]

        resource['group'] = groups

    except (KeyError, AttributeError, IndexError, TypeError):
        if not resource and body_text and 'No such entry' not in body_text:
            # 6K and other platforms may not return structured output;
            # attempt to get state from text output
            resource = get_non_structured_snmp_user(body_text)

    return resource


def get_non_structured_snmp_user(body_text):
    # This method is a workaround for platforms that don't support structured
    # output for 'show snmp user <foo>'. This workaround may not work on all
    # platforms. Sample non-struct output:
    #
    # User                Auth  Priv(enforce) Groups              acl_filter
    # ____                ____  _____________ ______              __________
    # sample1             no    no            network-admin       ipv4:my_acl
    #                                         network-operator
    #                                         priv-11
    #         -OR-
    # sample2             md5   des(no)       priv-15
    #         -OR-
    # sample3             md5   aes-128(no)   network-admin
    resource = {}
    output = body_text.rsplit('__________')[-1]
    pat = re.compile(r'^(?P<user>\S+)\s+'
                     r'(?P<auth>\S+)\s+'
                     r'(?P<priv>[\w\d-]+)(?P<enforce>\([\w\d-]+\))*\s+'
                     r'(?P<group>\S+)',
                     re.M)
    m = re.search(pat, output)
    if not m:
        return resource
    resource['user'] = m.group('user')
    resource['auth'] = m.group('auth')
    resource['encrypt'] = 'aes-128' if 'aes' in str(m.group('priv')) else 'none'

    resource['group'] = [m.group('group')]
    more_groups = re.findall(r'^\s+([\w\d-]+)\s*$', output, re.M)
    if more_groups:
        resource['group'] += more_groups

    return resource


def remove_snmp_user(user, group=None):
    if group:
        return ['no snmp-server user {0} {1}'.format(user, group)]
    else:
        return ['no snmp-server user {0}'.format(user)]


def config_snmp_user(proposed, user, reset):
    if reset:
        commands = remove_snmp_user(user)
    else:
        commands = []

    if proposed.get('group'):
        cmd = 'snmp-server user {0} {group}'.format(user, **proposed)
    else:
        cmd = 'snmp-server user {0}'.format(user)

    auth = proposed.get('authentication', None)
    pwd = proposed.get('pwd', None)

    if auth and pwd:
        cmd += ' auth {authentication} {pwd}'.format(**proposed)

    encrypt = proposed.get('encrypt', None)
    privacy = proposed.get('privacy', None)

    if encrypt and privacy:
        cmd += ' priv {encrypt} {privacy}'.format(**proposed)
    elif privacy:
        cmd += ' priv {privacy}'.format(**proposed)

    if cmd:
        commands.append(cmd)

    return commands


def main():
    argument_spec = dict(
        user=dict(required=True, type='str'),
        group=dict(type='str'),
        pwd=dict(type='str', no_log=True),
        privacy=dict(type='str'),
        authentication=dict(choices=['md5', 'sha']),
        encrypt=dict(type='bool'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['authentication', 'pwd'],
                                              ['encrypt', 'privacy']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    user = module.params['user']
    group = module.params['group']
    pwd = module.params['pwd']
    privacy = module.params['privacy']
    encrypt = module.params['encrypt']
    authentication = module.params['authentication']
    state = module.params['state']

    if privacy and encrypt:
        if not pwd and authentication:
            module.fail_json(msg='pwd and authentication must be provided '
                                 'when using privacy and encrypt')

    if group and group not in get_snmp_groups(module):
        module.fail_json(msg='group not configured yet on switch.')

    existing = get_snmp_user(user, module)

    if state == 'present' and existing:
        if group:
            if group not in existing['group']:
                existing['group'] = None
            else:
                existing['group'] = group
        else:
            existing['group'] = None

    commands = []

    if state == 'absent' and existing:
        if group:
            if group in existing['group']:
                if len(existing['group']) == 1:
                    commands.append(remove_snmp_user(user))
                else:
                    commands.append(remove_snmp_user(user, group))
        else:
            commands.append(remove_snmp_user(user))

    elif state == 'present':
        reset = False

        args = dict(user=user, pwd=pwd, group=group, privacy=privacy,
                    encrypt=encrypt, authentication=authentication)
        proposed = dict((k, v) for k, v in args.items() if v is not None)

        if not existing:
            if encrypt:
                proposed['encrypt'] = 'aes-128'
            commands.append(config_snmp_user(proposed, user, reset))

        elif existing:
            if encrypt and not existing['encrypt'].startswith('aes'):
                reset = True
                proposed['encrypt'] = 'aes-128'

            delta = dict(set(proposed.items()).difference(existing.items()))

            if delta.get('pwd'):
                delta['authentication'] = authentication

            if delta and encrypt:
                delta['encrypt'] = 'aes-128'

            if delta:
                command = config_snmp_user(delta, user, reset)
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
