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
    format:
        description:
            - Format of the data returned.
            - If C(raw) is selected information will be returned in raw format from Azure Python SDK.
            - If C(curated) is selected the structure will be identical to input parameters of azure_rm_virtualmachine_scaleset module.
            - In Ansible 2.5 and lower facts are always returned in raw format.
        default: 'curated'
        choices:
            - 'curated'
            - 'raw'

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
azure_virtualmachines:
    description: List of resource group's virtual machines dicts.
    returned: always
    type: list
    example: [{
        "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm",
        "location": "brazilsouth",
        "name": "vm",
        "powerstate": "running",
        "properties": {
            "hardware_profile": {
                "vm_size": "Standard_A0"
            },
            "instance_view": {
                "disks": [
                    {
                        "name": "vm.vhd",
                        "statuses": [
                            {
                                "code": "ProvisioningState/succeeded",
                                "display_status": "Provisioning succeeded",
                                "level": "Info",
                                "time": "2018-04-03T22:22:13.933101Z"
                            }
                        ]
                    }
                ],
                "extensions": [
                    {
                        "name": "OmsAgentForLinux",
                        "statuses": [
                            {
                                "code": "ProvisioningState/succeeded",
                                "display_status": "Provisioning succeeded",
                                "level": "Info",
                                "message": "Enable succeeded"
                            }
                        ],
                        "type": "Microsoft.EnterpriseCloud.Monitoring.OmsAgentForLinux",
                        "type_handler_version": "1.4.60.2"
                    }
                ],
                "statuses": [
                    {
                        "code": "ProvisioningState/succeeded",
                        "display_status": "Provisioning succeeded",
                        "level": "Info",
                        "time": "2018-04-03T22:24:05.21931199999999998Z"
                    },
                    {
                        "code": "PowerState/running",
                        "display_status": "VM running",
                        "level": "Info"
                    }
                ],
                "vm_agent": {
                    "extension_handlers": [
                        {
                            "status": {
                                "code": "ProvisioningState/succeeded",
                                "display_status": "Ready",
                                "level": "Info",
                                "message": "Plugin enabled"
                            },
                            "type": "Microsoft.EnterpriseCloud.Monitoring.OmsAgentForLinux",
                            "type_handler_version": "1.4.60.2"
                        }
                    ],
                    "statuses": [
                        {
                            "code": "ProvisioningState/succeeded",
                            "display_status": "Ready",
                            "level": "Info",
                            "message": "Guest Agent is running",
                            "time": "2018-04-04T14:13:41.000Z"
                        }
                    ],
                    "vm_agent_version": "2.2.25"
                }
            },
            "network_profile": {
                "network_interfaces": [{
                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/vm-nic",
                    "name": "vm-nic",
                    "properties": {
                        "dns_settings": {
                            "applied_dns_servers": [],
                            "dns_servers": [],
                            "internal_domain_name_suffix": "yp5qqpscrrgu3kalovpyi1rqoa.nx.internal.cloudapp.net"
                        },
                        "enable_accelerated_networking": false,
                        "enable_ip_forwarding": false,
                        "ip_configurations": [{
                            "etag": "W/'6d0bd817-d2f8-4b21-98ff-b33abcc9b11b'",
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/vm-nic/ipConfigurations/ipconfig1",
                            "name": "ipconfig1",
                            "properties": {
                                "primary": true,
                                "private_ip_address": "10.0.1.4",
                                "private_ip_address_version": "IPv4",
                                "private_ip_allocation_method": "Dynamic",
                                "provisioning_state": "Succeeded",
                                "public_ip_address": {
                                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/vm-ip",
                                    "name": "vm-ip",
                                    "properties": {
                                        "dns_settings": {
                                            "domain_name_label": "vm-domain",
                                            "fqdn": "vm-domain.brazilsouth.cloudapp.azure.com"
                                        },
                                        "idle_timeout_in_minutes": 4,
                                        "ip_address": "191.232.165.120",
                                        "ip_configuration": {
                                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Micro.../nInterfaces/vm-nic/ipConfigurations/ipconfig1"
                                        },
                                        "provisioning_state": "Succeeded",
                                        "public_ip_address_version": "IPv4",
                                        "public_ip_allocation_method": "Dynamic",
                                        "resource_guid": "4ac0bc74-3a5d-4ea1-8ceb-db5aaa1725d7"
                                    }
                                },
                                "subnet": {
                                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/Testing-vnet/subnets/default"
                                }
                            }
                        }],
                        "mac_address": "00-0D-3A-C1-57-96",
                        "network_security_group": {
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/vm-nsg"
                        },
                        "primary": true,
                        "provisioning_state": "Succeeded",
                        "resource_guid": "7212cde7-8c8e-40a2-81fd-9c0fe5777300",
                        "virtual_machine": {
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm"
                        }
                    }
                }]
            },
            "os_profile": {
                "admin_username": "ubuntu",
                "computer_name": "vm",
                "linux_configuration": {
                    "disable_password_authentication": true,
                    "ssh": {
                        "public_keys": [
                            {
                                "key_data": "ssh-rsa XXXXX",
                                "path": "/home/ubuntu/.ssh/authorized_keys"
                            }
                        ]
                    }
                },
                "secrets": []
            },
            "provisioning_state": "Succeeded",
            "storage_profile": {
                "data_disks": [],
                "image_reference": {
                    "offer": "UbuntuServer",
                    "publisher": "Canonical",
                    "sku": "16.04-LTS",
                    "version": "16.04.201801220"
                },
                "os_disk": {
                    "caching": "ReadOnly",
                    "create_option": "FromImage",
                    "disk_size_gb": 30,
                    "name": "vm.vhd",
                    "os_type": "Linux",
                    "vhd": {
                        "uri": "https://ubuntu1842.blob.core.windows.net/vhds/vm.vhd"
                    }
                }
            },
            "vm_id": "77f0006c-0874-42ca-9ec9-e920b36263cf"
        },
        "resources": [
            {
                "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm/extensions/OmsAgentForLinux",
                "location": "brazilsouth",
                "name": "OmsAgentForLinux",
                "properties": {
                    "auto_upgrade_minor_version": true,
                    "provisioning_state": "Succeeded",
                    "publisher": "Microsoft.EnterpriseCloud.Monitoring",
                    "settings": {
                        "azure_resource_id": "/subscriptions/XXXXX/resourcegroups/Testing/providers/microsoft.compute/virtualmachines/vm",
                        "stop_on_multiple_connections": true,
                        "workspace_id": "43ac2095-42c7-4488-924f-bc4cbca63f8d"
                    },
                    "type": "OmsAgentForLinux",
                    "type_handler_version": "1.0"
                },
                "type": "Microsoft.Compute/virtualMachines/extensions"
            }
        ],
        "tags": {
            "cluster_name": "cluster"
        },
        "type": "Microsoft.Compute/virtualMachines"
    }]
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
            tags=dict(type='list'),
            format=dict(
                type='str',
                choices=['curated',
                         'raw'],
                default='curated'
            )
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_virtualmachines=[])
        )

        self.resource_group = None
        self.name = None
        self.tags = None
        self.format = None

        super(AzureRMVirtualMachineFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")
        if self.name:
            self.results['ansible_facts']['azure_virtualmachines'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_virtualmachines'] = self.list_items()

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
        if self.format == 'curated':
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
        else:
            result['powerstate'] = dict()
            if vm.instance_view:
                result['powerstate'] = next((s.code.replace('PowerState/', '')
                                            for s in vm.instance_view.statuses if s.code.startswith('PowerState')), None)

            # Expand network interfaces to include config properties
            for interface in vm.network_profile.network_interfaces:
                int_dict = azure_id_to_dict(interface.id)
                nic = self.get_network_interface(int_dict['networkInterfaces'])
                for interface_dict in result['properties']['networkProfile']['networkInterfaces']:
                    if interface_dict['id'] == interface.id:
                        nic_dict = self.serialize_obj(nic, 'NetworkInterface')
                        interface_dict['name'] = int_dict['networkInterfaces']
                        interface_dict['properties'] = nic_dict['properties']

            # Expand public IPs to include config properties
            for interface in result['properties']['networkProfile']['networkInterfaces']:
                for config in interface['properties']['ipConfigurations']:
                    if config['properties'].get('publicIPAddress'):
                        pipid_dict = azure_id_to_dict(config['properties']['publicIPAddress']['id'])
                        try:
                            pip = self.network_client.public_ip_addresses.get(self.resource_group, pipid_dict['publicIPAddresses'])
                        except Exception as exc:
                            self.fail("Error fetching public ip {0} - {1}".format(pipid_dict['publicIPAddresses'], str(exc)))
                        pip_dict = self.serialize_obj(pip, 'PublicIPAddress')
                        config['properties']['publicIPAddress']['name'] = pipid_dict['publicIPAddresses']
                        config['properties']['publicIPAddress']['properties'] = pip_dict['properties']

            return result

    def get_network_interface(self, name):
        try:
            nic = self.network_client.network_interfaces.get(self.resource_group, name)
            return nic
        except Exception as exc:
            self.fail("Error fetching network interface {0} - {1}".format(name, str(exc)))


def main():
    AzureRMVirtualMachineFacts()

if __name__ == '__main__':
    main()
