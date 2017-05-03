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
module: junos_user
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage local user accounts on Juniper JUNOS devices
description:
  - This module manages locally configured user accounts on remote
    network devices running the JUNOS operating system.  It provides
    a set of arguments for creating, removing and updating locally
    defined accounts
extends_documentation_fragment: junos
options:
  users:
    description:
      - The C(users) argument defines a list of users to be configured
        on the remote device.  The list of users will be compared against
        the current users and only changes will be added or removed from
        the device configuration.  This argument is mutually exclusive with
        the name argument.
    required: False
    default: null
  name:
    description:
      - The C(name) argument defines the username of the user to be created
        on the system.  This argument must follow appropriate usernaming
        conventions for the target device running JUNOS.  This argument is
        mutually exclusive with the C(users) argument.
    required: false
    default: null
  full_name:
    description:
      - The C(full_name) argument provides the full name of the user
        account to be created on the remote device.  This argument accepts
        any text string value.
    required: false
    default: null
  role:
    description:
      - The C(role) argument defines the role of the user account on the
        remote system.  User accounts can have more than one role
        configured.
    required: false
    default: read-only
    choices: ['operator', 'read-only', 'super-user', 'unauthorized']
  sshkey:
    description:
      - The C(sshkey) argument defines the public SSH key to be configured
        for the user account on the remote system.  This argument must
        be a valid SSH key
    required: false
    default: null
  purge:
    description:
      - The C(purge) argument instructs the module to consider the
        users definition absolute.  It will remove any previously configured
        users on the device with the exception of the current defined
        set of users.
    required: false
    default: false
  state:
    description:
      - The C(state) argument configures the state of the user definitions
        as it relates to the device operational configuration.  When set
        to I(present), the user should be configured in the device active
        configuration and when set to I(absent) the user should not be
        in the device active configuration
    required: false
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: create new user account
  junos_user:
    name: ansible
    role: super-user
    sshkey: "{{ lookup('file', '~/.ssh/ansible.pub') }}"
    state: present

- name: remove a user account
  junos_user:
    name: ansible
    state: absent

- name: remove all user accounts except ansible
  junos_user:
    name: ansible
    purge: yes
"""

RETURN = """
"""
from functools import partial

from xml.etree.ElementTree import Element, SubElement, tostring

from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import load_config
from ansible.module_utils.six import iteritems

ROLES = ['operator', 'read-only', 'super-user', 'unauthorized']
USE_PERSISTENT_CONNECTION = True


def map_obj_to_ele(want):
    element = Element('system')
    login = SubElement(element, 'login', {'replace': 'replace'})

    for item in want:
        if item['state'] != 'present':
            operation = 'delete'
        else:
            operation = 'replace'

        user = SubElement(login, 'user', {'operation': operation})

        SubElement(user, 'name').text = item['name']

        if operation == 'replace':
            SubElement(user, 'class').text = item['role']

            if item.get('full_name'):
                SubElement(user, 'full-name').text = item['full_name']

            if item.get('sshkey'):
                auth = SubElement(user, 'authentication')
                ssh_rsa = SubElement(auth, 'ssh-rsa')
                key = SubElement(ssh_rsa, 'name').text = item['sshkey']

    return element


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
            module.fail_json(msg='missing required argument: name')
        else:
            collection = [{'name': module.params['name']}]
    else:
        collection = list()
        for item in users:
            if not isinstance(item, dict):
                collection.append({'username': item})
            elif 'name' not in item:
                module.fail_json(msg='missing required argument: name')
            else:
                collection.append(item)

    objects = list()

    for item in collection:
        get_value = partial(get_param_value, item=item, module=module)
        item.update({
            'full_name': get_value('full_name'),
            'role': get_value('role'),
            'sshkey': get_value('sshkey'),
            'state': get_value('state')
        })

        for key, value in iteritems(item):
            # validate the param value (if validator func exists)
            validator = globals().get('validate_%s' % key)
            if all((value, validator)):
                validator(value, module)

        objects.append(item)

    return objects


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        users=dict(type='list'),
        name=dict(),

        full_name=dict(),
        role=dict(choices=ROLES, default='unauthorized'),
        sshkey=dict(),

        purge=dict(type='bool'),

        state=dict(choices=['present', 'absent'], default='present')
    )

    mutually_exclusive = [('users', 'name')]

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    ele = map_obj_to_ele(want)

    kwargs = {'commit': not module.check_mode}
    if module.params['purge']:
        kwargs['action'] = 'replace'

    diff = load_config(module, tostring(ele), warnings, **kwargs)

    if diff:
        result.update({
            'changed': True,
            'diff': {'prepared': diff}
        })

    module.exit_json(**result)

if __name__ == "__main__":
    main()
