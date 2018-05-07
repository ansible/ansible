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
        required: false
        default: null
    resource_group:
        description:
            - The resource group to search for the desired virtual machine scale set
        required: false
    format:
        description:
            - What data should be returned?
        default: 'raw'
        choices:
            - 'ansible'
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
        "location": "eastus",
        "properties": {
            "overprovision": true,
            "singlePlacementGroup": true,
            "upgradePolicy": {
                "mode": "Manual"
            },
            "virtualMachineProfile": {
                "networkProfile": {
                    "networkInterfaceConfigurations": [
                        {
                            "name": "testvmss",
                            "properties": {
                                "dnsSettings": {
                                    "dnsServers": []
                                },
                                "enableAcceleratedNetworking": false,
                                "ipConfigurations": [
                                    {
                                        "name": "default",
                                        "properties": {
                                            "privateIPAddressVersion": "IPv4",
                                            "subnet": {
                                                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/testvnet/subnets/testsubnet"
                                            }
                                        }
                                    }
                                ],
                                "primary": true
                            }
                        }
                    ]
                },
                "osProfile": {
                    "adminUsername": "testuser",
                    "computerNamePrefix": "testvmss",
                    "linuxConfiguration": {
                        "disablePasswordAuthentication": true,
                        "ssh": {
                            "publicKeys": [
                                {
                                    "keyData": "",
                                    "path": "/home/testuser/.ssh/authorized_keys"
                                }
                            ]
                        }
                    },
                    "secrets": []
                },
                "storageProfile": {
                    "imageReference": {
                        "offer": "CoreOS",
                        "publisher": "CoreOS",
                        "sku": "Stable",
                        "version": "899.17.0"
                    },
                    "osDisk": {
                        "caching": "ReadWrite",
                        "createOption": "fromImage",
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        }
                    }
                }
            }
        },
        "sku": {
            "capacity": 1,
            "name": "Standard_DS1_v2",
            "tier": "Standard"
        }
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
                choices=['ansible',
                         'raw']
            ),
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

        if self.format == 'ansible':
            for index in range(len(self.results['ansible_facts']['azure_vmss'])):
                vmss = self.results['ansible_facts']['azure_vmss'][index]
                subnet_id = vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]
                                ['properties']['ipConfigurations'][0]['properties']['subnet']['id']
                backend_address_pool_id = vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]
                                              ['properties']['ipConfigurations'][0]['properties']['loadBalancerBackendAddressPools'][0]['id']
                subnet_name = re.sub('.*subnets\\/', '', subnet_id)
                load_balancer_name = re.sub('\\/backendAddressPools.*', '', re.sub('.*loadBalancers\\/', '', backend_address_pool_id))
                virtual_network_name = re.sub('.*virtualNetworks\\/', '', re.sub('\\/subnets.*', '', subnet_id))

                updated = {}
                updated['resource_group'] = self.resource_group
                updated['name'] = vmss['name']
                updated['state'] = 'present'
                updated['location'] = vmss['location']
                updated['vm_size'] = vmss['sku']['name']
                updated['capacity'] = vmss['sku']['capacity']
                updated['tier'] = vmss['sku']['tier']
                updated['upgrade_policy'] = vmss['properties']['upgradePolicy']['mode']
                updated['admin_username'] = vmss['properties']['virtualMachineProfile']['osProfile']['adminUsername']
                # updated['admin_password']
                updated['ssh_password_enabled'] = not vmss['properties']['virtualMachineProfile']['osProfile']
                                                          ['linuxConfiguration']['disablePasswordAuthentication']
                # updated['ssh_public_keys']
                # image could be a dict, string,
                updated['image'] = vmss['properties']['virtualMachineProfile']['storageProfile']['imageReference']

                updated['os_disk_caching'] = vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching']
                updated['os_type'] = 'Linux'  # vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching']
                updated['managed_disk_type'] = vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['managedDisk']['storageAccountType']

                data_disks = vmss['properties']['virtualMachineProfile']['storageProfile'].get('dataDisks', [])

                for disk_index in range(len(data_disks)):
                    old_disk = data_disks[disk_index]
                    new_disk = {}
                    new_disk['lun'] = old_disk['lun']
                    new_disk['disk_size_gb'] = old_disk['diskSizeGB']
                    new_disk['managed_disk_type'] = old_disk['managedDisk']['storageAccountType']
                    new_disk['caching'] = old_disk['caching']
                    data_disks[disk_index] = new_disk

                updated['data_disks'] = data_disks
                updated['virtual_network_name'] = virtual_network_name
                updated['subnet_name'] = subnet_name
                updated['load_balancer'] = load_balancer_name

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
