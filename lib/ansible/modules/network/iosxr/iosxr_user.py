#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: iosxr_user
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage the collection of local users on Cisco IOS XR device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the collection of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
options:
  users:
    description:
      - The set of username objects to be configured on the remote
        Cisco IOS XR device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument, alias C(collection).
  name:
    description:
      - The username to be configured on the Cisco IOS XR device.
        This argument accepts a string value and is mutually exclusive
        with the C(collection) argument.
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

import re

from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.six import iteritems
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def map_obj_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    update_password = module.params['update_password']

    def needs_update(want, have, x):
        return want.get(x) and (want.get(x) != have.get(x))

    def add(command, want, x):
        command.append('username %s %s' % (want['name'], x))

    for update in updates:
        want, have = update

        if want['state'] == 'absent':
            commands.append('no username %s' % want['name'])
            continue

        if needs_update(want, have, 'group'):
            add(commands, want, 'group %s' % want['group'])

        if needs_update(want, have, 'password'):
            if update_password == 'always' or not have:
                add(commands, want, 'secret %s' % want['password'])

    return commands


def parse_group(data):
    match = re.search(r'\n group (\S+)', data, re.M)
    if match:
        return match.group(1)


def map_config_to_obj(module):
    data = get_config(module, flags=['username'])

    match = re.findall(r'^username (\S+)', data, re.M)
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
            'password': None,
            'group': parse_group(cfg)
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
            collection = [{'name': module.params['name']}]
    else:
        collection = list()
        for item in users:
            if not isinstance(item, dict):
                collection.append({'name': item})
            elif 'name' not in item:
                module.fail_json(msg='name is required')
            else:
                collection.append(item)

    objects = list()

    for item in collection:
        get_value = partial(get_param_value, item=item, module=module)
        item['password'] = get_value('password')
        item['group'] = get_value('group')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


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


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        users=dict(type='list', aliases=['collection']),
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

    commands = map_obj_to_commands(update_objects(want, have), module)

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
