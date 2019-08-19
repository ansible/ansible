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


DOCUMENTATION = """
---
module: eos_user
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage the collection of local users on EOS devices
description:
  - This module provides declarative management of the local usernames
    configured on Arista EOS devices.  It allows playbooks to manage
    either individual usernames or the collection of usernames in the
    current running config.  It also supports purging usernames from the
    configuration that are not explicitly defined.
extends_documentation_fragment: eos
notes:
  - Tested against EOS 4.15
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        Arista EOS device.  The list entries can either be the username
        or a hash of username and properties.  This argument is mutually
        exclusive with the C(username) argument.
    aliases: ['users', 'collection']
    version_added: "2.4"
  name:
    description:
      - The username to be configured on the remote Arista EOS
        device.  This argument accepts a stringv value and is mutually
        exclusive with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
    version_added: "2.4"
  configured_password:
    description:
      - The password to be configured on the remote Arista EOS device. The
        password needs to be provided in clear and it will be encrypted
        on the device.
        Please note that this option is not same as C(provider password).
    version_added: "2.4"
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
        user when logged into the system.  This argument accepts integer
        values in the range of 1 to 15.
  role:
    description:
      - Configures the role for the username in the
        device running configuration.  The argument accepts a string value
        defining the role name.  This argument does not check if the role
        has been configured on the device.
  sshkey:
    description:
      - Specifies the SSH public key to configure
        for the given username.  This argument accepts a valid SSH key value.
  nopassword:
    description:
      - Defines the username without assigning
        a password.  This will allow the user to login to the system
        without being authenticated by a password.
    type: bool
  purge:
    description:
      - Instructs the module to consider the
        resource definition absolute.  It will remove any previously
        configured usernames on the device with the exception of the
        `admin` user which cannot be deleted per EOS constraints.
    type: bool
    default: false
  state:
    description:
      - Configures the state of the username definition
        as it relates to the device operational configuration.  When set
        to I(present), the username(s) should be configured in the device active
        configuration and when set to I(absent) the username(s) should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: create a new user
  eos_user:
    name: ansible
    sshkey: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
    state: present

- name: remove all users except admin
  eos_user:
    purge: yes

- name: set multiple users to privilege level 15
  eos_user:
    aggregate:
      - name: netop
      - name: netend
    privilege: 15
    state: present

- name: Change Password for User netop
  eos_user:
    username: netop
    configured_password: "{{ new_password }}"
    update_password: always
    state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - name ansible secret password
    - name admin secret admin
session_name:
  description: The EOS config session name used to load the configuration
  returned: when changed is True
  type: str
  sample: ansible_1479315771
"""

import re

from copy import deepcopy
from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import get_config, load_config
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args
from ansible.module_utils.six import iteritems


def validate_privilege(value, module):
    if not 1 <= value <= 15:
        module.fail_json(msg='privilege must be between 1 and 15, got %s' % value)


def map_obj_to_commands(updates, module):
    commands = list()
    update_password = module.params['update_password']

    for update in updates:
        want, have = update

        def needs_update(x):
            return want.get(x) and (want.get(x) != have.get(x))

        def add(x):
            return commands.append('username %s %s' % (want['name'], x))

        if want['state'] == 'absent':
            commands.append('no username %s' % want['name'])
            continue

        if needs_update('configured_password'):
            if update_password == 'always' or not have:
                add('secret %s' % want['configured_password'])

        if needs_update('role'):
            add('role %s' % want['role'])

        if needs_update('privilege'):
            add('privilege %s' % want['privilege'])

        if needs_update('sshkey'):
            add('sshkey %s' % want['sshkey'])

        if needs_update('nopassword'):
            if want['nopassword']:
                add('nopassword')
            else:
                add('no username %s nopassword' % want['name'])

        if want.get('state') == 'present' and want.get('name'):
            value = [want.get('configured_password'), want.get('nopassword'), want.get('sshkey')]
            if all(v is None for v in value) is True:
                module.fail_json(msg='configured_password, sshkey or nopassword should be provided')

    return commands


def parse_role(data):
    match = re.search(r'role (\S+)', data, re.M)
    if match:
        return match.group(1)


def parse_sshkey(data):
    match = re.search(r'sshkey (.+)$', data, re.M)
    if match:
        return match.group(1)


def parse_privilege(data):
    match = re.search(r'privilege (\S+)', data, re.M)
    if match:
        return int(match.group(1))


def map_config_to_obj(module):
    data = get_config(module, flags=['section username'])

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
            'nopassword': 'nopassword' in cfg,
            'configured_password': None,
            'sshkey': parse_sshkey(cfg),
            'privilege': parse_privilege(cfg),
            'role': parse_role(cfg)
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
        elif not module.params['name']:
            module.fail_json(msg='name is required')
        else:
            collection = [{'name': module.params['name']}]
    else:
        collection = list()
        for item in aggregate:
            if not isinstance(item, dict):
                collection.append({'name': item})
            elif 'name' not in item:
                module.fail_json(msg='name is required')
            else:
                collection.append(item)

    objects = list()

    for item in collection:
        get_value = partial(get_param_value, item=item, module=module)
        item['configured_password'] = get_value('configured_password')
        item['nopassword'] = get_value('nopassword')
        item['privilege'] = get_value('privilege')
        item['role'] = get_value('role')
        item['sshkey'] = get_value('sshkey')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


def update_objects(want, have):
    updates = list()
    for entry in want:
        if 'name' in entry:
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
        role=dict(),

        sshkey=dict(),

        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec, aliases=['collection', 'users']),
        purge=dict(type='bool', default=False)
    )

    argument_spec.update(element_spec)
    argument_spec.update(eos_argument_spec)
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
                commands.append('no username %s' % item)

    result['commands'] = commands

    # the eos cli prevents this by rule so capture it and display
    # a nice failure message
    if 'no username admin' in commands:
        module.fail_json(msg='cannot delete the `admin` account')

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
