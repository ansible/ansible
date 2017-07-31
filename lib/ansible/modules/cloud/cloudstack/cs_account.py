#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_account
short_description: Manages accounts on Apache CloudStack based clouds.
description:
    - Create, disable, lock, enable and remove accounts.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of account.
    required: true
  username:
    description:
      - Username of the user to be created if account did not exist.
      - Required on C(state=present).
    required: false
    default: null
  password:
    description:
      - Password of the user to be created if account did not exist.
      - Required on C(state=present).
    required: false
    default: null
  first_name:
    description:
      - First name of the user to be created if account did not exist.
      - Required on C(state=present).
    required: false
    default: null
  last_name:
    description:
      - Last name of the user to be created if account did not exist.
      - Required on C(state=present).
    required: false
    default: null
  email:
    description:
      - Email of the user to be created if account did not exist.
      - Required on C(state=present).
    required: false
    default: null
  timezone:
    description:
      - Timezone of the user to be created if account did not exist.
    required: false
    default: null
  network_domain:
    description:
      - Network domain of the account.
    required: false
    default: null
  account_type:
    description:
      - Type of the account.
    required: false
    default: 'user'
    choices: [ 'user', 'root_admin', 'domain_admin' ]
  domain:
    description:
      - Domain the account is related to.
    required: false
    default: 'ROOT'
  state:
    description:
      - State of the account.
      - C(unlocked) is an alias for C(enabled).
    required: false
    default: 'present'
    choices: [ 'present', 'absent', 'enabled', 'disabled', 'locked', 'unlocked' ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# create an account in domain 'CUSTOMERS'
local_action:
  module: cs_account
  name: customer_xy
  username: customer_xy
  password: S3Cur3
  last_name: Doe
  first_name: John
  email: john.doe@example.com
  domain: CUSTOMERS

# Lock an existing account in domain 'CUSTOMERS'
local_action:
  module: cs_account
  name: customer_xy
  domain: CUSTOMERS
  state: locked

# Disable an existing account in domain 'CUSTOMERS'
local_action:
  module: cs_account
  name: customer_xy
  domain: CUSTOMERS
  state: disabled

# Enable an existing account in domain 'CUSTOMERS'
local_action:
  module: cs_account
  name: customer_xy
  domain: CUSTOMERS
  state: enabled

# Remove an account in domain 'CUSTOMERS'
local_action:
  module: cs_account
  name: customer_xy
  domain: CUSTOMERS
  state: absent
'''

RETURN = '''
---
id:
  description: UUID of the account.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of the account.
  returned: success
  type: string
  sample: linus@example.com
account_type:
  description: Type of the account.
  returned: success
  type: string
  sample: user
state:
  description: State of the account.
  returned: success
  type: string
  sample: enabled
network_domain:
  description: Network domain of the account.
  returned: success
  type: string
  sample: example.local
domain:
  description: Domain the account is related.
  returned: success
  type: string
  sample: ROOT
'''

# import cloudstack common
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackAccount(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackAccount, self).__init__(module)
        self.returns = {
            'networkdomain': 'network_domain',
        }
        self.account = None
        self.account_types = {
            'user': 0,
            'root_admin': 1,
            'domain_admin': 2,
        }

    def get_account_type(self):
        account_type = self.module.params.get('account_type')
        return self.account_types[account_type]

    def get_account(self):
        if not self.account:
            args = {
                'listall': True,
                'domainid': self.get_domain(key='id'),
            }
            accounts = self.query_api('listAccounts', **args)
            if accounts:
                account_name = self.module.params.get('name')
                for a in accounts['account']:
                    if account_name == a['name']:
                        self.account = a
                        break

        return self.account

    def enable_account(self):
        account = self.get_account()
        if not account:
            account = self.present_account()

        if account['state'].lower() != 'enabled':
            self.result['changed'] = True
            args = {
                'id': account['id'],
                'account': self.module.params.get('name'),
                'domainid': self.get_domain(key='id')
            }
            if not self.module.check_mode:
                res = self.query_api('enableAccount', **args)
                account = res['account']
        return account

    def lock_account(self):
        return self.lock_or_disable_account(lock=True)

    def disable_account(self):
        return self.lock_or_disable_account()

    def lock_or_disable_account(self, lock=False):
        account = self.get_account()
        if not account:
            account = self.present_account()

        # we need to enable the account to lock it.
        if lock and account['state'].lower() == 'disabled':
            account = self.enable_account()

        if (lock and account['state'].lower() != 'locked' or
                not lock and account['state'].lower() != 'disabled'):
            self.result['changed'] = True
            args = {
                'id': account['id'],
                'account': self.module.params.get('name'),
                'domainid': self.get_domain(key='id'),
                'lock': lock,
            }
            if not self.module.check_mode:
                account = self.query_api('disableAccount', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    account = self.poll_job(account, 'account')
        return account

    def present_account(self):
        required_params = [
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        account = self.get_account()

        if not account:
            self.result['changed'] = True

            args = {
                'account': self.module.params.get('name'),
                'domainid': self.get_domain(key='id'),
                'accounttype': self.get_account_type(),
                'networkdomain': self.module.params.get('network_domain'),
                'username': self.module.params.get('username'),
                'password': self.module.params.get('password'),
                'firstname': self.module.params.get('first_name'),
                'lastname': self.module.params.get('last_name'),
                'email': self.module.params.get('email'),
                'timezone': self.module.params.get('timezone')
            }
            if not self.module.check_mode:
                res = self.query_api('createAccount', **args)
                account = res['account']
        return account

    def absent_account(self):
        account = self.get_account()
        if account:
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('deleteAccount', id=account['id'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'account')
        return account

    def get_result(self, account):
        super(AnsibleCloudStackAccount, self).get_result(account)
        if account:
            if 'accounttype' in account:
                for key, value in self.account_types.items():
                    if value == account['accounttype']:
                        self.result['account_type'] = key
                        break
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent', 'enabled', 'disabled', 'locked', 'unlocked'], default='present'),
        account_type=dict(choices=['user', 'root_admin', 'domain_admin'], default='user'),
        network_domain=dict(),
        domain=dict(default='ROOT'),
        email=dict(),
        first_name=dict(),
        last_name=dict(),
        username=dict(),
        password=dict(no_log=True),
        timezone=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_acc = AnsibleCloudStackAccount(module)

    state = module.params.get('state')

    if state in ['absent']:
        account = acs_acc.absent_account()

    elif state in ['enabled', 'unlocked']:
        account = acs_acc.enable_account()

    elif state in ['disabled']:
        account = acs_acc.disable_account()

    elif state in ['locked']:
        account = acs_acc.lock_account()

    else:
        account = acs_acc.present_account()

    result = acs_acc.get_result(account)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
