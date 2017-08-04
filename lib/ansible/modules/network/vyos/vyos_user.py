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
module: vyos_user
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage the collection of local users on VyOS device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the collection of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        VyOS device. The list entries can either be the username or
        a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument. alias C(users).
  name:
    description:
      - The username to be configured on the VyOS device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
  full_name:
    description:
      - The C(full_name) argument provides the full name of the user
        account to be created on the remote device. This argument accepts
        any text string value.
  password:
    description:
      - The password to be configured on the VyOS device. The
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
  level:
    description:
      - The C(level) argument configures the level of the user when logged
        into the system. This argument accepts string values admin or operator.
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
  vyos_user:
    name: ansible
    password: password
    state: present
- name: remove all users except admin
  vyos_user:
    purge: yes
- name: set multiple users to level operator
  vyos_user:
    users:
      - name: netop
      - name: netend
    level: operator
    state: present
- name: Change Password for User netop
  vyos_user:
    name: netop
    password: "{{ new_password }}"
    update_password: always
    state: present
- name: Add aggregate of users
  vyos_user:
    aggregate:
      - { name: ansibletest2, level: operator }
      - { name: ansibletest3, level: operator }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - set system login user test level operator
    - set system login user authentication plaintext-password password
"""

import re

from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vyos import get_config, load_config
from ansible.module_utils.six import iteritems
from ansible.module_utils.vyos import vyos_argument_spec, check_args


def validate_level(value, module):
    if value not in ('admin', 'operator'):
        module.fail_json(msg='level must be either admin or operator, got %s' % value)


def spec_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    update_password = module.params['update_password']

    def needs_update(want, have, x):
        return want.get(x) and (want.get(x) != have.get(x))

    def add(command, want, x):
        command.append('set system login user %s %s' % (want['name'], x))

    for update in updates:
        want, have = update

        if want['state'] == 'absent':
            commands.append('delete system login user %s' % want['name'])
            continue

        if needs_update(want, have, 'level'):
            add(commands, want, "level %s" % want['level'])

        if needs_update(want, have, 'full_name'):
            add(commands, want, "full-name %s" % want['full_name'])

        if needs_update(want, have, 'password'):
            if update_password == 'always' or not have:
                add(commands, want, 'authentication plaintext-password %s' % want['password'])

    return commands


def parse_level(data):
    match = re.search(r'level (\S+)', data, re.M)
    if match:
        level = match.group(1)[1:-1]
        return level


def parse_full_name(data):
    match = re.search(r'full-name (\S+)', data, re.M)
    if match:
        full_name = match.group(1)[1:-1]
        return full_name


def config_to_dict(module):
    data = get_config(module)

    match = re.findall(r'^set system login user (\S+)', data, re.M)
    if not match:
        return list()

    instances = list()

    for user in set(match):
        regex = r' %s .+$' % user
        cfg = re.findall(regex, data, re.M)
        cfg = '\n'.join(cfg)
        obj = {
            'name': user,
            'state': 'present',
            'password': None,
            'level': parse_level(cfg),
            'full_name': parse_full_name(cfg)
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
    aggregate = module.params['aggregate']
    if not aggregate:
        if not module.params['name'] and module.params['purge']:
            return list()
        else:
            aggregate = [{'name': module.params['name']}]

    objects = list()
    for item in aggregate:
        get_value = partial(get_param_value, item=item, module=module)
        item['password'] = get_value('password')
        item['full_name'] = get_value('full_name')
        item['level'] = get_value('level')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


def update_objects(want, have):
    updates = list()
    for entry in want:
        item = next((i for i in have if i['name'] == entry['name']), None)
        if item is None:
            updates.append((entry, {}))
        elif item:
            for key, value in iteritems(entry):
                if value and value != item[key]:
                    updates.append((entry, item))
    return updates


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        full_name=dict(),
        level=dict(aliases=['role']),
        password=dict(no_log=True),
        update_password=dict(default='always', choices=['on_create', 'always']),
        state=dict(default='present', choices=['present', 'absent'])
    )

    required_one_of = [['aggregate', 'name']]
    mutually_exclusive = [['name', 'aggregate'],
                          ['full_name', 'aggregate'],
                          ['level', 'aggregate'],
                          ['password', 'aggregate'],
                          ['update_password', 'aggregate'],
                          ['state', 'aggregate']]

    aggregate_spec = element_spec.copy()
    aggregate_spec['name'] = dict(required=True)

    argument_spec = dict(
        aggregate=dict(type='list',  aliases=['users'], elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(vyos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = config_to_dict(module)
    commands = spec_to_commands(update_objects(want, have), module)

    if module.params['purge']:
        want_users = [x['name'] for x in want]
        have_users = [x['name'] for x in have]
        for item in set(have_users).difference(want_users):
            commands.append('delete system login user %s' % item)

    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
