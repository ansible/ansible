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

version_added: "2.5"

short_description: Get virtual machine facts.

description:
  - Get facts for all virtual machines of a resource group.

options:
  resource_group:
    description:
      - Name of the resource group containing the virtual machines.
    required: true
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
        "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm-example",
        "location": "brazilsouth",
        "name": "vm-example",
        "properties": {
            "hardwareProfile": {
                "vmSize": "Standard_A0"
            },
            "instanceView": {
                "disks": [
                    {
                        "name": "vm-example.vhd",
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
                "networkInterfaces": [
                    {
                        "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/vm-example-nic"
                    }
                ]
            },
            "osProfile": {
                "adminUsername": "ubuntu",
                "computerName": "vm-example",
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
                    "name": "vm-example.vhd",
                    "osType": "Linux",
                    "vhd": {
                        "uri": "https://ubuntu1842.blob.core.windows.net/vhds/vm-example.vhd"
                    }
                }
            },
            "vmId": "77f0006c-0874-42ca-9ec9-e920b36263cf"
        },
        "resources": [
            {
                "id": "/subscriptions/XXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/vm-example/extensions/OmsAgentForLinux",
                "location": "brazilsouth",
                "name": "OmsAgentForLinux",
                "properties": {
                    "autoUpgradeMinorVersion": true,
                    "provisioningState": "Succeeded",
                    "publisher": "Microsoft.EnterpriseCloud.Monitoring",
                    "settings": {
                        "azureResourceId": "/subscriptions/XXXXX/resourcegroups/Testing/providers/microsoft.compute/virtualmachines/vm-example",
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

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'VirtualMachine'


class AzureRMVirtualMachineFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_virtualmachines=[])
        )

        self.resource_group = None
        self.tags = None

        super(AzureRMVirtualMachineFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.results['ansible_facts']['azure_virtualmachines'] = self.list_items()

        return self.results

    def list_items(self):
        self.log('List all items')
        try:
            items = self.compute_client.virtual_machines.list(self.resource_group)
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in items:
            if self.has_tags(item.tags, self.tags):
                vm = self.compute_client.virtual_machines.get(self.resource_group, item.name, expand='instanceview')
                results.append(self.serialize_obj(vm, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMVirtualMachineFacts()

if __name__ == '__main__':
    main()
