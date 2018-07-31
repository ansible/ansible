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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ios_user
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage the aggregate of local users on Cisco IOS device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the aggregate of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
notes:
  - Tested against IOS 15.6
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        Cisco IOS device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument.
    aliases: ['users', 'collection']
  name:
    description:
      - The username to be configured on the Cisco IOS device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
  configured_password:
    description:
      - The password to be configured on the Cisco IOS device. The
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
  privilege:
    description:
      - The C(privilege) argument configures the privilege level of the
        user when logged into the system. This argument accepts integer
        values in the range of 1 to 15.
  view:
    description:
      - Configures the view for the username in the
        device running configuration. The argument accepts a string value
        defining the view name. This argument does not check if the view
        has been configured on the device.
    aliases: ['role']
  sshkey:
    description:
      - Specifies the SSH public key to configure
        for the given username.  This argument accepts a valid SSH key value.
    version_added: "2.6"
  nopassword:
    description:
      - Defines the username without assigning
        a password. This will allow the user to login to the system
        without being authenticated by a password.
    type: bool
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
extends_documentation_fragment: ios
"""

EXAMPLES = """
- name: create a new user
  ios_user:
    name: ansible
    nopassword: True
    sshkey: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
    state: present

- name: remove all users except admin
  ios_user:
    purge: yes

- name: set multiple users to privilege level 15
  ios_user:
    aggregate:
      - name: netop
      - name: netend
    privilege: 15
    state: present

- name: set user view/role
  ios_user:
    name: netop
    view: network-operator
    state: present

- name: Change Password for User netop
  ios_user:
    name: netop
    configured_password: "{{ new_password }}"
    update_password: always
    state: present

- name: Aggregate of users
  ios_user:
    aggregate:
      - name: ansibletest2
      - name: ansibletest3
    view: network-admin

- name: Delete users with aggregate
  ios_user:
    aggregate:
      - name: ansibletest1
      - name: ansibletest2
      - name: ansibletest3
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - username ansible secret password
    - username admin secret admin
"""
from copy import deepcopy

import re
import json
import base64
import hashlib

from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.ios.ios import get_config, load_config
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args


def validate_privilege(value, module):
    if value and not 1 <= value <= 15:
        module.fail_json(msg='privilege must be between 1 and 15, got %s' % value)


def user_del_cmd(username):
    return {
        'command': 'no username %s' % username,
        'prompt': 'This operation will remove all username related configurations with same name',
        'answer': 'y',
        'newline': False,
    }


def sshkey_fingerprint(sshkey):
    # IOS will accept a MD5 fingerprint of the public key
    # and is easier to configure in a single line
    # we calculate this fingerprint here
    if not sshkey:
        return None
    if ' ' in sshkey:
        # ssh-rsa AAA...== comment
        keyparts = sshkey.split(' ')
        keyparts[1] = hashlib.md5(base64.b64decode(keyparts[1])).hexdigest().upper()
        return ' '.join(keyparts)
    else:
        # just the key, assume rsa type
        return 'ssh-rsa %s' % hashlib.md5(base64.b64decode(sshkey)).hexdigest().upper()


def map_obj_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    update_password = module.params['update_password']

    def needs_update(want, have, x):
        return want.get(x) and (want.get(x) != have.get(x))

    def add(command, want, x):
        command.append('username %s %s' % (want['name'], x))

    def add_ssh(command, want, x=None):
        command.append('ip ssh pubkey-chain')
        command.append(' no username %s' % want['name'])
        if x:
            command.append(' username %s' % want['name'])
            command.append('  key-hash %s' % x)
            command.append('  exit')
        command.append(' exit')

    for update in updates:
        want, have = update

        if want['state'] == 'absent':
            commands.append(user_del_cmd(want['name']))
            add_ssh(commands, want)
            continue

        if needs_update(want, have, 'view'):
            add(commands, want, 'view %s' % want['view'])

        if needs_update(want, have, 'privilege'):
            add(commands, want, 'privilege %s' % want['privilege'])

        if needs_update(want, have, 'sshkey'):
            add_ssh(commands, want, want['sshkey'])

        if needs_update(want, have, 'configured_password'):
            if update_password == 'always' or not have:
                add(commands, want, 'secret %s' % want['configured_password'])

        if needs_update(want, have, 'nopassword'):
            if want['nopassword']:
                add(commands, want, 'nopassword')
            else:
                add(commands, want, user_del_cmd(want['name']))

    return commands


def parse_view(data):
    match = re.search(r'view (\S+)', data, re.M)
    if match:
        return match.group(1)


def parse_sshkey(data):
    match = re.search(r'key-hash (\S+ \S+(?: .+)?)$', data, re.M)
    if match:
        return match.group(1)


def parse_privilege(data):
    match = re.search(r'privilege (\S+)', data, re.M)
    if match:
        return int(match.group(1))


def map_config_to_obj(module):
    data = get_config(module, flags=['| section username'])

    match = re.findall(r'^username (\S+)', data, re.M)
    if not match:
        return list()

    instances = list()

    for user in set(match):
        regex = r'username %s .+$' % user
        cfg = re.findall(regex, data, re.M)
        cfg = '\n'.join(cfg)
        sshregex = r'username %s\n\s+key-hash .+$' % user
        sshcfg = re.findall(sshregex, data, re.M)
        sshcfg = '\n'.join(sshcfg)
        obj = {
            'name': user,
            'state': 'present',
            'nopassword': 'nopassword' in cfg,
            'configured_password': None,
            'sshkey': parse_sshkey(sshcfg),
            'privilege': parse_privilege(cfg),
            'view': parse_view(cfg)
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
        item['nopassword'] = get_value('nopassword')
        item['privilege'] = get_value('privilege')
        item['view'] = get_value('view')
        item['sshkey'] = sshkey_fingerprint(get_value('sshkey'))
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
    element_spec = dict(
        name=dict(),

        configured_password=dict(no_log=True),
        nopassword=dict(type='bool'),
        update_password=dict(default='always', choices=['on_create', 'always']),

        privilege=dict(type='int'),
        view=dict(aliases=['role']),

        sshkey=dict(),

        state=dict(default='present', choices=['present', 'absent'])
    )
    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec, aliases=['users', 'collection']),
        purge=dict(type='bool', default=False)
    )

    argument_spec.update(element_spec)
    argument_spec.update(ios_argument_spec)

    mutually_exclusive = [('name', 'aggregate')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    if module.params['password'] and not module.params['configured_password']:
        warnings.append(
            'The "password" argument is used to authenticate the current connection. ' +
            'To set a user password use "configured_password" instead.'
        )

    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

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

    # the ios cli prevents this by rule so capture it and display
    # a nice failure message
    for cmd in commands:
        if 'no username admin' in cmd:
            module.fail_json(msg='cannot delete the `admin` account')

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
