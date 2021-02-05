#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Element Software Account Manager
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_account

short_description: NetApp Element Software Manage Accounts
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, destroy, or update accounts on Element SW

options:

    state:
        description:
        - Whether the specified account should exist or not.
        required: true
        choices: ['present', 'absent']

    element_username:
        description:
        - Unique username for this account. (May be 1 to 64 characters in length).
        required: true
        aliases:
        - account_id

    from_name:
        description:
        - ID or Name of the account to rename.
        - Required to create an account called 'element_username' by renaming 'from_name'.
        version_added: '2.8'

    initiator_secret:
        description:
        - CHAP secret to use for the initiator. Should be 12-16 characters long and impenetrable.
        - The CHAP initiator secrets must be unique and cannot be the same as the target CHAP secret.
        - If not specified, a random secret is created.

    target_secret:
        description:
        - CHAP secret to use for the target (mutual CHAP authentication).
        - Should be 12-16 characters long and impenetrable.
        - The CHAP target secrets must be unique and cannot be the same as the initiator CHAP secret.
        - If not specified, a random secret is created.

    attributes:
        description: List of Name/Value pairs in JSON object format.

    status:
        description:
        - Status of the account.

'''

EXAMPLES = """
- name: Create Account
  na_elementsw_account:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    state: present
    element_username: TenantA

- name: Modify Account
  na_elementsw_account:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    state: present
    status: locked
    element_username: TenantA

- name: Rename Account
  na_elementsw_account:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    state: present
    element_username: TenantA_Renamed
    from_name: TenantA

- name: Rename and modify Account
  na_elementsw_account:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    state: present
    status: locked
    element_username: TenantA_Renamed
    from_name: TenantA

- name: Delete Account
  na_elementsw_account:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    state: absent
    element_username: TenantA_Renamed
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWAccount(object):
    """
    Element SW Account
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            element_username=dict(required=True, aliases=["account_id"], type='str'),
            from_name=dict(required=False, default=None),
            initiator_secret=dict(required=False, type='str', no_log=True),
            target_secret=dict(required=False, type='str', no_log=True),
            attributes=dict(required=False, type='dict'),
            status=dict(required=False, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params.get('state')
        self.element_username = params.get('element_username')
        self.from_name = params.get('from_name')
        self.initiator_secret = params.get('initiator_secret')
        self.target_secret = params.get('target_secret')
        self.attributes = params.get('attributes')
        self.status = params.get('status')

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the Element SW Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        if self.attributes is not None:
            self.attributes.update(self.elementsw_helper.set_element_attributes(source='na_elementsw_account'))
        else:
            self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_account')

    def get_account(self, username):
        """
        Get Account
            :description: Get Account object from account id or name

            :return: Details about the account. None if not found.
            :rtype: object (Account object)
        """

        account_list = self.sfe.list_accounts()

        for account in account_list.accounts:
            # Check and get account object for a given name
            if str(account.account_id) == username:
                return account
            elif account.username == username:
                return account
        return None

    def create_account(self):
        """
        Create the Account
        """
        try:
            self.sfe.add_account(username=self.element_username,
                                 initiator_secret=self.initiator_secret,
                                 target_secret=self.target_secret,
                                 attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg='Error creating account %s: %s' % (self.element_username, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_account(self):
        """
        Delete the Account
        """
        try:
            self.sfe.remove_account(account_id=self.account_id)

        except Exception as e:
            self.module.fail_json(msg='Error deleting account %s: %s' % (self.account_id, to_native(e)),
                                  exception=traceback.format_exc())

    def rename_account(self):
        """
        Rename the Account
        """
        try:
            self.sfe.modify_account(account_id=self.account_id,
                                    username=self.element_username,
                                    status=self.status,
                                    initiator_secret=self.initiator_secret,
                                    target_secret=self.target_secret,
                                    attributes=self.attributes)

        except Exception as e:
            self.module.fail_json(msg='Error renaming account %s: %s' % (self.account_id, to_native(e)),
                                  exception=traceback.format_exc())

    def update_account(self):
        """
        Update the Account if account already exists
        """
        try:
            self.sfe.modify_account(account_id=self.account_id,
                                    status=self.status,
                                    initiator_secret=self.initiator_secret,
                                    target_secret=self.target_secret,
                                    attributes=self.attributes)

        except Exception as e:
            self.module.fail_json(msg='Error updating account %s: %s' % (self.account_id, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Process the account operation on the Element OS Cluster
        """
        changed = False
        update_account = False
        account_detail = self.get_account(self.element_username)

        if account_detail is None and self.state == 'present':
            changed = True

        elif account_detail is not None:
            # If account found
            self.account_id = account_detail.account_id

            if self.state == 'absent':
                changed = True
            else:
                # If state - present, check for any parameter of existing account needs modification.
                if account_detail.username is not None and self.element_username is not None and \
                        account_detail.username != self.element_username:
                    update_account = True
                    changed = True
                elif account_detail.status is not None and self.status is not None \
                        and account_detail.status != self.status:
                    update_account = True
                    changed = True

                elif account_detail.initiator_secret is not None and self.initiator_secret is not None \
                        and account_detail.initiator_secret != self.initiator_secret:
                    update_account = True
                    changed = True

                elif account_detail.target_secret is not None and self.target_secret is not None \
                        and account_detail.target_secret != self.target_secret:
                    update_account = True
                    changed = True

                elif account_detail.attributes is not None and self.attributes is not None \
                        and account_detail.attributes != self.attributes:
                    update_account = True
                    changed = True
        if changed:
            if self.module.check_mode:
                # Skipping the changes
                pass
            else:
                if self.state == 'present':
                    if update_account:
                        self.update_account()
                    else:
                        if self.from_name is not None:
                            # If from_name is defined
                            account_exists = self.get_account(self.from_name)
                            if account_exists is not None:
                                # If resource pointed by from_name exists, rename the account to name
                                self.account_id = account_exists.account_id
                                self.rename_account()
                            else:
                                # If resource pointed by from_name does not exists, error out
                                self.module.fail_json(msg="Resource does not exist : %s" % self.from_name)
                        else:
                            # If from_name is not defined, create from scratch.
                            self.create_account()
                elif self.state == 'absent':
                    self.delete_account()

        self.module.exit_json(changed=changed)


def main():
    """
    Main function
    """
    na_elementsw_account = ElementSWAccount()
    na_elementsw_account.apply()


if __name__ == '__main__':
    main()
