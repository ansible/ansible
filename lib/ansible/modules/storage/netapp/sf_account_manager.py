#!/usr/bin/python

# (c) 2017, NetApp, Inc
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


DOCUMENTATION = '''

module: sf_account_manager

short_description: Manage SolidFire accounts
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, destroy, or update accounts on SolidFire
    - auth_basic

options:

    state:
        required: true
        description:
        - Whether the specified account should exist or not.
        choices: ['present', 'absent']

    name:
        required: true
        description:
        - Unique username for this account. (May be 1 to 64 characters in length).

    new_name:
        required: false
        description:
        - New name for the user account.
        default: None

    initiator_secret:
        required: false
        type: CHAPSecret
        description:
        - CHAP secret to use for the initiator. Should be 12-16 characters long and impenetrable.
        - The CHAP initiator secrets must be unique and cannot be the same as the target CHAP secret.
        - If not specified, a random secret is created.

    target_secret:
        required: false
        type: CHAPSecret
        description:
        - CHAP secret to use for the target (mutual CHAP authentication).
        - Should be 12-16 characters long and impenetrable.
        - The CHAP target secrets must be unique and cannot be the same as the initiator CHAP secret.
        - If not specified, a random secret is created.

    attributes:
        required: false
        type: dict
        description: List of Name/Value pairs in JSON object format.

    account_id:
        required: false
        description:
        - The ID of the account to manage or update
        default: None

    status:
        required: false
        type: str
        description:
        - Status of the account

'''

EXAMPLES = """
    - name: Create Account
      sf_account_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: TenantA

    - name: Modify Account
     sf_account_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: TenantA
       new_name: TenantA-Renamed

    - name: Delete Account
     sf_account_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: delete
       name: TenantA-Renamed
"""

RETURN = """
msg:
    description: Successful creation
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successful update
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successful deletion
    returned: success
    type: string
    sample: '{"changed": true}'

"""

import logging
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SolidFireAccount(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            account_id=dict(required=False, type='int', default=None),

            new_name=dict(required=False, type='str', default=None),
            initiator_secret=dict(required=False, type='str'),
            target_secret=dict(required=False, type='str'),
            attributes=dict(required=False, type='dict'),
            status=dict(required=False, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.account_id = p['account_id']

        self.new_name = p['new_name']
        self.initiator_secret = p['initiator_secret']
        self.target_secret = p['target_secret']
        self.attributes = p['attributes']
        self.status = p['status']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_account(self):
        """
            Return account object if found

            :return: Details about the account. None if not found.
            :rtype: dict
        """
        account_list = self.sfe.list_accounts()

        for account in account_list.accounts:
            if account.username == self.name:
                # Update self.account_id:
                if self.account_id is not None:
                    if account.account_id == self.account_id:
                        return account
                else:
                    self.account_id = account.account_id
                    return account
        return None

    def create_account(self):
        logger.debug('Creating account %s', self.name)

        try:
            self.sfe.add_account(username=self.name,
                                 initiator_secret=self.initiator_secret,
                                 target_secret=self.target_secret,
                                 attributes=self.attributes)
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
            self.sfe.modify_account(account_id=self.account_id,
                                    username=self.new_name,
                                    status=self.status,
                                    initiator_secret=self.initiator_secret,
                                    target_secret=self.target_secret,
                                    attributes=self.attributes)

        except:
            err = get_exception()
            logger.exception('Error updating account %s : %s', self.account_id, str(err))
            raise

    def apply(self):
        changed = False
        account_exists = False
        update_account = False
        account_detail = self.get_account()

        if account_detail:
            account_exists = True

            if self.state == 'absent':
                logger.debug(
                    "CHANGED: account exists, but requested state is 'absent'")
                changed = True

            elif self.state == 'present':
                # Check if we need to update the account

                if account_detail.username is not None and self.new_name is not None and \
                        account_detail.username != self.new_name:
                    logger.debug("CHANGED: account username needs to be updated")
                    update_account = True
                    changed = True

                elif account_detail.status is not None and self.status is not None \
                        and account_detail.status != self.status:
                    logger.debug("CHANGED: Account status needs to be updated")
                    update_account = True
                    changed = True

                elif account_detail.initiator_secret is not None and self.initiator_secret is not None \
                        and account_detail.initiator_secret != self.initiator_secret:
                    logger.debug("CHANGED: Initiator secret needs to be updated")
                    update_account = True
                    changed = True

                elif account_detail.target_secret is not None and self.target_secret is not None \
                        and account_detail.target_secret != self.target_secret:
                    logger.debug("CHANGED: Target secret needs to be updated")
                    update_account = True
                    changed = True

                elif account_detail.attributes is not None and self.attributes is not None \
                        and account_detail.attributes != self.attributes:
                    logger.debug("CHANGED: Attributes needs to be updated")
                    update_account = True
                    changed = True
        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: account does not exist, but requested state is "
                    "'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not account_exists:
                        self.create_account()
                    elif update_account:
                        self.update_account()

                elif self.state == 'absent':
                    self.delete_account()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireAccount()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

if __name__ == '__main__':
    main()

