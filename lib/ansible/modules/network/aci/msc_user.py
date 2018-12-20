#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: msc_user
short_description: Manage users
description:
- Manage users on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  user_id:
    description:
    - The ID of the user.
    type: str
  user:
    description:
    - The name of the user.
    - Alternative to the name, you can use C(user_id).
    type: str
    required: yes
    aliases: [ name, user_name ]
  user_password:
    description:
    - The password of the user.
    type: str
  first_name:
    description:
    - The first name of the user.
    - This parameter is required when creating new users.
    type: str
  last_name:
    description:
    - The last name of the user.
    - This parameter is required when creating new users.
    type: str
  email:
    description:
    - The email address of the user.
    - This parameter is required when creating new users.
    type: str
  phone:
    description:
    - The phone number of the user.
    - This parameter is required when creating new users.
    type: str
  account_status:
    description:
    - The status of the user account.
    type: str
    choices: [ active ]
  domain:
    description:
    - The domain this user belongs to.
    - When creating new users, this defaults to C(Local).
    type: str
  roles:
    description:
    - The roles for this user.
    type: list
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
notes:
- A default installation of ACI Multi-Site ships with admin password 'we1come!' which requires a password change on first login.
  See the examples of how to change the 'admin' password using Ansible.
extends_documentation_fragment: msc
'''

EXAMPLES = r'''
- name: Update initial admin password
  msc_user:
    host: msc_host
    username: admin
    password: we1come!
    user_name: admin
    user_password: SomeSecretPassword
    state: present
  delegate_to: localhost

- name: Add a new user
  msc_user:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    user_name: dag
    description: Test user
    first_name: Dag
    last_name: Wieers
    email: dag@wieers.com
    phone: +32 478 436 299
    state: present
  delegate_to: localhost

- name: Remove a user
  msc_user:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    user_name: dag
    state: absent
  delegate_to: localhost

- name: Query a user
  msc_user:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    user_name: dag
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all users
  msc_user:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.msc import MSCModule, msc_argument_spec, issubset


def main():
    argument_spec = msc_argument_spec()
    argument_spec.update(
        user_id=dict(type='str', required=False),
        user=dict(type='str', required=False, aliases=['name', 'user_name']),
        user_password=dict(type='str', no_log=True),
        first_name=dict(type='str'),
        last_name=dict(type='str'),
        email=dict(type='str'),
        phone=dict(type='str'),
        # TODO: What possible options do we have ?
        account_status=dict(type='str', choices=['active']),
        domain=dict(type='str'),
        roles=dict(type='list'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['user_name']],
            ['state', 'present', ['user_name']],
        ],
    )

    user_id = module.params['user_id']
    user_name = module.params['user']
    user_password = module.params['user_password']
    first_name = module.params['first_name']
    last_name = module.params['last_name']
    email = module.params['email']
    phone = module.params['phone']
    account_status = module.params['account_status']
    state = module.params['state']

    msc = MSCModule(module)

    roles = msc.lookup_roles(module.params['roles'])
    domain = msc.lookup_domain(module.params['domain'])

    path = 'users'

    # Query for existing object(s)
    if user_id is None and user_name is None:
        msc.existing = msc.query_objs(path)
    elif user_id is None:
        msc.existing = msc.get_obj(path, username=user_name)
        if msc.existing:
            user_id = msc.existing['id']
    elif user_name is None:
        msc.existing = msc.get_obj(path, id=user_id)
    else:
        msc.existing = msc.get_obj(path, id=user_id)
        existing_by_name = msc.get_obj(path, username=user_name)
        if existing_by_name and user_id != existing_by_name['id']:
            msc.fail_json(msg="Provided user '{0}' with id '{1}' does not match existing id '{2}'.".format(user_name, user_id, existing_by_name['id']))

    # If we found an existing object, continue with it
    if user_id:
        path = 'users/{id}'.format(id=user_id)

    if state == 'query':
        pass

    elif state == 'absent':
        msc.previous = msc.existing
        if msc.existing:
            if module.check_mode:
                msc.existing = {}
            else:
                msc.existing = msc.request(path, method='DELETE')

    elif state == 'present':
        msc.previous = msc.existing

        payload = dict(
            id=user_id,
            username=user_name,
            password=user_password,
            firstName=first_name,
            lastName=last_name,
            emailAddress=email,
            phoneNumber=phone,
            accountStatus=account_status,
            domainId=domain,
            roles=roles,
            # active=True,
            # remote=True,
        )

        msc.sanitize(payload, collate=True)

        if msc.sent.get('accountStatus') is None:
            msc.sent['accountStatus'] = 'active'

        if msc.existing:
            if not issubset(msc.sent, msc.existing):
                # NOTE: Since MSC always returns '******' as password, we need to assume a change
                if 'password' in msc.proposed:
                    msc.module.warn("A password change is assumed, as the MSC REST API does not return passwords we do not know.")
                    msc.result['changed'] = True

                if module.check_mode:
                    msc.existing = msc.proposed
                else:
                    msc.existing = msc.request(path, method='PUT', data=msc.sent)
        else:
            if module.check_mode:
                msc.existing = msc.proposed
            else:
                msc.existing = msc.request(path, method='POST', data=msc.sent)

    msc.exit_json()


if __name__ == "__main__":
    main()
