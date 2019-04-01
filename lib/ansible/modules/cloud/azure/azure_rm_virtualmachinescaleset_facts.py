#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Sertac Ozercan <seozerca@microsoft.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_virtualmachinescaleset_facts

version_added: "2.4"

short_description: Get Virtual Machine Scale Set facts

description:
    - Get facts for a virtual machine scale set

notes:
    - This module was called C(azure_rm_virtualmachine_scaleset_facts) before Ansible 2.8. The usage did not change.

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
            - If C(curated) is selected the structure will be identical to input parameters of azure_rm_virtualmachinescaleset module.
            - In Ansible 2.5 and lower facts are always returned in raw format.
            - Please note that this option will be deprecated in 2.10 when curated format will become the only supported format.
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
      azure_rm_virtualmachinescaleset_facts:
        resource_group: myResourceGroup
        name: testvmss001
        format: curated

    - name: Get facts for all virtual networks
      azure_rm_virtualmachinescaleset_facts:
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_virtualmachinescaleset_facts:
        resource_group: myResourceGroup
        tags:
          - testing
'''

RETURN = '''
vmss:
    description: List of virtual machine scale sets
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/scalesets/myscaleset
        admin_username:
            description:
                - Admin username used to access the host after it is created.
            returned: always
            type: str
            sample: adminuser
        capacity:
            description:
                - Capacity of VMSS.
            returned: always
            type: int
            sample: 2
        data_disks:
            description:
                - List of attached data disks.
            returned: always
            type: complex
            contains:
                caching:
                    description:
                        - Type of data disk caching.
                    type: str
                    sample: ReadOnly
                disk_size_gb:
                    description:
                        - The initial disk size in GB for blank data disks
                    type: int
                    sample: 64
                lun:
                    description:
                        - The logical unit number for data disk
                    type: int
                    sample: 0
                managed_disk_type:
                    description:
                        - Managed data disk type
                    type: str
                    sample: Standard_LRS
        image:
            description:
                - Image specification
            returned: always
            type: complex
            contains:
                offer:
                    description:
                        - Offer.
                    type: str
                    sample: RHEL
                publisher:
                    description:
                        - Publisher name.
                    type: str
                    sample: RedHat
                sku:
                    description:
                        - SKU name.
                    type: str
                    sample: 7-RAW
                version:
                    description:
                        - Image version.
                    type: str
                    sample: 7.5.2018050901
        load_balancer:
            description:
                - Load balancer name.
            returned: always
            type: str
            sample: testlb
        location:
            description:
                - Resource location.
            type: str
            returned: always
            sample: japaneast
        managed_disk_type:
            description:
                - Managed data disk type
            type: str
            returned: always
            sample: Standard_LRS
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: myvmss
        os_disk_caching:
            description:
                - Type of OS disk caching.
            type: str
            returned: always
            sample: ReadOnly
        os_type:
            description:
                - Base type of operating system.
            type: str
            returned: always
            sample: Linux
        overprovision:
            description:
                - Specifies whether the Virtual Machine Scale Set should be overprovisioned.
            type: bool
            sample: true
        resource_group:
            description:
                - Resource group.
            type: str
            returned: always
            sample: myResourceGroup
        ssh_password_enabled:
            description:
                - Is SSH password authentication enabled. Valid only for Linux.
            type: bool
            returned: always
            sample: true
        subnet_name:
            description:
                - Subnet name.
            type: str
            returned: always
            sample: testsubnet
        tier:
            description:
                - SKU Tier.
            type: str
            returned: always
            sample: Basic
        upgrade_policy:
            description:
                - Upgrade policy.
            type: str
            returned: always
            sample: Manual
        virtual_network_name:
            description:
                - Associated virtual network name.
            type: str
            returned: always
            sample: testvn
        vm_size:
            description:
                - Virtual machine size.
            type: str
            returned: always
            sample: Standard_D4
        tags:
            description: Tags assigned to the resource. Dictionary of string:string pairs.
            type: dict
            sample: { "tag1": "abc" }
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
import re

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
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

        if self.module._name == 'azure_rm_virtualmachine_scaleset_facts':
            self.module.deprecate("The 'azure_rm_virtualmachine_scaleset_facts' module has been renamed to 'azure_rm_virtualmachinescaleset_facts'",
                                  version='2.12')

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
                except Exception:
                    self.log('Could not extract subnet name')

                try:
                    backend_address_pool_id = (vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]
                                               ['properties']['ipConfigurations'][0]['properties']['loadBalancerBackendAddressPools'][0]['id'])
                    load_balancer_name = re.sub('\\/backendAddressPools.*', '', re.sub('.*loadBalancers\\/', '', backend_address_pool_id))
                    virtual_network_name = re.sub('.*virtualNetworks\\/', '', re.sub('\\/subnets.*', '', subnet_id))
                except Exception:
                    self.log('Could not extract load balancer / virtual network name')

                try:
                    ssh_password_enabled = (not vmss['properties']['virtualMachineProfile']['osProfile']
                                                    ['linuxConfiguration']['disablePasswordAuthentication'])
                except Exception:
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
                    'id': vmss['id'],
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
                    'overprovision': vmss['properties']['overprovision'],
                    'managed_disk_type': vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['managedDisk']['storageAccountType'],
                    'data_disks': data_disks,
                    'virtual_network_name': virtual_network_name,
                    'subnet_name': subnet_name,
                    'load_balancer': load_balancer_name,
                    'tags': vmss.get('tags')
                }

                self.results['ansible_facts']['azure_vmss'][index] = updated

            # proper result format we want to support in the future
            # dropping 'ansible_facts' and shorter name 'vmss'
            self.results['vmss'] = self.results['ansible_facts']['azure_vmss']

        return self.results

    def get_item(self):
        """Get a single virtual machine scale set"""

        self.log('Get properties for {0}'.format(self.name))

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
            self.fail('Failed to list all items - {0}'.format(str(exc)))

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
