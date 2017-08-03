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
    required: False
    default: null
  name:
    description:
      - The C(name) argument defines the username of the user to be created
        on the system.  This argument must follow appropriate usernaming
        conventions for the target device running JUNOS.  This argument is
        mutually exclusive with the C(aggregate) argument.
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
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    choices: [True, False]
    version_added: "2.4"
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
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
  type: string
  sample: >
          [edit system login]
          +    user test-user {
          +        uid 2005;
          +        class read-only;
          +    }
"""
from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import commit_configuration, discard_changes
from ansible.module_utils.junos import load_config, locked_config
from ansible.module_utils.six import iteritems

try:
    from lxml.etree import Element, SubElement, tostring
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring

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
            if item['active']:
                user.set('active', 'active')
            else:
                user.set('inactive', 'inactive')

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
        role=dict(choices=ROLES, default='unauthorized'),
        sshkey=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        active=dict(default=True, type='bool')
    )

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=element_spec, aliases=['collection', 'users']),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['aggregate', 'name']]
    mutually_exclusive = [['aggregate', 'name'],
                          ['aggregate', 'full_name'],
                          ['aggregate', 'sshkey'],
                          ['aggregate', 'state'],
                          ['aggregate', 'active']]

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    ele = map_obj_to_ele(want)

    kwargs = {}
    if module.params['purge']:
        kwargs['action'] = 'replace'

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, **kwargs)

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
