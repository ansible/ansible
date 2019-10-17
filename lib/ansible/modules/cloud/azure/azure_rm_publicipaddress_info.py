#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_publicipaddress_info

version_added: "2.9"

short_description: Get public IP facts

description:
    - Get facts for a specific public IP or all public IPs within a resource group.

options:
    name:
        description:
            - Only show results for a specific Public IP.
    resource_group:
        description:
            - Limit results by resource group. Required when using name parameter.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = '''
    - name: Get facts for one Public IP
      azure_rm_publicipaddress_info:
        resource_group: myResourceGroup
        name: publicip001

    - name: Get facts for all Public IPs within a resource groups
      azure_rm_publicipaddress_info:
        resource_group: myResourceGroup
'''

RETURN = '''
azure_publicipaddresses:
    description:
        - List of public IP address dicts.
        - Please note that this option will be deprecated in 2.10 when curated format will become the only supported format.
    returned: always
    type: list
    example: [{
        "etag": 'W/"a31a6d7d-cb18-40a5-b16d-9f4a36c1b18a"',
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/pip2001",
        "location": "eastus2",
        "name": "pip2001",
        "properties": {
            "idleTimeoutInMinutes": 4,
            "provisioningState": "Succeeded",
            "publicIPAllocationMethod": "Dynamic",
            "resourceGuid": "29de82f4-a7da-440e-bd3d-9cabb79af95a"
        },
        "type": "Microsoft.Network/publicIPAddresses"
    }]
publicipaddresses:
    description:
        - List of publicipaddress.
        - Contains the detail which matches azure_rm_publicipaddress parameters.
        - Returned when the format parameter set to curated.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: /subscriptions/xxx---xxxxx/resourceGroups/v-xisuRG/providers/Microsoft.Network/publicIPAddresses/pipb57dc95224
        name:
            description:
                - Name of the public IP address.
            returned: always
            type: str
            sample: pipb57dc95224
        type:
            description:
                - Resource type.
            returned: always
            type: str
            sample: "Microsoft.Network/publicIPAddresses"
        location:
            description:
                - Resource location.
            returned: always
            type: str
            sample: eastus
        tags:
            description:
                - Resource tags.
            returned: always
            type: dict
            sample: {
                    "delete": "on-exit",
                    "testing": "testing"
                    }
        allocation_method:
            description:
                - The public IP allocation method.
                - Possible values are C(static) and C(dynamic).
            returned: always
            type: str
            sample: static
        version:
            description:
                - The public IP address version.
                - Possible values are C(ipv4) and C(ipv6).
            returned: always
            type: str
            sample: ipv4
        dns_settings:
            description:
                - The FQDN of the DNS record associated with the public IP address.
            returned: always
            type: dict
            sample: {
                    "domain_name_label": "ansible-b57dc95985712e45eb8b9c2e",
                    "fqdn": "ansible-b57dc95985712e45eb8b9c2e.eastus.cloudapp.azure.com",
                    "reverse_fqdn": null
                    }
        ip_tags:
            description:
                - The list of tags associated with the public IP address.
            returned: always
            type: list
            sample: [
                    {
                        "type": "FirstPartyUsage",
                        "value": "Storage"
                    }
                    ]
        ip_address:
            description:
                - The Public IP Prefix this Public IP Address should be allocated from.
            returned: always
            type: str
            sample: 40.121.144.14
        idle_timeout:
            description:
                - The idle timeout of the public IP address.
            returned: always
            type: int
            sample: 4
        provisioning_state:
            description:
                - The provisioning state of the PublicIP resource.
                - Possible values is C(Succeeded).
            returned: always
            type: str
            sample: Succeeded
        etag:
            description:
                - A unique read-only string that changes whenever the resource is updated.
            returned: always
            type: str
            sample: "W/'1905ee13-7623-45b1-bc6b-4a12b2fb9d15'"
        sku:
            description:
                - The public IP address SKU.
            returned: always
            type: str
            sample: Basic
'''
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

AZURE_OBJECT_CLASS = 'PublicIp'


class AzureRMPublicIPInfo(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMPublicIPInfo, self).__init__(self.module_arg_spec,
                                                  supports_tags=False,
                                                  facts_module=True)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_publicipaddress_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_publicipaddress_facts' module has been renamed to 'azure_rm_publicipaddress_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        result = []
        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            result = self.get_item()
        elif self.resource_group:
            result = self.list_resource_group()
        else:
            result = self.list_all()

        raw = self.filter(result)

        if is_old_facts:
            self.results['ansible_facts'] = {
                'azure_publicipaddresses': self.serialize(raw),
            }
        self.results['publicipaddresses'] = self.format(raw)

        return self.results

    def format(self, raw):
        return [self.pip_to_dict(item) for item in raw]

    def serialize(self, raw):
        results = []
        for item in raw:
            pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
            pip['name'] = item.name
            pip['type'] = item.type
            results.append(pip)
        return results

    def filter(self, response):
        return [item for item in response if self.has_tags(item.tags, self.tags)]

    # duplicate with azure_rm_publicipaddress
    def pip_to_dict(self, pip):
        result = dict(
            id=pip.id,
            name=pip.name,
            type=pip.type,
            location=pip.location,
            tags=pip.tags,
            allocation_method=pip.public_ip_allocation_method.lower(),
            version=pip.public_ip_address_version.lower(),
            dns_settings=dict(),
            ip_tags=dict(),
            ip_address=pip.ip_address,
            idle_timeout=pip.idle_timeout_in_minutes,
            provisioning_state=pip.provisioning_state,
            etag=pip.etag,
            sku=pip.sku.name
        )
        if pip.dns_settings:
            result['dns_settings']['domain_name_label'] = pip.dns_settings.domain_name_label
            result['dns_settings']['fqdn'] = pip.dns_settings.fqdn
            result['dns_settings']['reverse_fqdn'] = pip.dns_settings.reverse_fqdn
        if pip.ip_tags:
            result['ip_tags'] = [dict(type=x.ip_tag_type, value=x.tag) for x in pip.ip_tags]
        return result

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        try:
            item = self.network_client.public_ip_addresses.get(self.resource_group, self.name)
        except CloudError:
            pass
        return [item] if item else []

    def list_resource_group(self):
        self.log('List items in resource groups')
        try:
            response = self.network_client.public_ip_addresses.list(self.resource_group)
        except AzureHttpError as exc:
            self.fail("Error listing items in resource groups {0} - {1}".format(self.resource_group, str(exc)))
        return response

    def list_all(self):
        self.log('List all items')
        try:
            response = self.network_client.public_ip_addresses.list_all()
        except AzureHttpError as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))
        return response


def main():
    AzureRMPublicIPInfo()


if __name__ == '__main__':
    main()
