#!/usr/bin/python
#
# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_netapp_account

short_description: Manage NetApp Azure Files Account
version_added: "2.9"
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Create and delete NetApp Azure account.
      Provide the Resource group name for the NetApp account to be created.
extends_documentation_fragment:
    - netapp.azure_rm_netapp

options:
    name:
        description:
            - The name of the NetApp account.
        required: true
        type: str
    location:
        description:
            - Resource location.
            - Required for create.
        type: str
    state:
        description:
            - State C(present) will check that the NetApp account exists with the requested configuration.
            - State C(absent) will delete the NetApp account.
        default: present
        choices:
            - absent
            - present
        type: str

'''
EXAMPLES = '''

- name: Create NetApp Azure Account
  azure_rm_netapp_account:
    resource_group: myResourceGroup
    name: testaccount
    location: eastus

- name: Delete NetApp Azure Account
  azure_rm_netapp_account:
    state: absent
    resource_group: myResourceGroup
    name: testaccount
    location: eastus

'''

RETURN = '''
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.basic import to_native
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.basic import AnsibleModule
import traceback

HAS_AZURE_MGMT_NETAPP = False
try:
    from azure.mgmt.netapp.azure_net_app_files_management_client import AzureNetAppFilesManagementClient
    from azure.mgmt.netapp.models import NetAppAccount
    HAS_AZURE_MGMT_NETAPP = True
except ImportError:
    HAS_AZURE_MGMT_NETAPP = False


class AzureRMNetAppAccount(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            location=dict(type='str'),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
        )
        self.module = AnsibleModule(
            argument_spec=self.module_arg_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        # authentication - using CLI
        if HAS_AZURE_MGMT_NETAPP is False:
            self.module.fail_json(msg="the python Azure-mgmt-NetApp module is required")
        super(AzureRMNetAppAccount, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                   supports_check_mode=True)

    def get_azure_netapp_account(self):
        """
            Returns NetApp Account object for an existing account
            Return None if account does not exist
        """
        try:
            account_get = self.netapp_client.accounts.get(self.parameters['resource_group'], self.parameters['name'])
        except CloudError:  # account does not exist
            return None
        return account_get

    def create_azure_netapp_account(self):
        """
            Create an Azure NetApp Account
            :return: None
        """
        account_body = NetAppAccount(
            location=self.parameters['location']
        )
        try:
            self.netapp_client.accounts.create_or_update(body=account_body,
                                                         resource_group_name=self.parameters['resource_group'],
                                                         account_name=self.parameters['name'])
        except CloudError as error:
            self.module.fail_json(msg='Error creating Azure NetApp account %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_azure_netapp_account(self):
        """
            Delete an Azure NetApp Account
            :return: None
        """
        try:
            self.netapp_client.accounts.delete(resource_group_name=self.parameters['resource_group'],
                                               account_name=self.parameters['name'])
        except CloudError as error:
            self.module.fail_json(msg='Error deleting Azure NetApp account %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def exec_module(self, **kwargs):
        current = self.get_azure_netapp_account()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_azure_netapp_account()
                elif cd_action == 'delete':
                    self.delete_azure_netapp_account()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    AzureRMNetAppAccount()


if __name__ == '__main__':
    main()
