#!/usr/bin/python
#
# Copyright (c) 2017 Sertac Ozercan, <seozerca@microsoft.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_scaleset_facts

version_added: "2.4"

short_description: Get Virtual Machine Scale Set facts

description:
    - Get facts for a virtual machine scale set

options:
    name:
        description:
            - Limit results to a specific virtual machine scale set
    resource_group:
        description:
            - The resource group to search for the desired virtual machine scale set
    tags:
        description:
            - List of tags to be matched
    format:
        description:
            - Format of the data returned.
            - If C(raw) is selected information will be returned in raw format from Azure Python SDK.
            - If C(curated) is selected the structure will be identical to input parameters of azure_rm_virtualmachine_scaleset module.
            - In Ansible 2.5 and lower facts are always returned in raw format.
        default: 'raw'
        choices:
            - 'curated'
            - 'raw'
        version_added: "2.6"

extends_documentation_fragment:
    - azure

author:
    - "Sertac Ozercan (@sozercan)"
'''

EXAMPLES = '''
    - name: Get facts for a virtual machine scale set
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing
        name: testvmss001
        format: curated

    - name: Get facts for all virtual networks
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing

    - name: Get facts by tags
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing
        tags:
          - testing
'''

RETURN = '''
azure_vmss:
    description: List of virtual machine scale sets
    returned: always
    type: list
    example: [{
        "admin_username": "testuser",
        "capacity": 2,
        "data_disks": [
            {
                "caching": "ReadWrite",
                "disk_size_gb": 64,
                "lun": 0,
                "managed_disk_type": "Standard_LRS"
            }
        ],
        "image": {
            "offer": "CoreOS",
            "publisher": "CoreOS",
            "sku": "Stable",
            "version": "899.17.0"
        },
        "load_balancer": null,
        "location": "eastus",
        "managed_disk_type": "Standard_LRS",
        "name": "testVMSSeb4fd3c704",
        "os_disk_caching": "ReadWrite",
        "os_type": "Linux",
        "resource_group": "myresourcegroup",
        "ssh_password_enabled": false,
        "state": "present",
        "subnet_name": null,
        "tier": "Standard",
        "upgrade_policy": "Manual",
        "virtual_network_name": null,
        "vm_size": "Standard_DS1_v2"
    }]
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
import re

try:
    from msrestazure.azure_exceptions import CloudError
except:
    # handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'VirtualMachineScaleSet'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineScaleSetFacts(AzureRMModuleBase):
    """Utility class to get virtual machine scale set facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            format=dict(
                type='str',
                choices=['curated',
                         'raw'],
                default='raw'
            )
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                azure_vmss=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.format = None
        self.tags = None

        super(AzureRMVirtualMachineScaleSetFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")
        if self.name:
            self.results['ansible_facts']['azure_vmss'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_vmss'] = self.list_items()

        if self.format == 'curated':
            for index in range(len(self.results['ansible_facts']['azure_vmss'])):
                vmss = self.results['ansible_facts']['azure_vmss'][index]
                subnet_name = None
                load_balancer_name = None
                virtual_network_name = None
                ssh_password_enabled = False

                try:
                    subnet_id = (vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]
                                 ['properties']['ipConfigurations'][0]['properties']['subnet']['id'])
                    subnet_name = re.sub('.*subnets\\/', '', subnet_id)
                except:
                    self.log('Could not extract subnet name')

                try:
                    backend_address_pool_id = (vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]
                                               ['properties']['ipConfigurations'][0]['properties']['loadBalancerBackendAddressPools'][0]['id'])
                    load_balancer_name = re.sub('\\/backendAddressPools.*', '', re.sub('.*loadBalancers\\/', '', backend_address_pool_id))
                    virtual_network_name = re.sub('.*virtualNetworks\\/', '', re.sub('\\/subnets.*', '', subnet_id))
                except:
                    self.log('Could not extract load balancer / virtual network name')

                try:
                    ssh_password_enabled = (not vmss['properties']['virtualMachineProfile']['osProfile'],
                                                    ['linuxConfiguration']['disablePasswordAuthentication'])
                except:
                    self.log('Could not extract SSH password enabled')

                data_disks = vmss['properties']['virtualMachineProfile']['storageProfile'].get('dataDisks', [])

                for disk_index in range(len(data_disks)):
                    old_disk = data_disks[disk_index]
                    new_disk = {
                        'lun': old_disk['lun'],
                        'disk_size_gb': old_disk['diskSizeGB'],
                        'managed_disk_type': old_disk['managedDisk']['storageAccountType'],
                        'caching': old_disk['caching']
                    }
                    data_disks[disk_index] = new_disk

                updated = {
                    'resource_group': self.resource_group,
                    'name': vmss['name'],
                    'state': 'present',
                    'location': vmss['location'],
                    'vm_size': vmss['sku']['name'],
                    'capacity': vmss['sku']['capacity'],
                    'tier': vmss['sku']['tier'],
                    'upgrade_policy': vmss['properties']['upgradePolicy']['mode'],
                    'admin_username': vmss['properties']['virtualMachineProfile']['osProfile']['adminUsername'],
                    'admin_password': vmss['properties']['virtualMachineProfile']['osProfile'].get('adminPassword'),
                    'ssh_password_enabled': ssh_password_enabled,
                    'image': vmss['properties']['virtualMachineProfile']['storageProfile']['imageReference'],
                    'os_disk_caching': vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching'],
                    'os_type': 'Linux' if (vmss['properties']['virtualMachineProfile']['osProfile'].get('linuxConfiguration') is not None) else 'Windows',
                    'managed_disk_type': vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['managedDisk']['storageAccountType'],
                    'data_disks': data_disks,
                    'virtual_network_name': virtual_network_name,
                    'subnet_name': subnet_name,
                    'load_balancer': load_balancer_name
                }

                self.results['ansible_facts']['azure_vmss'][index] = updated

        return self.results

    def get_item(self):
        """Get a single virtual machine scale set"""

        self.log('Get properties for {}'.format(self.name))

        item = None
        results = []

        try:
            item = self.compute_client.virtual_machine_scale_sets.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            results = [self.serialize_obj(item, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)]

        return results

    def list_items(self):
        """Get all virtual machine scale sets"""

        self.log('List all virtual machine scale sets')

        try:
            response = self.compute_client.virtual_machine_scale_sets.list(self.resource_group)
        except CloudError as exc:
            self.fail('Failed to list all items - {}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES))

        return results


def main():
    """Main module execution code path"""

    AzureRMVirtualMachineScaleSetFacts()

if __name__ == '__main__':
    main()
