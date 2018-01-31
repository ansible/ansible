#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_aaa_user
short_description: Manage AAA users (aaa:User)
description:
- Manage AAA users.
- More information from the internal APIC class I(aaa:User) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.5'
options:
  aaa_password:
    description:
    - The AAA user password.
#  aaa_password_lifetime:
#    description:
#    - The lifetime of the locally-authenticated user password.
#  aaa_password_update_required:
#    description:
#    - Whether this account needs password update.
  aaa_user:
    description:
    - The name of the user to add.
    aliases: [ name, user ]
  email:
    description:
    - The email address of the locally-authenticated user.
  enabled:
    description:
    - The status of the locally-authenticated user account.
  expiration:
    description:
    - The expiration date of the locally-authenticated user account.
  expires:
    description:
    - Whether to enable an expiration date for the locally-authenticated user account.
  first_name:
    description:
    - The first name of the locally-authenticated user.
  last_name:
    description:
    - The last name of the locally-authenticated user.
  phone:
    description:
    - The phone number of the locally-authenticated user.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    aaa_password: AnotherSecretPassword
    expiration: never
    expires: no
    email: dag@wieers.com
    phone: 1-234-555-678
    first_name: Dag
    last_name: Wieers
    state: present

- name: Remove a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    state: absent

- name: Query a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    state: query

- name: Query all users
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r''' # '''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        aaa_password=dict(type='str', no_log=True),
        aaa_user=dict(type='str', required=True),
        description=dict(type='str', aliases=['descr']),
        email=dict(type='str'),
        enabled=dict(type='bool'),
        expiration=dict(type='str'),
        expires=dict(type='bool'),
        first_name=dict(type='str'),
        last_name=dict(type='str'),
        phone=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['aaa_user']],
            ['state', 'present', ['aaa_user']],
            ['expires', True, ['expiration']],
        ],
    )

    aaa_password = module.params['aaa_password']
    aaa_user = module.params['aaa_user']
    description = module.params['description']
    email = module.params['email']
    enabled = module.params['enabled']
    expiration = module.params['expiration']
    expires = module.params['expires']
    first_name = module.params['first_name']
    last_name = module.params['last_name']
    phone = module.params['phone']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='aaaUser',
            aci_rn='userext/user-' + aaa_user,
            filter_target='eq(aaaUser.name, "{0}")'.format(aaa_user),
            module_object=aaa_user,
        ),
    )
    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class='aaaUser',
            class_config=dict(
                accountStatus='inactive' if enabled is False else 'active',
                clearPwdHistory='no' if aaa_password is None else 'yes',  # Required if password is set :-/
                email=email,
                expiration=expiration,
                expires='yes' if expires is True and expiration else 'no',
                firstName=first_name,
                lastName=last_name,
                name=aaa_user,
                phone=phone,
                pwd=aaa_password,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='aaaUser')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
