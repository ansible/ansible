#!/usr/bin/python
#
# Copyright (c) 2018 Gustavo Muniz do Carmo <gustavo@esign.com.br>
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

version_added: "2.6"

short_description: Get virtual machine facts.

description:
  - Get facts for all virtual machines of a resource group.

options:
  resource_group:
    description:
      - Name of the resource group containing the virtual machines.
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
            "hardwareProfile": {
                "vmSize": "Standard_A0"
            },
            "instanceView": {
                "disks": [
                    {
                        "name": "vm.vhd",
                        "statuses": [
                            {
                                "code": "ProvisioningState/succeeded",
                                "displayStatus": "Provisioning succeeded",
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
                                "displayStatus": "Provisioning succeeded",
                                "level": "Info",
                                "message": "Enable succeeded"
                            }
                        ],
                        "type": "Microsoft.EnterpriseCloud.Monitoring.OmsAgentForLinux",
                        "typeHandlerVersion": "1.4.60.2"
                    }
                ],
                "statuses": [
                    {
                        "code": "ProvisioningState/succeeded",
                        "displayStatus": "Provisioning succeeded",
                        "level": "Info",
                        "time": "2018-04-03T22:24:05.21931199999999998Z"
                    },
                    {
                        "code": "PowerState/running",
                        "displayStatus": "VM running",
                        "level": "Info"
                    }
                ],
                "vmAgent": {
                    "extensionHandlers": [
                        {
                            "status": {
                                "code": "ProvisioningState/succeeded",
                                "displayStatus": "Ready",
                                "level": "Info",
                                "message": "Plugin enabled"
                            },
                            "type": "Microsoft.EnterpriseCloud.Monitoring.OmsAgentForLinux",
                            "typeHandlerVersion": "1.4.60.2"
                        }
                    ],
                    "statuses": [
                        {
                            "code": "ProvisioningState/succeeded",
                            "displayStatus": "Ready",
                            "level": "Info",
                            "message": "Guest Agent is running",
                            "time": "2018-04-04T14:13:41.000Z"
                        }
                    ],
                    "vmAgentVersion": "2.2.25"
                }
            },
            "networkProfile": {
                "networkInterfaces": [{
                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/vm-nic",
                    "name": "vm-nic",
                    "properties": {
                        "dnsSettings": {
                            "appliedDnsServers": [],
                            "dnsServers": [],
                            "internalDomainNameSuffix": "yp5qqpscrrgu3kalovpyi1rqoa.nx.internal.cloudapp.net"
                        },
                        "enableAcceleratedNetworking": false,
                        "enableIPForwarding": false,
                        "ipConfigurations": [{
                            "etag": "W/'6d0bd817-d2f8-4b21-98ff-b33abcc9b11b'",
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/vm-nic/ipConfigurations/ipconfig1",
                            "name": "ipconfig1",
                            "properties": {
                                "primary": true,
                                "privateIPAddress": "10.0.1.4",
                                "privateIPAddressVersion": "IPv4",
                                "privateIPAllocationMethod": "Dynamic",
                                "provisioningState": "Succeeded",
                                "publicIPAddress": {
                                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/vm-ip",
                                    "name": "vm-ip",
                                    "properties": {
                                        "dnsSettings": {
                                            "domainNameLabel": "vm-domain",
                                            "fqdn": "vm-domain.brazilsouth.cloudapp.azure.com"
                                        },
                                        "idleTimeoutInMinutes": 4,
                                        "ipAddress": "191.232.165.120",
                                        "ipConfiguration": {
                                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Micro.../nInterfaces/vm-nic/ipConfigurations/ipconfig1"
                                        },
                                        "provisioningState": "Succeeded",
                                        "publicIPAddressVersion": "IPv4",
                                        "publicIPAllocationMethod": "Dynamic",
                                        "resourceGuid": "4ac0bc74-3a5d-4ea1-8ceb-db5aaa1725d7"
                                    }
                                },
                                "subnet": {
                                    "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/Testing-vnet/subnets/default"
                                }
                            }
                        }],
                        "macAddress": "00-0D-3A-C1-57-96",
                        "networkSecurityGroup": {
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/vm-nsg"
                        },
                        "primary": true,
                        "provisioningState": "Succeeded",
                        "resourceGuid": "7212cde7-8c8e-40a2-81fd-9c0fe5777300",
                        "virtualMachine": {
                            "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm"
                        }
                    }
                }]
            },
            "osProfile": {
                "adminUsername": "ubuntu",
                "computerName": "vm",
                "linuxConfiguration": {
                    "disablePasswordAuthentication": true,
                    "ssh": {
                        "publicKeys": [
                            {
                                "keyData": "ssh-rsa XXXXX",
                                "path": "/home/ubuntu/.ssh/authorized_keys"
                            }
                        ]
                    }
                },
                "secrets": []
            },
            "provisioningState": "Succeeded",
            "storageProfile": {
                "dataDisks": [],
                "imageReference": {
                    "offer": "UbuntuServer",
                    "publisher": "Canonical",
                    "sku": "16.04-LTS",
                    "version": "16.04.201801220"
                },
                "osDisk": {
                    "caching": "ReadOnly",
                    "createOption": "FromImage",
                    "diskSizeGB": 30,
                    "name": "vm.vhd",
                    "osType": "Linux",
                    "vhd": {
                        "uri": "https://ubuntu1842.blob.core.windows.net/vhds/vm.vhd"
                    }
                }
            },
            "vmId": "77f0006c-0874-42ca-9ec9-e920b36263cf"
        },
        "resources": [
            {
                "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm/extensions/OmsAgentForLinux",
                "location": "brazilsouth",
                "name": "OmsAgentForLinux",
                "properties": {
                    "autoUpgradeMinorVersion": true,
                    "provisioningState": "Succeeded",
                    "publisher": "Microsoft.EnterpriseCloud.Monitoring",
                    "settings": {
                        "azureResourceId": "/subscriptions/XXXXX/resourcegroups/Testing/providers/microsoft.compute/virtualmachines/vm",
                        "stopOnMultipleConnections": true,
                        "workspaceId": "43ac2095-42c7-4488-924f-bc4cbca63f8d"
                    },
                    "type": "OmsAgentForLinux",
                    "typeHandlerVersion": "1.0"
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


AZURE_OBJECT_CLASS = 'VirtualMachine'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str'),
            name=dict(type='str'),
            tags=dict(type='list'),
            auth_source=dict(type='str', choices=['auto', 'cli', 'env', 'credential_file', 'msi'], default='auto'),
            cloud_environment=dict(type='str', default='AzureCloud')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_virtualmachines=[])
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
        except CloudError:
            pass

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
        result['id'] = vm.id
        result['name'] = vm.name
        result['type'] = vm.type
        result['location'] = vm.location
        result['tags'] = vm.tags

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
                        pip = self.network_client.public_ip_addresses.get(self.resource_group,
                                                                          pipid_dict['publicIPAddresses'])
                    except Exception as exc:
                        self.fail("Error fetching public ip {0} - {1}".format(pipid_dict['publicIPAddresses'],
                                                                              str(exc)))
                    pip_dict = self.serialize_obj(pip, 'PublicIPAddress')
                    config['properties']['publicIPAddress']['name'] = pipid_dict['publicIPAddresses']
                    config['properties']['publicIPAddress']['properties'] = pip_dict['properties']

        self.log(result, pretty_print=True)
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
