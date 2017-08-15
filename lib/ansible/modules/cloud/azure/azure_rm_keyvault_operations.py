#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvault_operations
version_added: "2.4"
short_description: Use Azure KeyVault Certs/Secrets/Keys.
description:
    - Create, update or delete a subnet within a given virtual network. Allows setting and updating the address
      prefix CIDR, which must be valid within the context of the virtual network. Use the azure_rm_networkinterface
      module to associate interfaces with the subnet and assign specific IP addresses.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    name:
        description:
            - Name of the subnet.
        required: true
    address_prefix_cidr:
        description:
            - CIDR defining the IPv4 address space of the subnet. Must be valid within the context of the
              virtual network.
        required: true
        aliases:
            - address_prefix
    security_group_name:
        description:
            - Name of an existing security group with which to associate the subnet.
        required: false
        default: null
        aliases:
            - security_group
    state:
        description:
            - Assert the state of the subnet. Use 'present' to create or update a subnet and
              'absent' to delete a subnet.
        required: false
        default: present
        choices:
            - absent
            - present
    virtual_network_name:
        description:
            - Name of an existing virtual network with which the subnet is or will be associated.
        required: true
        aliases:
            - virtual_network

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Create a subnet
      azure_rm_subnet:
        name: foobar
        virtual_network_name: My_Virtual_Network
        resource_group: Testing
        address_prefix_cidr: "10.1.0.0/24"

    - name: Delete a subnet
      azure_rm_subnet:
        name: foobar
        virtual_network_name: My_Virtual_Network
        resource_group: Testing
        state: absent
'''

RETURN = '''
state:
    description: Current state of the subnet.
    returned: success
    type: complex
    contains:
        address_prefix:
          description: IP address CIDR.
          type: str
          example: "10.1.0.0/16"
        id:
          description: Subnet resource path.
          type: str
          example: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/My_Virtual_Network/subnets/foobar"
        name:
          description: Subnet name.
          type: str
          example: "foobar"
        network_security_group:
          type: complex
          contains:
            id:
              description: Security group resource identifier.
              type: str
              example: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/secgroupfoo"
            name:
              description: Name of the security group.
              type: str
              example: "secgroupfoo"
        provisioning_state:
          description: Success or failure of the provisioning event.
          type: str
          example: "Succeeded"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN, azure_id_to_dict

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import Subnet, NetworkSecurityGroup
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMKeyVaultOperations(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            virtual_network_name=dict(type='str', required=True, aliases=['virtual_network']),
            address_prefix_cidr=dict(type='str', aliases=['address_prefix']),
            security_group_name=dict(type='str', aliases=['security_group']),
        )

        required_if = [
            ('state', 'present', ['address_prefix_cidr'])
        ]

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.virtual_etwork_name = None
        self.address_prefix_cidr = None
        self.security_group_name = None

        super(AzureRMKeyVaultOperations, self).__init__(self.module_arg_spec,
                                            supports_check_mode=True,
                                            required_if=required_if)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])


def main():
    AzureRMKeyVaultOperations()

if __name__ == '__main__':
    main()
