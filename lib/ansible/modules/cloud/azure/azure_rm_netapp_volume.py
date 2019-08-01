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
module: azure_rm_netapp_volume

short_description: Manage NetApp Azure Files Volume
version_added: "2.9"
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Create and delete NetApp Azure volume.
extends_documentation_fragment:
    - netapp.azure_rm_netapp

options:
    name:
        description:
            - The name of the volume.
        required: true
        type: str
    file_path:
        description:
            - A unique file path for the volume. Used when creating mount targets.
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
    subnet_id:
        description:
            - The Azure Resource URI for a delegated subnet. Must have the delegation Microsoft.NetApp/volumes.
            - Provide name of the subnet ID.
            - Required for create.
        type: str
    virtual_network:
        description:
            - The name of the virtual network required for the subnet to create a volume.
            - Required for create.
        type: str
    service_level:
        description:
            - The service level of the file system.
        type: str
        default: Premium
        choices:
            - Premium
            - Standard
            - Ultra
    state:
        description:
            - State C(present) will check that the volume exists with the requested configuration.
            - State C(absent) will delete the volume.
        default: present
        choices:
            - absent
            - present

'''
EXAMPLES = '''

- name: Create Azure NetApp volume
  azure_rm_netapp_volume:
    resource_group: myResourceGroup
    account_name: tests-netapp
    pool_name: tests-pool
    name: tests-volume2
    location: eastus
    file_path: tests-volume2
    virtual_network: myVirtualNetwork
    subnet_id: test
    service_level: Ultra

- name: Delete Azure NetApp volume
  azure_rm_netapp_volume:
    state: absent
    resource_group: myResourceGroup
    account_name: tests-netapp
    pool_name: tests-pool
    name: tests-volume2

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
    from azure.mgmt.netapp.models import Volume
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


class AzureRMNetAppVolume(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            file_path=dict(type='str', required=False),
            pool_name=dict(type='str', required=True),
            account_name=dict(type='str', required=True),
            location=dict(type='str', required=False),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            subnet_id=dict(type='str', required=False),
            virtual_network=dict(type='str', required=False),
            service_level=dict(type='str', required=False, choices=['Premium', 'Standard', 'Ultra'], default='Premium')
        )
        self.module = AnsibleModule(
            argument_spec=self.module_arg_spec,
            required_if=[
                ('state', 'present', ['location', 'file_path', 'subnet_id', 'virtual_network']),
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
        super(AzureRMNetAppVolume, self).__init__(derived_arg_spec=self.module_arg_spec, supports_check_mode=True)

    def get_azure_netapp_volume(self):
        """
            Returns volume object for an existing volume
            Return None if volume does not exist
        """
        try:
            volume_get = self.client.volumes.get(self.parameters['resource_group'], self.parameters['account_name'],
                                                 self.parameters['pool_name'], self.parameters['name'])
        except CloudError:  # volume does not exist
            return None
        return volume_get

    def create_azure_netapp_volume(self):
        """
            Create a volume for the given Azure NetApp Account
            :return: None
        """
        volume_body = Volume(
            location=self.parameters['location'],
            creation_token=self.parameters['file_path'],
            service_level=self.parameters['service_level'],
            subnet_id='/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s'
                      % (self.client.config.subscription_id, self.parameters['resource_group'],
                         self.parameters['virtual_network'], self.parameters['subnet_id'])
        )
        try:
            result = self.client.volumes.create_or_update(body=volume_body, resource_group_name=self.parameters['resource_group'],
                                                          account_name=self.parameters['account_name'],
                                                          pool_name=self.parameters['pool_name'], volume_name=self.parameters['name'])
            # waiting till the status turns Succeeded
            while result.done() is not True:
                result.result(10)
        except CloudError as error:
            self.module.fail_json(msg='Error creating volume %s for Azure NetApp account %s: %s'
                                      % (self.parameters['name'], self.parameters['account_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_azure_netapp_volume(self):
        """
            Delete a volume for the given Azure NetApp Account
            :return: None
        """
        try:
            result = self.client.volumes.delete(resource_group_name=self.parameters['resource_group'],
                                                account_name=self.parameters['account_name'],
                                                pool_name=self.parameters['pool_name'], volume_name=self.parameters['name'])
            # waiting till the status turns Succeeded
            while result.done() is not True:
                result.result(10)
        except CloudError as error:
            self.module.fail_json(msg='Error deleting volume %s for Azure NetApp account %s: %s'
                                      % (self.parameters['name'], self.parameters['account_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def exec_module(self, **kwargs):
        current = self.get_azure_netapp_volume()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_azure_netapp_volume()
                elif cd_action == 'delete':
                    self.delete_azure_netapp_volume()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    AzureRMNetAppVolume()


if __name__ == '__main__':
    main()
