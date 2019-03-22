#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


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
  aggregate:
    description:
      - The C(aggregate) argument defines a list of users to be configured
        on the remote device.  The list of users will be compared against
        the current users and only changes will be added or removed from
        the device configuration.  This argument is mutually exclusive with
        the name argument.
    version_added: "2.4"
    aliases: ['users', 'collection']
  name:
    description:
      - The C(name) argument defines the username of the user to be created
        on the system.  This argument must follow appropriate usernaming
        conventions for the target device running JUNOS.  This argument is
        mutually exclusive with the C(aggregate) argument.
  full_name:
    description:
      - The C(full_name) argument provides the full name of the user
        account to be created on the remote device.  This argument accepts
        any text string value.
  role:
    description:
      - The C(role) argument defines the role of the user account on the
        remote system.  User accounts can have more than one role
        configured.
    choices: ['operator', 'read-only', 'super-user', 'unauthorized']
  sshkey:
    description:
      - The C(sshkey) argument defines the public SSH key to be configured
        for the user account on the remote system.  This argument must
        be a valid SSH key
  encrypted_password:
    description:
      - The C(encrypted_password) argument set already hashed password
        for the user account on the remote system.
    version_added: "2.8"
  purge:
    description:
      - The C(purge) argument instructs the module to consider the
        users definition absolute.  It will remove any previously configured
        users on the device with the exception of the current defined
        set of aggregate.
    type: bool
    default: 'no'
  state:
    description:
      - The C(state) argument configures the state of the user definitions
        as it relates to the device operational configuration.  When set
        to I(present), the user should be configured in the device active
        configuration and when set to I(absent) the user should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    type: bool
    default: 'yes'
    version_added: "2.4"
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
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
    aggregate:
    - name: ansible
    purge: yes

- name: set user password
  junos_user:
    name: ansible
    role: super-user
    encrypted_password: "{{ 'my-password' | password_hash('sha512') }}"
    state: present

- name: Create list of users
  junos_user:
    aggregate:
      - {name: test_user1, full_name: test_user2, role: operator, state: present}
      - {name: test_user2, full_name: test_user2, role: read-only, state: present}

- name: Delete list of users
  junos_user:
    aggregate:
      - {name: test_user1, full_name: test_user2, role: operator, state: absent}
      - {name: test_user2, full_name: test_user2, role: read-only, state: absent}
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: str
  sample: >
          [edit system login]
          +    user test-user {
          +        uid 2005;
          +        class read-only;
          +    }
"""
from functools import partial

from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.junos.junos import junos_argument_spec, get_connection, tostring
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes
from ansible.module_utils.network.junos.junos import load_config, locked_config
from ansible.module_utils.six import iteritems

try:
    from lxml.etree import Element, SubElement
except ImportError:
    from xml.etree.ElementTree import Element, SubElement

ROLES = ['operator', 'read-only', 'super-user', 'unauthorized']
USE_PERSISTENT_CONNECTION = True


def handle_purge(module, want):
    want_users = [item['name'] for item in want]
    element = Element('system')
    login = SubElement(element, 'login')

    conn = get_connection(module)
    try:
        reply = conn.execute_rpc(tostring(Element('get-configuration')), ignore_warning=False)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    users = reply.xpath('configuration/system/login/user/name')
    if users:
        for item in users:
            name = item.text
            if name not in want_users and name != 'root':
                user = SubElement(login, 'user', {'operation': 'delete'})
                SubElement(user, 'name').text = name
    if element.xpath('/system/login/user/name'):
        return element


def map_obj_to_ele(module, want):
    element = Element('system')
    login = SubElement(element, 'login')

    for item in want:
        if item['state'] != 'present':
            if item['name'] == 'root':
                module.fail_json(msg="cannot delete the 'root' account.")
            operation = 'delete'
        else:
            operation = 'merge'

        if item['name'] != 'root':
            user = SubElement(login, 'user', {'operation': operation})
            SubElement(user, 'name').text = item['name']
        else:
            user = auth = SubElement(element, 'root-authentication', {'operation': operation})

        if operation == 'merge':
            if item['name'] == 'root' and (not item['active'] or item['role'] or item['full_name']):
                module.fail_json(msg="'root' account cannot be deactivated or be assigned a role and a full name")

            if item['active']:
                user.set('active', 'active')
            else:
                user.set('inactive', 'inactive')

            if item['role']:
                SubElement(user, 'class').text = item['role']

            if item.get('full_name'):
                SubElement(user, 'full-name').text = item['full_name']

            if item.get('sshkey'):
                if 'auth' not in locals():
                    auth = SubElement(user, 'authentication')
                if 'ssh-rsa' in item['sshkey']:
                    ssh_rsa = SubElement(auth, 'ssh-rsa')
                elif 'ssh-dss' in item['sshkey']:
                    ssh_rsa = SubElement(auth, 'ssh-dsa')
                elif 'ecdsa-sha2' in item['sshkey']:
                    ssh_rsa = SubElement(auth, 'ssh-ecdsa')
                elif 'ssh-ed25519' in item['sshkey']:
                    ssh_rsa = SubElement(auth, 'ssh-ed25519')
                key = SubElement(ssh_rsa, 'name').text = item['sshkey']

            if item.get('encrypted_password'):
                if 'auth' not in locals():
                    auth = SubElement(user, 'authentication')
                SubElement(auth, 'encrypted-password').text = item['encrypted_password']

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
    aggregate = module.params['aggregate']
    if not aggregate:
        if not module.params['name'] and module.params['purge']:
            return list()
        elif not module.params['name']:
            module.fail_json(msg='missing required argument: name')
        else:
            collection = [{'name': module.params['name']}]
    else:
        collection = list()
        for item in aggregate:
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
            'encrypted_password': get_value('encrypted_password'),
            'sshkey': get_value('sshkey'),
            'state': get_value('state'),
            'active': get_value('active')
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
    element_spec = dict(
        name=dict(),
        full_name=dict(),
        role=dict(choices=ROLES),
        encrypted_password=dict(),
        sshkey=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        active=dict(type='bool', default=True)
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec, aliases=['collection', 'users']),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    mutually_exclusive = [['aggregate', 'name']]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    ele = map_obj_to_ele(module, want)

    purge_request = None
    if module.params['purge']:
        purge_request = handle_purge(module, want)

    with locked_config(module):
        if purge_request:
            load_config(module, tostring(purge_request), warnings, action='replace')
        diff = load_config(module, tostring(ele), warnings, action='merge')

        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    module.exit_json(**result)


if __name__ == "__main__":
    main()
