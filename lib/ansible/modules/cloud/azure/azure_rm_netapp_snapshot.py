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
module: azure_rm_netapp_snapshot

short_description: Manage NetApp Azure Files Snapshot
version_added: "2.9"
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Create and delete NetApp Azure Snapshot.
extends_documentation_fragment:
    - netapp.azure_rm_netapp

options:
    name:
        description:
            - The name of the snapshot.
        required: true
        type: str
    volume_name:
        description:
            - The name of the volume.
        required: true
        type: str
    pool_name:
        description:
            - The name of the capacity pool.
        required: true
        type: str
    account_name:
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
            - State C(present) will check that the snapshot exists with the requested configuration.
            - State C(absent) will delete the snapshot.
        default: present
        choices:
            - absent
            - present

'''
EXAMPLES = '''

- name: Create Azure NetApp Snapshot
  azure_rm_netapp_snapshot:
    resource_group: myResourceGroup
    account_name: tests-netapp
    pool_name: tests-pool
    volume_name: tests-volume2
    name: tests-snapshot
    location: eastus

- name: Delete Azure NetApp Snapshot
  azure_rm_netapp_snapshot:
    state: absent
    resource_group: myResourceGroup
    account_name: tests-netapp
    pool_name: tests-pool
    volume_name: tests-volume2
    name: tests-snapshot

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

AZURE_OBJECT_CLASS = 'NetAppAccount'
HAS_AZURE_MGMT_NETAPP = False
try:
    from azure.mgmt.netapp.azure_net_app_files_management_client import AzureNetAppFilesManagementClient
    from azure.mgmt.netapp.models import Snapshot
    from azure.common.client_factory import get_client_from_cli_profile
    HAS_AZURE_MGMT_NETAPP = True
except ImportError:
    HAS_AZURE_MGMT_NETAPP = False

HAS_AZURE_COMMON = False
try:
    from azure.common.client_factory import get_client_from_cli_profile
    HAS_AZURE_COMMON = True
except ImportError:
    HAS_AZURE_COMMON = False


class AzureRMNetAppSnapshot(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            volume_name=dict(type='str', required=True),
            pool_name=dict(type='str', required=True),
            account_name=dict(type='str', required=True),
            location=dict(type='str', required=False),
            state=dict(choices=['present', 'absent'], default='present', type='str')
        )
        self.module = AnsibleModule(
            argument_spec=self.module_arg_spec,
            required_if=[
                ('state', 'present', ['location']),
            ],
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        # authentication - using CLI
        if HAS_AZURE_MGMT_NETAPP is False:
            self.module.fail_json(msg="the python Azure-mgmt-NetApp module is required")
        if HAS_AZURE_COMMON is False:
            self.module.fail_json(msg="the python azure-common module is required")
        self.client = get_client_from_cli_profile(AzureNetAppFilesManagementClient)
        super(AzureRMNetAppSnapshot, self).__init__(derived_arg_spec=self.module_arg_spec, supports_check_mode=True)

    def get_azure_netapp_snapshot(self):
        """
            Returns snapshot object for an existing snapshot
            Return None if snapshot does not exist
        """
        try:
            snapshot_get = self.client.snapshots.get(self.parameters['resource_group'], self.parameters['account_name'],
                                                     self.parameters['pool_name'], self.parameters['volume_name'],
                                                     self.parameters['name'])
        except CloudError:  # snapshot does not exist
            return None
        return snapshot_get

    def create_azure_netapp_snapshot(self):
        """
            Create a snapshot for the given Azure NetApp Account
            :return: None
        """
        snapshot_body = Snapshot(
            location=self.parameters['location']
        )
        try:
            self.client.snapshots.create(body=snapshot_body, resource_group_name=self.parameters['resource_group'],
                                         account_name=self.parameters['account_name'],
                                         pool_name=self.parameters['pool_name'],
                                         volume_name=self.parameters['volume_name'], snapshot_name=self.parameters['name'])
        except CloudError as error:
            self.module.fail_json(msg='Error creating snapshot %s for Azure NetApp account %s: %s'
                                      % (self.parameters['name'], self.parameters['account_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_azure_netapp_snapshot(self):
        """
            Delete a snapshot for the given Azure NetApp Account
            :return: None
        """
        try:
            self.client.snapshots.delete(resource_group_name=self.parameters['resource_group'],
                                         account_name=self.parameters['account_name'],
                                         pool_name=self.parameters['pool_name'],
                                         volume_name=self.parameters['volume_name'], snapshot_name=self.parameters['name'])
        except CloudError as error:
            self.module.fail_json(msg='Error deleting snapshot %s for Azure NetApp account %s: %s'
                                      % (self.parameters['name'], self.parameters['account_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def exec_module(self, **kwargs):
        current = self.get_azure_netapp_snapshot()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_azure_netapp_snapshot()
                elif cd_action == 'delete':
                    self.delete_azure_netapp_snapshot()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    AzureRMNetAppSnapshot()


if __name__ == '__main__':
    main()
