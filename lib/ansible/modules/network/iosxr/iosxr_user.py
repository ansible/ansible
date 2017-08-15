#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: iosxr_user
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage the aggregate of local users on Cisco IOS XR device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the aggregate of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
options:
  users:
    description:
      - The set of username objects to be configured on the remote
        Cisco IOS XR device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument, alias C(aggregate).
  name:
    description:
      - The username to be configured on the Cisco IOS XR device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
  password:
    description:
      - The password to be configured on the Cisco IOS XR device. The
        password needs to be provided in clear and it will be encrypted
        on the device.
        Please note that this option is not same as C(provider password).
  update_password:
    description:
      - Since passwords are encrypted in the device running config, this
        argument will instruct the module when to change the password.  When
        set to C(always), the password will always be updated in the device
        and when set to C(on_create) the password will be updated only if
        the username is created.
    default: always
    choices: ['on_create', 'always']
  group:
    description:
      - Configures the group for the username in the
        device running configuration. The argument accepts a string value
        defining the group name. This argument does not check if the group
        has been configured on the device, alias C(role).
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
"""

EXAMPLES = """
- name: create a new user
  iosxr_user:
    name: ansible
    password: test
    state: present
- name: remove all users except admin
  iosxr_user:
    purge: yes
- name: set multiple users to group sys-admin
  iosxr_user:
    users:
      - name: netop
      - name: netend
    group: sysadmin
    state: present
- name: Change Password for User netop
  iosxr_user:
    name: netop
    password: "{{ new_password }}"
    update_password: always
    state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - username ansible secret password group sysadmin
    - username admin secret admin
"""

from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        name = w['name']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent' and obj_in_have:
            commands.append('no username ' + name)
        elif state == 'present' and not obj_in_have:
            user_cmd = 'username ' + name
            commands.append(user_cmd)

            if w['password']:
                commands.append(user_cmd + ' secret ' + w['password'])
            if w['group']:
                commands.append(user_cmd + ' group ' + w['group'])

        elif state == 'present' and obj_in_have:
            user_cmd = 'username ' + name

            if module.params['update_password'] == 'always' and w['password']:
                commands.append(user_cmd + ' secret ' + w['password'])
            if w['group'] and w['group'] != obj_in_have['group']:
                commands.append(user_cmd + ' group ' + w['group'])

    return commands


def map_config_to_obj(module):
    data = get_config(module, flags=['username'])
    users = data.strip().rstrip('!').split('!')

    if not users:
        return list()

    instances = list()

    for user in users:
        user_config = user.strip().splitlines()

        name = user_config[0].strip().split()[1]
        group = None

        if len(user_config) > 1:
            group_or_secret = user_config[1].strip().split()
            if group_or_secret[0] == 'group':
                group = group_or_secret[1]

        obj = {
            'name': name,
            'state': 'present',
            'password': None,
            'group': group
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
    users = module.params['users']
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
        item['password'] = get_value('password')
        item['group'] = get_value('group')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        users=dict(type='list', aliases=['aggregate']),
        name=dict(),

        password=dict(no_log=True),
        update_password=dict(default='always', choices=['on_create', 'always']),

        group=dict(aliases=['role']),

        purge=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(iosxr_argument_spec)
    mutually_exclusive = [('name', 'users')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)

    if module.params['purge']:
        want_users = [x['name'] for x in want]
        have_users = [x['name'] for x in have]
        for item in set(have_users).difference(want_users):
            if item != 'admin':
                commands.append('no username %s' % item)

    result['commands'] = commands
    result['warnings'] = warnings

    if 'no username admin' in commands:
        module.fail_json(msg='cannot delete the `admin` account')

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
