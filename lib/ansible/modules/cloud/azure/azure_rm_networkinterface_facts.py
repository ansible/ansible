#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_networkinterface_facts

version_added: "2.1"

short_description: Get network interface facts.

description:
    - Get facts for a specific network interface or all network interfaces within a resource group.

options:
    name:
        description:
            - Only show results for a specific network interface.
        required: false
        default: null
    resource_group:
        description:
            - Name of the resource group containing the network interface(s). Required when searching by name.
        required: false
        default: null
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        required: false
        default: null

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Get facts for one network interface
      azure_rm_networkinterface_facts:
        resource_group: Testing
        name: nic001

    - name: Get network interfaces within a resource group
      azure_rm_networkinterface_facts:
        resource_group: Testing

    - name: Get network interfaces by tag
      azure_rm_networkinterface_facts:
        resource_group: Testing
        tags:
          - testing
          - foo:bar
'''

RETURN = '''
azure_networkinterfaces:
    description: List of network interface dicts.
    returned: always
    type: list
    example: [{
        "dns_settings": {
            "applied_dns_servers": [],
            "dns_servers": [],
            "internal_dns_name_label": null,
            "internal_fqdn": null
        },
        "enable_ip_forwarding": false,
        "etag": 'W/"59726bfc-08c4-44ed-b900-f6a559876a9d"',
        "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/nic003",
        "ip_configuration": {
            "name": "default",
            "private_ip_address": "10.10.0.4",
            "private_ip_allocation_method": "Dynamic",
            "public_ip_address": {
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/publicip001",
                "name": "publicip001"
            },
            "subnet": {
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/vnet001/subnets/subnet001",
                "name": "subnet001",
                "virtual_network_name": "vnet001"
            }
        },
        "location": "westus",
        "mac_address": null,
        "name": "nic003",
        "network_security_group": {
            "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/secgroup001",
            "name": "secgroup001"
        },
        "primary": null,
        "provisioning_state": "Succeeded",
        "tags": {},
        "type": "Microsoft.Network/networkInterfaces"
    }]
'''  # NOQA
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'NetworkInterface'


class AzureRMNetworkInterfaceFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_networkinterfaces=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMNetworkInterfaceFacts, self).__init__(self.module_arg_spec,
                                                           supports_tags=False,
                                                           facts_module=True
                                                           )

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['ansible_facts']['azure_networkinterfaces'] = self.get_item()
        elif self.resource_group:
            self.results['ansible_facts']['azure_networkinterfaces'] = self.list_resource_group()
        else:
            self.results['ansible_facts']['azure_networkinterfaces'] = self.list_all()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        result = []
        item = None
        try:
            item = self.network_client.network_interfaces.get(self.resource_group, self.name)
        except:
            pass

        if item and self.has_tags(item.tags, self.tags):
            nic = self.serialize_obj(item, AZURE_OBJECT_CLASS)
            result = [nic]

        return result

    def list_resource_group(self):
        self.log('List for resource group')
        try:
            response = self.network_client.network_interfaces.list(self.resource_group)
        except Exception as exc:
            self.fail("Error listing by resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                nic = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                results.append(nic)
        return results

    def list_all(self):
        self.log('List all')
        try:
            response = self.network_client.network_interfaces.list_all()
        except Exception as exc:
            self.fail("Error listing all - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                nic = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                results.append(nic)
        return results


def main():
    AzureRMNetworkInterfaceFacts()

if __name__ == '__main__':
    main()
