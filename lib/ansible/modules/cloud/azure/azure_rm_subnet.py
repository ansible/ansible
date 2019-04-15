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
module: azure_rm_subnet
version_added: "2.1"
short_description: Manage Azure subnets.
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
        aliases:
            - address_prefix
    security_group:
        description:
            - Existing security group with which to associate the subnet.
            - It can be the security group name which is in the same resource group.
            - It can be the resource Id.
            - It can be a dict which contains C(name) and C(resource_group) of the security group.
        aliases:
            - security_group_name
    state:
        description:
            - Assert the state of the subnet. Use C(present) to create or update a subnet and
              C(absent) to delete a subnet.
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
    route_table:
        description:
            - The reference of the RouteTable resource.
            - It can accept both a str or a dict.
            - The str can be the name or resource id of the route table.
            - The dict can contains C(name) and C(resource_group) of the route_table.
        version_added: "2.7"
    service_endpoints:
        description:
            - An array of service endpoints.
        type: list
        suboptions:
            service:
                description:
                    - The type of the endpoint service.
                required: True
            locations:
                description:
                    - A list of locations.
                type: list
        version_added: "2.8"

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Create a subnet
      azure_rm_subnet:
        resource_group: myResourceGroup
        virtual_network_name: myVirtualNetwork
        name: mySubnet
        address_prefix_cidr: "10.1.0.0/24"

    - name: Create a subnet refer nsg from other resource group
      azure_rm_subnet:
        resource_group: myResourceGroup
        virtual_network_name: myVirtualNetwork
        name: mySubnet
        address_prefix_cidr: "10.1.0.0/16"
        security_group:
          name: secgroupfoo
          resource_group: mySecondResourceGroup
        route_table: route

    - name: Delete a subnet
      azure_rm_subnet:
        resource_group: myResourceGroup
        virtual_network_name: myVirtualNetwork
        name: mySubnet
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
          example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVirtualNetwork/subnets/mySubnet"
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
              example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/secgroupfoo"
            name:
              description: Name of the security group.
              type: str
              example: "secgroupfoo"
        provisioning_state:
          description: Success or failure of the provisioning event.
          type: str
          example: "Succeeded"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN, azure_id_to_dict, format_resource_id

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


def subnet_to_dict(subnet):
    result = dict(
        id=subnet.id,
        name=subnet.name,
        provisioning_state=subnet.provisioning_state,
        address_prefix=subnet.address_prefix,
        network_security_group=dict(),
        route_table=dict()
    )
    if subnet.network_security_group:
        id_keys = azure_id_to_dict(subnet.network_security_group.id)
        result['network_security_group']['id'] = subnet.network_security_group.id
        result['network_security_group']['name'] = id_keys['networkSecurityGroups']
        result['network_security_group']['resource_group'] = id_keys['resourceGroups']
    if subnet.route_table:
        id_keys = azure_id_to_dict(subnet.route_table.id)
        result['route_table']['id'] = subnet.route_table.id
        result['route_table']['name'] = id_keys['routeTables']
        result['route_table']['resource_group'] = id_keys['resourceGroups']
    if subnet.service_endpoints:
        result['service_endpoints'] = [{'service': item.service, 'locations': item.locations or []} for item in subnet.service_endpoints]
    return result


class AzureRMSubnet(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            virtual_network_name=dict(type='str', required=True, aliases=['virtual_network']),
            address_prefix_cidr=dict(type='str', aliases=['address_prefix']),
            security_group=dict(type='raw', aliases=['security_group_name']),
            route_table=dict(type='raw'),
            service_endpoints=dict(
                type='list'
            )
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.virtual_network_name = None
        self.address_prefix_cidr = None
        self.security_group = None
        self.route_table = None
        self.service_endpoints = None

        super(AzureRMSubnet, self).__init__(self.module_arg_spec,
                                            supports_check_mode=True,
                                            supports_tags=False)

    def exec_module(self, **kwargs):

        nsg = None
        subnet = None

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.address_prefix_cidr and not CIDR_PATTERN.match(self.address_prefix_cidr):
            self.fail("Invalid address_prefix_cidr value {0}".format(self.address_prefix_cidr))

        nsg = dict()
        if self.security_group:
            nsg = self.parse_nsg()

        route_table = dict()
        if self.route_table:
            route_table = self.parse_resource_to_dict(self.route_table)
            self.route_table = format_resource_id(val=route_table['name'],
                                                  subscription_id=route_table['subscription_id'],
                                                  namespace='Microsoft.Network',
                                                  types='routeTables',
                                                  resource_group=route_table['resource_group'])

        results = dict()
        changed = False

        try:
            self.log('Fetching subnet {0}'.format(self.name))
            subnet = self.network_client.subnets.get(self.resource_group,
                                                     self.virtual_network_name,
                                                     self.name)
            self.check_provisioning_state(subnet, self.state)
            results = subnet_to_dict(subnet)

            if self.state == 'present':
                if self.address_prefix_cidr and results['address_prefix'] != self.address_prefix_cidr:
                    self.log("CHANGED: subnet {0} address_prefix_cidr".format(self.name))
                    changed = True
                    results['address_prefix'] = self.address_prefix_cidr

                if self.security_group is not None and results['network_security_group'].get('id') != nsg.get('id'):
                    self.log("CHANGED: subnet {0} network security group".format(self.name))
                    changed = True
                    results['network_security_group']['id'] = nsg.get('id')
                    results['network_security_group']['name'] = nsg.get('name')
                if self.route_table is not None and self.route_table != results['route_table'].get('id'):
                    changed = True
                    results['route_table']['id'] = self.route_table
                    self.log("CHANGED: subnet {0} route_table to {1}".format(self.name, route_table.get('name')))

                if self.service_endpoints:
                    oldd = {}
                    for item in self.service_endpoints:
                        name = item['service']
                        locations = item.get('locations') or []
                        oldd[name] = {'service': name, 'locations': locations.sort()}
                    newd = {}
                    if 'service_endpoints' in results:
                        for item in results['service_endpoints']:
                            name = item['service']
                            locations = item.get('locations') or []
                            newd[name] = {'service': name, 'locations': locations.sort()}
                    if newd != oldd:
                        changed = True
                        results['service_endpoints'] = self.service_endpoints

            elif self.state == 'absent':
                changed = True
        except CloudError:
            # the subnet does not exist
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if not self.check_mode:

            if self.state == 'present' and changed:
                if not subnet:
                    # create new subnet
                    if not self.address_prefix_cidr:
                        self.fail('address_prefix_cidr is not set')
                    self.log('Creating subnet {0}'.format(self.name))
                    subnet = self.network_models.Subnet(
                        address_prefix=self.address_prefix_cidr
                    )
                    if nsg:
                        subnet.network_security_group = self.network_models.NetworkSecurityGroup(id=nsg.get('id'))
                    if self.route_table:
                        subnet.route_table = self.network_models.RouteTable(id=self.route_table)
                else:
                    # update subnet
                    self.log('Updating subnet {0}'.format(self.name))
                    subnet = self.network_models.Subnet(
                        address_prefix=results['address_prefix']
                    )
                    if results['network_security_group'].get('id') is not None:
                        subnet.network_security_group = self.network_models.NetworkSecurityGroup(id=results['network_security_group'].get('id'))
                    if results['route_table'].get('id') is not None:
                        subnet.route_table = self.network_models.RouteTable(id=results['route_table'].get('id'))

                    if results.get('service_endpoints') is not None:
                        subnet.service_endpoints = results['service_endpoints']

                self.results['state'] = self.create_or_update_subnet(subnet)
            elif self.state == 'absent' and changed:
                # delete subnet
                self.delete_subnet()
                # the delete does not actually return anything. if no exception, then we'll assume
                # it worked.
                self.results['state']['status'] = 'Deleted'

        return self.results

    def create_or_update_subnet(self, subnet):
        try:
            poller = self.network_client.subnets.create_or_update(self.resource_group,
                                                                  self.virtual_network_name,
                                                                  self.name,
                                                                  subnet)
            new_subnet = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating subnet {0} - {1}".format(self.name, str(exc)))
        self.check_provisioning_state(new_subnet)
        return subnet_to_dict(new_subnet)

    def delete_subnet(self):
        self.log('Deleting subnet {0}'.format(self.name))
        try:
            poller = self.network_client.subnets.delete(self.resource_group,
                                                        self.virtual_network_name,
                                                        self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting subnet {0} - {1}".format(self.name, str(exc)))

        return result

    def parse_nsg(self):
        nsg = self.security_group
        resource_group = self.resource_group
        if isinstance(self.security_group, dict):
            nsg = self.security_group.get('name')
            resource_group = self.security_group.get('resource_group', self.resource_group)
        id = format_resource_id(val=nsg,
                                subscription_id=self.subscription_id,
                                namespace='Microsoft.Network',
                                types='networkSecurityGroups',
                                resource_group=resource_group)
        name = azure_id_to_dict(id).get('name')
        return dict(id=id, name=name)


def main():
    AzureRMSubnet()


if __name__ == '__main__':
    main()
