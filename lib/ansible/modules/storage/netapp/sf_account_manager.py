#!/usr/bin/python
# (c) 2016, NetApp, Inc
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

#!/usr/bin/python

DOCUMENTATION = '''

module: sf_account_manager

short_description: Manage SolidFire accounts

description:
- Create, destroy, or update accounts on SolidFire
    - auth_basic

options:

    hostname:
        required: true
        description:
        - hostname

    username:
        required: true
        description:
        - username

    password:
        required: true
        description:
        - password

    action:
        required: true
        description:
        - Create, Delete, or Update an account with the passed parameters
        choices: ['create', 'delete', 'update']

    name:
        required: true when action == 'create'
        description:
        - Unique username for this account. (May be 1 to 64 characters in length).

    initiator_secret:
        required: false
        type: CHAPSecret
        description:
        - CHAP secret to use for the initiator. Should be 12-16 characters long and impenetrable.
        The CHAP initiator secrets must be unique and cannot be the same as the target CHAP secret.
        If not specified, a random secret is created.

    target_secret:
        required: false
        type: CHAPSecret
        description:
        - CHAP secret to use for the target (mutual CHAP authentication). Should be 12-16 characters
        long and impenetrable. The CHAP target secrets must be unique and cannot be the same as the
        initiator CHAP secret. If not specified, a random secret is created.

    attributes:
        required: false
        type: dict
        description: List of Name/Value pairs in JSON object format.

    account_id:
        required: true when action == 'delete' or action == 'update'
        description:
        - The ID of the account to manage or update

    status:
        required: false
        type: str
        description:
        - Status of the account

'''

'''
    Todo:
        Enable account deletion by Name. Currently only possible through account_id.

        Before updating an account, check the previous (current) attributes to currently report
        the 'changed' property

'''
import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory


class SolidFireAccount(object):

    def __init__(self):

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'update']),

                name=dict(type='str'),
                initiator_secret=dict(required=False, type='str'),
                target_secret=dict(required=False, type='str'),
                attributes=dict(required=False, type='dict'),

                account_id=dict(type='int'),
                status=dict(required=False, type='str'),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['name']),
                ('action', 'delete', ['account_id']),
                ('action', 'update', ['account_id'])
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        self.name = p['name']
        self.initiator_secret = p['initiator_secret']
        self.target_secret = p['target_secret']
        self.attributes = p['attributes']
        self.account_id = p['account_id']
        self.status = p['status']

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def create_account(self):
        logger.debug('Creating account %s', self.name)

        try:
            self.sfe.add_account(username=self.name, initiator_secret=self.initiator_secret,
                                 target_secret=self.target_secret, attributes=self.attributes)
        except:
            err = get_exception()
            logger.exception('Error creating account %s : %s',
                             self.name, str(err))
            raise

    def delete_account(self):
        logger.debug('Deleting account %s', self.account_id)

        try:
            self.sfe.remove_account(account_id=self.account_id)

        except:
            err = get_exception()
            logger.exception('Error deleting account %s : %s', self.account_id, str(err))
            raise

    def update_account(self):
        logger.debug('Updating account %s', self.account_id)

        try:
            self.sfe.modify_account(account_id=self.account_id, username=self.name, status=self.status,
                                    initiator_secret=self.initiator_secret, target_secret=self.target_secret,
                                    attributes=self.attributes)

        except:
            err = get_exception()
            logger.exception('Error updating account %s : %s', self.account_id, str(err))
            raise

    def apply(self):
        changed = False

        if self.action == 'create':
            self.create_account()
            changed = True

        elif self.action == 'delete':
            self.delete_account()
            changed = True

        elif self.action == 'update':
            self.update_account()
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireAccount()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

main()
