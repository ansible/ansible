#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2019 IBM CORPORATION
# Author(s): Tzur Eliya <tzure@il.ibm.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibm_sa_users
short_description: Handle users on IBM Spectrum Accelerate Family storage systems.
version_added: "2.9"

description:
    - "This module manages users on IBM Spectrum Accelerate Family storage systems."

options:
    user:
        description:
            - User name.
        required: true
    state:
        description:
            - User desired state.
        required: true
        default: "present"
        choices: [ "present", "absent" ]
    domain:
        description:
            - Domain to add the user to.
        required: false
    category:
        description:
            - User desired category for storage management.
        choices: ["applicationadmin", "readonly", "securityadmin", "storageadmin", "storageintegrationadmin"]
        required: false
    user_pass:
        description:
            - user password. Not to be confused with the regular 'password' field, for the endpoint credentials.
        required: false

extends_documentation_fragment:
    - ibm_storage

author:
    - Tzur Eliya (@tzure)
'''

EXAMPLES = '''
- name: Define a new user on the storage array and add to a domain.
  ibm_sa_users:
    user: user_name
    user_pass: pass
    state: present
    category: storageintegrationadmin
    domain: test_domain
    username: admin
    password: secret
    endpoints: hostdev-system

- name: Delete an existing user from the storage array, regardless if it is a member of a domain.
  ibm_sa_users:
    user: user_name
    state: absent
    username: admin
    password: secret
    endpoints: hostdev-system
'''
RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ibm_sa_utils import execute_pyxcli_command, \
    connect_ssl, spectrum_accelerate_spec, is_pyxcli_installed


def main():
    argument_spec = spectrum_accelerate_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            user=dict(required=True),
            domain=dict(),
            category=dict(choices=['applicationadmin', 'readonly',
                                   'securityadmin', 'storageadmin',
                                   'storageintegrationadmin']),
            user_pass=dict(no_log=True)
        )
    )

    module = AnsibleModule(argument_spec)

    is_pyxcli_installed(module)

    xcli_client = connect_ssl(module)
    # required args
    user = xcli_client.cmd.user_list(user=module.params.get('user')).as_single_element

    state = module.params['state']
    if state == 'present':
        module.params.pop('password')
        module.params['password'] = module.params.get('user_pass')
        module.params['password_verify'] = module.params.get('user_pass')
        module.params.pop('user_pass')
    state_changed = False
    if state == 'present' and not user:
        state_changed = execute_pyxcli_command(
            module, 'user_define', xcli_client, user_module=True)
    elif state == 'absent' and user:
        state_changed = execute_pyxcli_command(module, 'user_delete', xcli_client)

    module.exit_json(changed=state_changed)


if __name__ == '__main__':
    main()
