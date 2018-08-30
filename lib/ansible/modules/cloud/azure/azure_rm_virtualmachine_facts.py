#!/usr/bin/python
#
# Copyright (c) 2018
# Gustavo Muniz do Carmo <gustavo@esign.com.br>
# Zim Kalinowski <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_facts

version_added: "2.7"

short_description: Get virtual machine facts.

description:
  - Get facts for all virtual machines of a resource group.

options:
    resource_group:
        description:
        - Name of the resource group containing the virtual machines (required when filtering by vm name).
    name:
        description:
        - Name of the virtual machine.
    tags:
        description:
        - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
  - azure

author:
  - "Gustavo Muniz do Carmo (@gustavomcarmo)"
  - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get facts for all virtual machines of a resource group
    azure_rm_virtualmachine_facts:
      resource_group: Testing

  - name: Get facts by name
    azure_rm_virtualmachine_facts:
      resource_group: Testing
      name: vm

  - name: Get facts by tags
    azure_rm_virtualmachine_facts:
      resource_group: Testing
      tags:
        - testing
        - foo:bar
'''

RETURN = '''
vms:
    description: List of virtual machines.
    returned: always
    type: complex
    contains:
        admin_username:
            description:
                - Administrator user name.
            returned: always
            type: str
            sample: admin
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
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: /subscriptions/xxxx/resourceGroups/myclusterrg/providers/Microsoft.Compute/virtualMachines/mycluster-node-2
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
        location:
            description:
                - Resource location.
            returned: always
            type: str
            sample: japaneast
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: mycluster-node-2
        network_interface_names:
            description:
                - List of attached network interfaces.
            type: list
            sample: [
                "mycluster-node-2-nic"
            ]
        os_disk_caching:
            description:
                - Type of OS disk caching.
            type: str
            sample: ReadOnly
        os_type:
            description:
                - Base type of operating system.
            type: str
            sample: Linux
        resource_group:
            description:
                - Resource group.
            type: str
        state:
            description:
                - State of the resource.
            type: str
            sample: present
        tags:
            description:
                - Tags.
            type: dict
        vm_size:
            description:
                - Virtual machine size.
            type: str
            sample: Standard_D4
'''

try:
    from msrestazure.azure_exceptions import CloudError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six.moves.urllib.parse import urlparse
import re


AZURE_OBJECT_CLASS = 'VirtualMachine'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str'),
            name=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            vms=[]
        )

        self.resource_group = None
        self.name = None
        self.tags = None

        super(AzureRMVirtualMachineFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")
        if self.name:
            self.results['vms'] = self.get_item()
        else:
            self.results['vms'] = self.list_items()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.compute_client.virtual_machines.get(self.resource_group, self.name)
        except CloudError as err:
            self.module.warn("Error getting virtual machine {0} - {1}".format(self.name, str(err)))

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_vm(item)]

        return result

    def list_items(self):
        self.log('List all items')
        try:
            items = self.compute_client.virtual_machines.list(self.resource_group)
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in items:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_vm(self.get_vm(item.name)))
        return results

    def get_vm(self, name):
        '''
        Get the VM with expanded instanceView

        :return: VirtualMachine object
        '''
        try:
            vm = self.compute_client.virtual_machines.get(self.resource_group, name, expand='instanceview')
            return vm
        except Exception as exc:
            self.fail("Error getting virtual machine {0} - {1}".format(self.name, str(exc)))

    def serialize_vm(self, vm):
        '''
        Convert a VirtualMachine object to dict.

        :param vm: VirtualMachine object
        :return: dict
        '''

        result = self.serialize_obj(vm, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)

        new_result = {}
        new_result['id'] = vm.id
        new_result['resource_group'] = re.sub('\\/.*', '', re.sub('.*resourceGroups\\/', '', result['id']))
        new_result['name'] = vm.name
        new_result['state'] = 'present'
        new_result['location'] = vm.location
        new_result['vm_size'] = result['properties']['hardwareProfile']['vmSize']
        new_result['admin_username'] = result['properties']['osProfile']['adminUsername']
        image = result['properties']['storageProfile'].get('imageReference')
        if image is not None:
            new_result['image'] = {
                'publisher': image['publisher'],
                'sku': image['sku'],
                'offer': image['offer'],
                'version': image['version']
            }

        vhd = result['properties']['storageProfile']['osDisk'].get('vhd')
        if vhd is not None:
            url = urlparse(vhd['uri'])
            new_result['storage_account_name'] = url.netloc.split('.')[0]
            new_result['storage_container_name'] = url.path.split('/')[1]
            new_result['storage_blob_name'] = url.path.split('/')[-1]

        new_result['os_disk_caching'] = result['properties']['storageProfile']['osDisk']['caching']
        new_result['os_type'] = result['properties']['storageProfile']['osDisk']['osType']
        new_result['data_disks'] = []
        disks = result['properties']['storageProfile']['dataDisks']
        for disk_index in range(len(disks)):
            new_result['data_disks'].append({
                'lun': disks[disk_index]['lun'],
                'disk_size_gb': disks[disk_index]['diskSizeGB'],
                'managed_disk_type': disks[disk_index]['managedDisk']['storageAccountType'],
                'caching': disks[disk_index]['caching']
            })

        new_result['network_interface_names'] = []
        nics = result['properties']['networkProfile']['networkInterfaces']
        for nic_index in range(len(nics)):
            new_result['network_interface_names'].append(re.sub('.*networkInterfaces/', '', nics[nic_index]['id']))

        new_result['tags'] = vm.tags
        return new_result


def main():
    AzureRMVirtualMachineFacts()


if __name__ == '__main__':
    main()
