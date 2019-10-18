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
module: azure_rm_virtualnetwork
version_added: "2.1"
short_description: Manage Azure virtual networks
description:
    - Create, update or delete a virtual networks. Allows setting and updating the available IPv4 address ranges
      and setting custom DNS servers. Use the M(azure_rm_subnet) module to associate subnets with a virtual network.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    address_prefixes_cidr:
        description:
            - List of IPv4 address ranges where each is formatted using CIDR notation.
            - Required when creating a new virtual network or using I(purge_address_prefixes).
        aliases:
            - address_prefixes
    dns_servers:
        description:
            - Custom list of DNS servers. Maximum length of two.
            - The first server in the list will be treated as the Primary server. This is an explicit list.
            - Existing DNS servers will be replaced with the specified list.
            - Use the I(purge_dns_servers) option to remove all custom DNS servers and revert to default Azure servers.
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    name:
        description:
            - Name of the virtual network.
        required: true
    purge_address_prefixes:
        description:
            - Use with I(state=present) to remove any existing I(address_prefixes).
        type: bool
        default: 'no'
        aliases:
          - purge
    purge_dns_servers:
        description:
            - Use with I(state=present) to remove existing DNS servers, reverting to default Azure servers. Mutually exclusive with DNS servers.
        type: bool
        default: 'no'
    state:
        description:
            - State of the virtual network. Use C(present) to create or update and C(absent) to delete.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

'''

EXAMPLES = '''
    - name: Create a virtual network
      azure_rm_virtualnetwork:
        resource_group: myResourceGroup
        name: myVirtualNetwork
        address_prefixes_cidr:
            - "10.1.0.0/16"
            - "172.100.0.0/16"
        dns_servers:
            - "127.0.0.1"
            - "127.0.0.2"
        tags:
            testing: testing
            delete: on-exit

    - name: Delete a virtual network
      azure_rm_virtualnetwork:
        resource_group: myResourceGroup
        name: myVirtualNetwork
        state: absent
'''
RETURN = '''
state:
    description:
       - Current state of the virtual network.
    returned: always
    type: complex
    contains:
        address_prefixes:
            description:
                - The virtual network IPv4 address ranges.
            returned: always
            type: list
            sample: [
                     "10.1.0.0/16",
                     "172.100.0.0/16"
                    ]
        dns_servers:
            description:
                - DNS servers.
            returned: always
            type: list
            sample: [
                    "127.0.0.1",
                    "127.0.0.3"
                    ]
        etag:
            description:
                - A unique read-only string that changes whenever the resource is update.
            returned: always
            type: str
            sample: 'W/"0712e87c-f02f-4bb3-8b9e-2da0390a3886"'
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/
                    Microsoft.Network/virtualNetworks/myVirtualNetwork"
        location:
            description:
                - The Geo-location where the resource lives.
            returned: always
            type: str
            sample: eastus
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: my_test_network
        provisioning_state:
            description:
                - Provisioning state of the virtual network.
            returned: always
            type: str
            sample: Succeeded
        tags:
            description:
                - Resource tags, such as { 'tags1':'value1' }
            returned: always
            type: dict
            sample: { 'key1':'value1' }
        type:
            description:
                - Resource type.
            returned: always
            type: str
            sample: Microsoft.Network/virtualNetworks
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN


def virtual_network_to_dict(vnet):
    '''
    Convert a virtual network object to a dict.
    :param vnet: VirtualNet object
    :return: dict
    '''
    results = dict(
        id=vnet.id,
        name=vnet.name,
        location=vnet.location,
        type=vnet.type,
        tags=vnet.tags,
        provisioning_state=vnet.provisioning_state,
        etag=vnet.etag
    )
    if vnet.dhcp_options and len(vnet.dhcp_options.dns_servers) > 0:
        results['dns_servers'] = []
        for server in vnet.dhcp_options.dns_servers:
            results['dns_servers'].append(server)
    if vnet.address_space and len(vnet.address_space.address_prefixes) > 0:
        results['address_prefixes'] = []
        for space in vnet.address_space.address_prefixes:
            results['address_prefixes'].append(space)
    return results


class AzureRMVirtualNetwork(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            address_prefixes_cidr=dict(type='list', aliases=['address_prefixes']),
            dns_servers=dict(type='list',),
            purge_address_prefixes=dict(type='bool', default=False, aliases=['purge']),
            purge_dns_servers=dict(type='bool', default=False),
        )

        mutually_exclusive = [
            ('dns_servers', 'purge_dns_servers')
        ]

        required_if = [
            ('purge_address_prefixes', True, ['address_prefixes_cidr'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.address_prefixes_cidr = None
        self.purge_address_prefixes = None
        self.dns_servers = None
        self.purge_dns_servers = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMVirtualNetwork, self).__init__(self.module_arg_spec,
                                                    mutually_exclusive=mutually_exclusive,
                                                    required_if=required_if,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if self.state == 'present' and self.purge_address_prefixes:
            for prefix in self.address_prefixes_cidr:
                if not CIDR_PATTERN.match(prefix):
                    self.fail("Parameter error: invalid address prefix value {0}".format(prefix))

            if self.dns_servers and len(self.dns_servers) > 2:
                self.fail("Parameter error: You can provide a maximum of 2 DNS servers.")

        changed = False
        results = dict()

        try:
            self.log('Fetching vnet {0}'.format(self.name))
            vnet = self.network_client.virtual_networks.get(self.resource_group, self.name)

            results = virtual_network_to_dict(vnet)
            self.log('Vnet exists {0}'.format(self.name))
            self.log(results, pretty_print=True)
            self.check_provisioning_state(vnet, self.state)

            if self.state == 'present':
                if self.address_prefixes_cidr:
                    existing_address_prefix_set = set(vnet.address_space.address_prefixes)
                    requested_address_prefix_set = set(self.address_prefixes_cidr)
                    missing_prefixes = requested_address_prefix_set - existing_address_prefix_set
                    extra_prefixes = existing_address_prefix_set - requested_address_prefix_set
                    if len(missing_prefixes) > 0:
                        self.log('CHANGED: there are missing address_prefixes')
                        changed = True
                        if not self.purge_address_prefixes:
                            # add the missing prefixes
                            for prefix in missing_prefixes:
                                results['address_prefixes'].append(prefix)

                    if len(extra_prefixes) > 0 and self.purge_address_prefixes:
                        self.log('CHANGED: there are address_prefixes to purge')
                        changed = True
                        # replace existing address prefixes with requested set
                        results['address_prefixes'] = self.address_prefixes_cidr

                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True

                if self.dns_servers:
                    existing_dns_set = set(vnet.dhcp_options.dns_servers) if vnet.dhcp_options else set([])
                    requested_dns_set = set(self.dns_servers)
                    if existing_dns_set != requested_dns_set:
                        self.log('CHANGED: replacing DNS servers')
                        changed = True
                        results['dns_servers'] = self.dns_servers

                if self.purge_dns_servers and vnet.dhcp_options and len(vnet.dhcp_options.dns_servers) > 0:
                    self.log('CHANGED: purging existing DNS servers')
                    changed = True
                    results['dns_servers'] = []
            elif self.state == 'absent':
                self.log("CHANGED: vnet exists but requested state is 'absent'")
                changed = True
        except CloudError:
            self.log('Vnet {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: vnet {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                if not results:
                    # create a new virtual network
                    self.log("Create virtual network {0}".format(self.name))
                    if not self.address_prefixes_cidr:
                        self.fail('Parameter error: address_prefixes_cidr required when creating a virtual network')
                    vnet_param = self.network_models.VirtualNetwork(
                        location=self.location,
                        address_space=self.network_models.AddressSpace(
                            address_prefixes=self.address_prefixes_cidr
                        )
                    )
                    if self.dns_servers:
                        vnet_param.dhcp_options = self.network_models.DhcpOptions(
                            dns_servers=self.dns_servers
                        )
                    if self.tags:
                        vnet_param.tags = self.tags
                    self.results['state'] = self.create_or_update_vnet(vnet_param)
                else:
                    # update existing virtual network
                    self.log("Update virtual network {0}".format(self.name))
                    vnet_param = self.network_models.VirtualNetwork(
                        location=results['location'],
                        address_space=self.network_models.AddressSpace(
                            address_prefixes=results['address_prefixes']
                        ),
                        tags=results['tags'],
                        subnets=vnet.subnets
                    )
                    if results.get('dns_servers'):
                        vnet_param.dhcp_options = self.network_models.DhcpOptions(
                            dns_servers=results['dns_servers']
                        )
                    self.results['state'] = self.create_or_update_vnet(vnet_param)
            elif self.state == 'absent':
                self.delete_virtual_network()
                self.results['state']['status'] = 'Deleted'

        return self.results

    def create_or_update_vnet(self, vnet):
        try:
            poller = self.network_client.virtual_networks.create_or_update(self.resource_group, self.name, vnet)
            new_vnet = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating virtual network {0} - {1}".format(self.name, str(exc)))
        return virtual_network_to_dict(new_vnet)

    def delete_virtual_network(self):
        try:
            poller = self.network_client.virtual_networks.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting virtual network {0} - {1}".format(self.name, str(exc)))
        return result


def main():
    AzureRMVirtualNetwork()


if __name__ == '__main__':
    main()
