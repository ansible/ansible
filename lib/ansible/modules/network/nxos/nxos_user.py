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
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: nxos_user
extends_documentation_fragment: nxos
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage the collection of local users on Nexus devices
description:
  - This module provides declarative management of the local usernames
    configured on Cisco Nexus devices.  It allows playbooks to manage
    either individual usernames or the collection of usernames in the
    current running config.  It also supports purging usernames from the
    configuration that are not explicitly defined.
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        Cisco Nexus device.  The list entries can either be the username
        or a hash of username and properties.  This argument is mutually
        exclusive with the C(name) argument.
    version_added: "2.4"
    required: false
    default: null
  name:
    description:
      - The username to be configured on the remote Cisco Nexus
        device.  This argument accepts a stringv value and is mutually
        exclusive with the C(aggregate) argument.
    required: false
    default: null
  update_password:
    description:
      - Since passwords are encrypted in the device running config, this
        argument will instruct the module when to change the password.  When
        set to C(always), the password will always be updated in the device
        and when set to C(on_create) the password will be updated only if
        the username is created.
    required: false
    default: always
    choices: ['on_create', 'always']
  role:
    description:
      - The C(role) argument configures the role for the username in the
        device running configuration.  The argument accepts a string value
        defining the role name.  This argument does not check if the role
        has been configured on the device.
    required: false
    default: null
  sshkey:
    description:
      - The C(sshkey) argument defines the SSH public key to configure
        for the username.  This argument accepts a valid SSH key value.
    required: false
    default: null
  purge:
    description:
      - The C(purge) argument instructs the module to consider the
        resource definition absolute.  It will remove any previously
        configured usernames on the device with the exception of the
        `admin` user which cannot be deleted per nxos constraints.
    required: false
    default: false
  state:
    description:
      - The C(state) argument configures the state of the username definition
        as it relates to the device operational configuration.  When set
        to I(present), the username(s) should be configured in the device active
        configuration and when set to I(absent) the username(s) should not be
        in the device active configuration
    required: false
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: create a new user
  nxos_user:
    name: ansible
    sshkey: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
    state: present

- name: remove all users except admin
  nxos_user:
    purge: yes

- name: set multiple users role
  aggregate:
    - name: netop
    - name: netend
  role: network-operator
  state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - name ansible
    - name ansible password password
start:
  description: The time the job started
  returned: always
  type: str
  sample: "2016-11-16 10:38:15.126146"
end:
  description: The time the job ended
  returned: always
  type: str
  sample: "2016-11-16 10:38:25.595612"
delta:
  description: The time elapsed to perform all operations
  returned: always
  type: str
  sample: "0:00:10.469466"
"""
import re

from functools import partial

from ansible.module_utils.nxos import run_commands, load_config
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types, iteritems
from ansible.module_utils.network_common import to_list

VALID_ROLES = ['network-admin', 'network-operator', 'vdc-admin', 'vdc-operator',
               'priv-15', 'priv-14', 'priv-13', 'priv-12', 'priv-11', 'priv-10',
               'priv-9', 'priv-8', 'priv-7', 'priv-6', 'priv-5', 'priv-4',
               'priv-3', 'priv-2', 'priv-1', 'priv-0']


def validate_roles(value, module):
    for item in value:
        if item not in VALID_ROLES:
            module.fail_json(msg='invalid role specified')

def map_obj_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    update_password = module.params['update_password']

    for update in updates:
        want, have = update

        needs_update = lambda x: want.get(x) and (want.get(x) != have.get(x))
        add = lambda x: commands.append('username %s %s' % (want['name'], x))
        remove = lambda x: commands.append('no username %s %s' % (want['name'], x))

        if want['state'] == 'absent':
            commands.append('no username %s' % want['name'])
            continue

        if want['state'] == 'present' and not have:
            commands.append('username %s' % want['name'])

        if needs_update('password'):
            if update_password == 'always' or not have:
                add('password %s' % want['password'])

        if needs_update('sshkey'):
            add('sshkey %s' % want['sshkey'])


        if want['roles']:
            if have:
                for item in set(have['roles']).difference(want['roles']):
                    remove('role %s' % item)

                for item in set(want['roles']).difference(have['roles']):
                    add('role %s' % item)
            else:
                for item in want['roles']:
                    add('role %s' % item)


    return commands

def parse_password(data):
    if not data.get('remote_login'):
        return '<PASSWORD>'

def parse_roles(data):
    configured_roles = data.get('TABLE_role')['ROW_role']
    roles = list()
    if configured_roles:
        for item in to_list(configured_roles):
            roles.append(item['role'])
    return roles

def map_config_to_obj(module):
    out = run_commands(module, ['show user-account | json'])
    data = out[0]

    objects = list()

    for item in to_list(data['TABLE_template']['ROW_template']):
        objects.append({
            'name': item['usr_name'],
            'password': parse_password(item),
            'sshkey': item.get('sshkey_info'),
            'roles': parse_roles(item),
            'state': 'present'
        })
    return objects

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

    return value

def map_params_to_obj(module):
    aggregate = module.params['aggregate']
    if not aggregate:
        if not module.params['name'] and module.params['purge']:
            return list()
        elif not module.params['name']:
            module.fail_json(msg='username is required')
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
        item.update({
            'password': get_value('password'),
            'sshkey': get_value('sshkey'),
            'roles': get_value('roles'),
            'state': get_value('state')
        })

        for key, value in iteritems(item):
            if value:
                # validate the param value (if validator func exists)
                validator = globals().get('validate_%s' % key)
                if all((value, validator)):
                    validator(value, module)

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
        aggregate=dict(type='list', no_log=True, aliases=['collection', 'users']),
        name=dict(),

        password=dict(no_log=True),
        update_password=dict(default='always', choices=['on_create', 'always']),

        roles=dict(type='list', aliases=['role']),

        sshkey=dict(),

        purge=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(nxos_argument_spec)

    mutually_exclusive = [('name', 'aggregate')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)


    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
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

    # the nxos cli prevents this by rule so capture it and display
    # a nice failure message
    if 'no username admin' in commands:
        module.fail_json(msg='cannot delete the `admin` account')

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
