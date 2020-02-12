#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_user
version_added: "2.10"
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
short_description: Manage the aggregate of local users on AlliedWare Plus device
description:
    - This module provides declarative management of the local usernames
        configured on network devices. It allows playbooks to manage
        either individual usernames or the aggregate of usernames in the
        current running config. It also supports purging usernames from the
        configuration that are not explicitly defined.
options:
    aggregate:
        description:
            - The set of username objects to be configured on the remote
                AlliedWare Plus device. The list entries can either be the username
                or a hash of username and properties. This argument is mutually
                exclusive with the C(name) argument.
        aliases: ['users', 'collection']
    name:
        description:
            - The username to be configured on the AlliedWare Plus device.
                This argument accepts a string value and is mutually exclusive
                with the C(aggregate) argument.
                Please note that this option is not same as C(provider username).
    configured_password:
        description:
            - The password to be configured on the AlliedWare Plus device. The
                password needs to be provided in clear and it will be encrypted
                on the device.
                Please note that this option is not same as C(provider password).
    hashed_password:
        description:
            - This option allows configuring hashed passwords on AlliedWare Plus device.
        suboptions:
            value:
                description:
                    - The actual hashed password to be configured on the device
                required: True
    privilege:
        description:
            - The C(privilege) argument configures the privilege level of the
                user when logged into the system. This argument accepts integer
                values in the range of 1 to 15.
    purge:
        description:
            - Instructs the module to consider the
                resource definition absolute. It will remove any previously
                configured usernames on the device with the exception of the
                `admin` user (the current defined set of users).
        type: bool
        default: false
    state:
        description:
            - Configures the state of the username definition
                as it relates to the device operational configuration. When set
                to I(present), the username(s) should be configured in the device active
                configuration and when set to I(absent) the username(s) should not be
                in the device active configuration
        default: present
        choices: ['present', 'absent']
notes:
    - Check mode is supported.
"""

EXAMPLES = """
- name: create a new user with configured password
    awplus_user:
        name: ansible
        configured_password: hello
        state: present

- name: purge all users except manager
    awplus_user:
        name: manager
        purge: yes

- name: create a new user with hash password
    awplus_user:
        name: ansible1
        hashed_password:
            value: $1$Xbe4cg43$k7jjFxx8aJBm0oG8fzIc.0

- name: Delete user ansible1
    awplus_user:
        name: ansible1
        state: absent

- name: Delete user ansible with aggregate
    awplus_user:
        aggregate:
            - name: ansible1
            - name: ansible
        state: absent

- name: Change password for user ansible
    awplus_user:
        name: ansible
        configured_password: bye
        state: present

- name: set multiple users to privilege level 15
    awplus_user:
        aggregate:
            - name: chengk
            - name: ansible
        privilege: 15
        state: present
"""

RETURN = """
commands:
    description: Show the commands sent.
    returned: always
    type: list
    sample: ['interface port1.0.5', 'static-channel-group 2 member-filters']
"""

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.basic import AnsibleModule
from functools import partial
from copy import deepcopy
import re


def validate_privilege(value, module):
    if value and not 1 <= value <= 15:
        module.fail_json(
            msg='privilege must be between 1 and 15, got %s' % value)


def user_del_cmd(username):
    return {
        'command': 'no username %s' % username,
        'prompt': 'This operation will remove all username related configurations with same name',
        'answer': 'y',
        'newline': False,
    }


def map_obj_to_commands(updates, module):
    commands = list()

    def needs_update(want, have, x):
        return want.get(x) and (want.get(x) != have.get(x))

    def add(command, want, x):
        command.append('username %s %s' % (want['name'], x))

    def add_hashed_password(command, want, x):
        command.append('username %s password 8 %s' %
                       (want['name'], x.get('value')))

    for update in updates:
        want, have = update

        if want['state'] == 'absent':
            commands.append(user_del_cmd(want['name']))

        if needs_update(want, have, 'privilege'):
            add(commands, want, 'privilege %s' % want['privilege'])

        if needs_update(want, have, 'configured_password'):
            add(commands, want, 'password %s' % (want['configured_password']))

        if needs_update(want, have, 'hashed_password'):
            add_hashed_password(commands, want, want['hashed_password'])

    return commands


def update_objects(want, have):
    updates = list()
    for entry in want:
        item = next((i for i in have if i['name'] == entry['name']), None)
        if all((item is None, entry['state'] == 'present')):
            updates.append((entry, {}))
        elif item:
            for key, value in iteritems(entry):
                if value and value != item[key]:
                    updates.append((entry, item))
    return updates


def parse_privilege(data):
    match = re.search(r'privilege (\S+)', data, re.M)
    if match:
        return int(match.group(1))


def map_config_to_obj(module):
    data = get_config(module, flags=['| include username'])

    match = re.findall(r'(?:^(?:u|\s{2}u))sername (\S+)', data, re.M)
    if not match:
        return list()

    instances = list()

    for user in set(match):
        regex = r'username %s .+$' % user
        cfg = re.findall(regex, data, re.M)
        cfg = '\n'.join(cfg)
        obj = {
            'name': user,
            'state': 'present',
            'configured_password': None,
            'hashed_password': None,
            'privilege': parse_privilege(cfg),
        }
        instances.append(obj)

    return instances


def get_param_value(key, item, module):
    # if key doesn't exist in the item, get it from module.params
    if not item.get(key):
        value = module.params[key]

    # if key does exist, do a type check on it to validate it
    else:
        value_type = module.argument_spec[key].get('type', 'str')
        type_checker = module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
        type_checker(item[key])
        value = item[key]

    # validate the param value (if validator func exists)
    validator = globals().get('validate_%s' % key)
    if all((value, validator)):
        validator(value, module)

    return value


def map_params_to_obj(module):
    users = module.params['aggregate']
    if not users:
        if not module.params['name'] and module.params['purge']:
            return list()
        elif not module.params['name']:
            module.fail_json(msg='username is required')
        else:
            aggregate = [{'name': module.params['name']}]
    else:
        aggregate = list()
        for item in users:
            if not isinstance(item, dict):
                aggregate.append({'name': item})
            elif 'name' not in item:
                module.fail_json(msg='name is required')
            else:
                aggregate.append(item)

    objects = list()

    for item in aggregate:
        get_value = partial(get_param_value, item=item, module=module)
        item['configured_password'] = get_value('configured_password')
        item['hashed_password'] = get_value('hashed_password')
        item['privilege'] = get_value('privilege')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


def main():
    """ main entry point for module execution
    """
    hashed_password_spec = dict(
        value=dict(no_log=True, required=True)
    )

    element_spec = dict(
        name=dict(),
        configured_password=dict(no_log=True),
        hashed_password=dict(no_log=True, type='dict',
                             options=hashed_password_spec),
        privilege=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent'])
    )
    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict',
                       options=aggregate_spec, aliases=['users', 'collection']),
        purge=dict(type='bool', default=False)
    )

    argument_spec.update(element_spec)
    argument_spec.update(awplus_argument_spec)

    mutually_exclusive = [('name', 'aggregate'),
                          ('hashed_password', 'configured_password')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(update_objects(want, have), module)

    if module.params['purge']:
        want_users = [x['name'] for x in want]
        have_users = [x['name'] for x in have]
        for item in set(have_users).difference(want_users):
            if item != 'admin':
                commands.append(user_del_cmd(item))

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
