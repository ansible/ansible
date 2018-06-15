#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_user
short_description: Manages users on Apache CloudStack based clouds.
description:
    - Create, update, disable, lock, enable and remove users.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  username:
    description:
      - Username of the user.
    required: true
  account:
    description:
      - Account the user will be created under.
      - Required on C(state=present).
  password:
    description:
      - Password of the user to be created.
      - Required on C(state=present).
      - Only considered on creation and will not be updated if user exists.
  first_name:
    description:
      - First name of the user.
      - Required on C(state=present).
  last_name:
    description:
      - Last name of the user.
      - Required on C(state=present).
  email:
    description:
      - Email of the user.
      - Required on C(state=present).
  timezone:
    description:
      - Timezone of the user.
  keys_registered:
    description:
      - If API keys of the user should be generated.
      - "Note: Keys can not be removed by the API again."
    version_added: "2.4"
    type: bool
    default: no
  domain:
    description:
      - Domain the user is related to.
    default: ROOT
  state:
    description:
      - State of the user.
      - C(unlocked) is an alias for C(enabled).
    default: present
    choices: [ present, absent, enabled, disabled, locked, unlocked ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create an user in domain 'CUSTOMERS'
  local_action:
    module: cs_user
    account: developers
    username: johndoe
    password: S3Cur3
    last_name: Doe
    first_name: John
    email: john.doe@example.com
    domain: CUSTOMERS

- name: Lock an existing user in domain 'CUSTOMERS'
  local_action:
    module: cs_user
    username: johndoe
    domain: CUSTOMERS
    state: locked

- name: Disable an existing user in domain 'CUSTOMERS'
  local_action:
    module: cs_user
    username: johndoe
    domain: CUSTOMERS
    state: disabled

- name: Enable/unlock an existing user in domain 'CUSTOMERS'
  local_action:
    module: cs_user
    username: johndoe
    domain: CUSTOMERS
    state: enabled

- name: Remove an user in domain 'CUSTOMERS'
  local_action:
    module: cs_user
    name: customer_xy
    domain: CUSTOMERS
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the user.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
username:
  description: Username of the user.
  returned: success
  type: string
  sample: johndoe
fist_name:
  description: First name of the user.
  returned: success
  type: string
  sample: John
last_name:
  description: Last name of the user.
  returned: success
  type: string
  sample: Doe
email:
  description: Emailof the user.
  returned: success
  type: string
  sample: john.doe@example.com
user_api_key:
  description: API key of the user.
  returned: success
  type: string
  sample: JLhcg8VWi8DoFqL2sSLZMXmGojcLnFrOBTipvBHJjySODcV4mCOo29W2duzPv5cALaZnXj5QxDx3xQfaQt3DKg
user_api_secret:
  description: API secret of the user.
  returned: success
  type: string
  sample: FUELo3LB9fa1UopjTLPdqLv_6OXQMJZv9g9N4B_Ao3HFz8d6IGFCV9MbPFNM8mwz00wbMevja1DoUNDvI8C9-g
account:
  description: Account name of the user.
  returned: success
  type: string
  sample: developers
account_type:
  description: Type of the account.
  returned: success
  type: string
  sample: user
timezone:
  description: Timezone of the user.
  returned: success
  type: string
  sample: enabled
created:
  description: Date the user was created.
  returned: success
  type: string
  sample: Doe
state:
  description: State of the user.
  returned: success
  type: string
  sample: enabled
domain:
  description: Domain the user is related.
  returned: success
  type: string
  sample: ROOT
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackUser(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackUser, self).__init__(module)
        self.returns = {
            'username': 'username',
            'firstname': 'first_name',
            'lastname': 'last_name',
            'email': 'email',
            'secretkey': 'user_api_secret',
            'apikey': 'user_api_key',
            'timezone': 'timezone',
        }
        self.account_types = {
            'user': 0,
            'root_admin': 1,
            'domain_admin': 2,
        }
        self.user = None

    def get_account_type(self):
        account_type = self.module.params.get('account_type')
        return self.account_types[account_type]

    def get_user(self):
        if not self.user:
            args = {
                'domainid': self.get_domain('id'),
                'fetch_list': True,
            }

            users = self.query_api('listUsers', **args)

            if users:
                user_name = self.module.params.get('username')
                for u in users:
                    if user_name.lower() == u['username'].lower():
                        self.user = u
                        break
        return self.user

    def enable_user(self):
        user = self.get_user()
        if not user:
            user = self.present_user()

        if user['state'].lower() != 'enabled':
            self.result['changed'] = True
            args = {
                'id': user['id'],
            }
            if not self.module.check_mode:
                res = self.query_api('enableUser', **args)
                user = res['user']
        return user

    def lock_user(self):
        user = self.get_user()
        if not user:
            user = self.present_user()

        # we need to enable the user to lock it.
        if user['state'].lower() == 'disabled':
            user = self.enable_user()

        if user['state'].lower() != 'locked':
            self.result['changed'] = True

            args = {
                'id': user['id'],
            }

            if not self.module.check_mode:
                res = self.query_api('lockUser', **args)
                user = res['user']

        return user

    def disable_user(self):
        user = self.get_user()
        if not user:
            user = self.present_user()

        if user['state'].lower() != 'disabled':
            self.result['changed'] = True
            args = {
                'id': user['id'],
            }
            if not self.module.check_mode:
                user = self.query_api('disableUser', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    user = self.poll_job(user, 'user')
        return user

    def present_user(self):
        required_params = [
            'account',
            'email',
            'password',
            'first_name',
            'last_name',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        user = self.get_user()
        if user:
            user = self._update_user(user)
        else:
            user = self._create_user(user)
        return user

    def _get_common_args(self):
        return {
            'firstname': self.module.params.get('first_name'),
            'lastname': self.module.params.get('last_name'),
            'email': self.module.params.get('email'),
            'timezone': self.module.params.get('timezone'),
        }

    def _create_user(self, user):
        self.result['changed'] = True

        args = self._get_common_args()
        args.update({
            'account': self.get_account(key='name'),
            'domainid': self.get_domain('id'),
            'username': self.module.params.get('username'),
            'password': self.module.params.get('password'),
        })

        if not self.module.check_mode:
            res = self.query_api('createUser', **args)
            user = res['user']

            # register user api keys
            if self.module.params.get('keys_registered'):
                res = self.query_api('registerUserKeys', id=user['id'])
                user.update(res['userkeys'])

        return user

    def _update_user(self, user):
        args = self._get_common_args()
        args.update({
            'id': user['id'],
        })

        if self.has_changed(args, user):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateUser', **args)

                user = res['user']

        # register user api keys
        if 'apikey' not in user and self.module.params.get('keys_registered'):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('registerUserKeys', id=user['id'])
                user.update(res['userkeys'])
        return user

    def absent_user(self):
        user = self.get_user()
        if user:
            self.result['changed'] = True

            if not self.module.check_mode:
                self.query_api('deleteUser', id=user['id'])

        return user

    def get_result(self, user):
        super(AnsibleCloudStackUser, self).get_result(user)
        if user:
            if 'accounttype' in user:
                for key, value in self.account_types.items():
                    if value == user['accounttype']:
                        self.result['account_type'] = key
                        break

            # secretkey has been removed since CloudStack 4.10 from listUsers API
            if self.module.params.get('keys_registered') and 'apikey' in user and 'secretkey' not in user:
                user_keys = self.query_api('getUserKeys', id=user['id'])
                if user_keys:
                    self.result['user_api_secret'] = user_keys['userkeys'].get('secretkey')

        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        username=dict(required=True),
        account=dict(),
        state=dict(choices=['present', 'absent', 'enabled', 'disabled', 'locked', 'unlocked'], default='present'),
        domain=dict(default='ROOT'),
        email=dict(),
        first_name=dict(),
        last_name=dict(),
        password=dict(no_log=True),
        timezone=dict(),
        keys_registered=dict(type='bool', default=False),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_acc = AnsibleCloudStackUser(module)

    state = module.params.get('state')

    if state == 'absent':
        user = acs_acc.absent_user()

    elif state in ['enabled', 'unlocked']:
        user = acs_acc.enable_user()

    elif state == 'disabled':
        user = acs_acc.disable_user()

    elif state == 'locked':
        user = acs_acc.lock_user()

    else:
        user = acs_acc.present_user()

    result = acs_acc.get_result(user)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
