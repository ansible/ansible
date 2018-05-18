#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vr_user
short_description: Manages users on Vultr.
description:
  - Create, update and remove users.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the user
    required: true
  email:
    description:
      - Email of the user.
      - Required if C(state=present).
  password:
    description:
      - Password of the user.
      - Only considered while creating a user or when C(force=yes).
  force:
    description:
      - Password will only be changed with enforcement.
    default: no
    type: bool
  api_enabled:
    description:
      - Whether the API is enabled or not.
    default: yes
    type: bool
  acls:
    description:
      - List of ACLs this users should have, see U(https://www.vultr.com/api/#user_user_list).
      - Required if C(state=present).
      - One or more of the choices list, some depend on each other.
    choices:
      - manage_users
      - subscriptions
      - provisioning
      - billing
      - support
      - abuse
      - dns
      - upgrade
  state:
    description:
      - State of the user.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Ensure a user exists
  local_action:
    module: vr_user
    name: john
    email: john.doe@example.com
    password: s3cr3t
    acls:
      - upgrade
      - dns
      - manage_users
      - subscriptions
      - upgrade

- name: Remove a user
  local_action:
    module: vr_user
    name: john
    state: absent
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: string
      sample: "https://api.vultr.com"
vultr_user:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: ID of the user.
      returned: success
      type: string
      sample: 5904bc6ed9234
    api_key:
      description: API key of the user.
      returned: only after resource was created
      type: string
      sample: 567E6K567E6K567E6K567E6K567E6K
    name:
      description: Name of the user.
      returned: success
      type: string
      sample: john
    email:
      description: Email of the user.
      returned: success
      type: string
      sample: "john@exmaple.com"
    api_enabled:
      description: Whether the API is enabled or not.
      returned: success
      type: bool
      sample: true
    acls:
      description: List of ACLs of the user.
      returned: success
      type: list
      sample: [manage_users, support, upgrade]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


ACLS = [
    'manage_users',
    'subscriptions',
    'provisioning',
    'billing',
    'support',
    'abuse',
    'dns',
    'upgrade',
]


class AnsibleVultrUser(Vultr):

    def __init__(self, module):
        super(AnsibleVultrUser, self).__init__(module, "vultr_user")

        self.returns = {
            'USERID': dict(key='id'),
            'name': dict(),
            'email': dict(),
            'api_enabled': dict(convert_to='bool'),
            'acls': dict(),
            'api_key': dict()
        }

    def _common_args(self):
        return {
            'name': self.module.params.get('name'),
            'email': self.module.params.get('email'),
            'acls': self.module.params.get('acls'),
            'password': self.module.params.get('password'),
            'api_enabled': self.get_yes_or_no('api_enabled'),
        }

    def get_user(self):
        users = self.api_query(path="/v1/user/list")
        for user in users or []:
            if user.get('name') == self.module.params.get('name'):
                return user
        return {}

    def present_user(self):
        # Choices with list
        acls = self.module.params.get('acls')
        for acl in acls or []:
            if acl not in ACLS:
                self.fail_json(msg='value of acls must be one or more of: %s, got: %s' % (ACLS, acls))

        user = self.get_user()
        if not user:
            user = self._create_user(user)
        else:
            user = self._update_user(user)
        return user

    def _has_changed(self, user, data):
        for k, v in data.items():
            if k not in user:
                continue
            elif isinstance(v, list):
                for i in v:
                    if i not in user[k]:
                        return True
            elif data[k] != user[k]:
                return True
        return False

    def _create_user(self, user):
        self.module.fail_on_missing_params(required_params=['password'])

        self.result['changed'] = True

        data = self._common_args()
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            user = self.api_query(
                path="/v1/user/create",
                method="POST",
                data=data
            )
            user.update(self.get_user())
        return user

    def _update_user(self, user):
        data = self._common_args()
        data.update({
            'USERID': user['USERID'],
        })

        force = self.module.params.get('force')
        if not force:
            del data['password']

        if force or self._has_changed(user=user, data=data):
            self.result['changed'] = True

            self.result['diff']['before'] = user
            self.result['diff']['after'] = user.copy()
            self.result['diff']['after'].update(data)

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/user/update",
                    method="POST",
                    data=data
                )
                user = self.get_user()
        return user

    def absent_user(self):
        user = self.get_user()
        if user:
            self.result['changed'] = True

            data = {
                'USERID': user['USERID'],
            }

            self.result['diff']['before'] = user
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/user/delete",
                    method="POST",
                    data=data
                )
        return user


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        email=dict(),
        password=dict(no_log=True),
        force=dict(type='bool', default=False),
        api_enabled=dict(type='bool', default=True),
        acls=dict(type='list', aliases=['acl']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['email', 'acls']),
        ],
        supports_check_mode=True,
    )

    vr_user = AnsibleVultrUser(module)
    if module.params.get('state') == "absent":
        user = vr_user.absent_user()
    else:
        user = vr_user.present_user()

    result = vr_user.get_result(user)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
