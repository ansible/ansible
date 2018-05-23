#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#                    Yuwei ZHou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_networkinterface

version_added: "2.1"

short_description: Manage Azure network interfaces.

description:
    - Create, update or delete a network interface. When creating a network interface you must provide the name of an
      existing virtual network, the name of an existing subnet within the virtual network. A default security group
      and public IP address will be created automatically, or you can provide the name of an existing security group
      and public IP address. See the examples below for more details.

options:
    resource_group:
        description:
            - Name of a resource group where the network interface exists or will be created.
        required: true
    name:
        description:
            - Name of the network interface.
        required: true
    state:
        description:
            - Assert the state of the network interface. Use 'present' to create or update an interface and
              'absent' to delete an interface.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        required: false
    virtual_network_resource_group:
        description:
        - The resource group of I(virtual_network_name).
        - If not set then this is the same resource group as I(resource_group).
        - This can be used to specify the resource group of a virtual network that is in another resource group
          than the network interface.
        - If I(virtual_network_name) is specified as a virtual network id, this parameter is ignored.
        version_added: 2.6
    virtual_network_name:
        description:
            - Name or id of an existing virtual network with which the network interface will be associated. Required
              when creating a network interface.
        aliases:
            - virtual_network
        required: true
    subnet_name:
        description:
            - Name of an existing subnet within the specified virtual network. Required when creating a network
              interface
        aliases:
            - subnet
        required: true
    os_type:
        description:
            - Determines any rules to be added to a default security group. When creating a network interface, if no
              security group name is provided, a default security group will be created. If the os_type is 'Windows',
              a rule will be added allowing RDP access. If the os_type is 'Linux', a rule allowing SSH access will be
              added.
        choices:
            - Windows
            - Linux
        default: Linux
    private_ip_address:
        description:
            - (Deprecate) Valid IPv4 address that falls within the specified subnet.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
    private_ip_allocation_method:
        description:
            - "(Deprecate) Specify whether or not the assigned IP address is permanent. NOTE: when creating a network interface
              specifying a value of 'Static' requires that a private_ip_address value be provided. You can update
              the allocation method to 'Static' after a dynamic private ip address has been assigned."
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        default: Dynamic
        choices:
            - Dynamic
            - Static
    public_ip:
        description:
            - (Deprecate) When creating a network interface, if no public IP address name is provided a default public IP
              address will be created. Set to false, if you do not want a public IP address automatically created.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        type: bool
        default: 'yes'
    public_ip_address_name:
        description:
            - (Deprecate) Name of an existing public IP address object to associate with the security group.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        aliases:
            - public_ip_address
            - public_ip_name
    public_ip_allocation_method:
        description:
            - (Deprecate) If a public_ip_address_name is not provided, a default public IP address will be created. The allocation
              method determines whether or not the public IP address assigned to the network interface is permanent.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        choices:
            - Dynamic
            - Static
        default: Dynamic
    ip_configurations:
        description:
            - List of ip configuration if contains mutilple configuration, should contain configuration object include
              field private_ip_address, private_ip_allocation_method, public_ip_address_name, public_ip, subnet_name,
              virtual_network_name, public_ip_allocation_method, name
        suboptions:
            name:
                description:
                    - Name of the ip configuration.
                required: true
            private_ip_address:
                description:
                    - Private ip address for the ip configuration.
            private_ip_allocation_method:
                description:
                    - private ip allocation method.
                choices:
                    - Dynamic
                    - Static
                default: Dynamic
            public_ip_address_name:
                description:
                    - Name of the public ip address. None for disable ip address.
            public_ip_allocation_method:
                description:
                    - public ip allocation method.
                choices:
                    - Dynamic
                    - Static
                default: Dynamic
            primary:
                description:
                    - Whether the ip configuration is the primary one in the list.
                type: bool
                default: 'no'
        version_added: 2.5
    security_group_name:
        description:
            - Name of an existing security group with which to associate the network interface. If not provided, a
              default security group will be created.
        aliases:
            - security_group
    open_ports:
        description:
            - When a default security group is created for a Linux host a rule will be added allowing inbound TCP
              connections to the default SSH port 22, and for a Windows host rules will be added allowing inbound
              access to RDP ports 3389 and 5986. Override the default ports by providing a list of open ports.
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"
    - "Yuwei Zhou (@yuwzho)"
'''

EXAMPLES = '''
    - name: Create a network interface with minimal parameters
      azure_rm_networkinterface:
        name: nic001
        resource_group: Testing
        virtual_network_name: vnet001
        subnet_name: subnet001
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network interface with private IP address only (no Public IP)
      azure_rm_networkinterface:
        name: nic001
        resource_group: Testing
        virtual_network_name: vnet001
        subnet_name: subnet001
        ip_configurations:
          - name: ipconfig1
            primary: True

    - name: Create a network interface for use in a Windows host (opens RDP port) with custom RDP port
      azure_rm_networkinterface:
        name: nic002
        resource_group: Testing
        virtual_network_name: vnet001
        subnet_name: subnet001
        os_type: Windows
        rdp_port: 3399
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network interface using existing security group and public IP
      azure_rm_networkinterface:
        name: nic003
        resource_group: Testing
        virtual_network_name: vnet001
        subnet_name: subnet001
        security_group_name: secgroup001
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network with mutilple ip configurations
      azure_rm_networkinterface:
        name: nic004
        resource_group: Testing
        subnet_name: subnet001
        virtual_network_name: vnet001
        security_group_name: secgroup001
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True
          - name: ipconfig2

    - name: Delete network interface
      azure_rm_networkinterface:
        resource_group: Testing
        name: nic003
        state: absent
'''

RETURN = '''
state:
    description: The current state of the network interface.
    returned: always
    type: dict
    sample: {
        "dns_settings": {
            "applied_dns_servers": [],
            "dns_servers": [],
            "internal_dns_name_label": null,
            "internal_fqdn": null
        },
        "enable_ip_forwarding": false,
        "etag": 'W/"be115a43-2148-4545-a324-f33ad444c926"',
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/nic003",
        "ip_configurations": [{
            "name": "default",
            "private_ip_address": "10.1.0.10",
            "private_ip_allocation_method": "Static",
            "public_ip_address": {
                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/publicip001",
                "name": "publicip001"
            },
            "subnet": {},
            "load_balancer_backend_address_pools": []
        }],
        "location": "eastus2",
        "mac_address": null,
        "name": "nic003",
        "network_security_group": {},
        "primary": null,
        "provisioning_state": "Succeeded",
        "tags": null,
        "type": "Microsoft.Network/networkInterfaces"
    }
'''

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict
from ansible.module_utils._text import to_native


def subnet_to_dict(subnet):
    dic = azure_id_to_dict(subnet.id)
    return dict(
        id=subnet.id,
        virtual_network_name=dic.get('virtualNetworks'),
        resource_group=dic.get('resourceGroups'),
        name=dic.get('subnets')
    )


def nic_to_dict(nic):
    ip_configurations = [
        dict(
            name=config.name,
            private_ip_address=config.private_ip_address,
            private_ip_allocation_method=config.private_ip_allocation_method,
            subnet=subnet_to_dict(config.subnet),
            primary=config.primary,
            public_ip_address=dict(
                id=config.public_ip_address.id,
                name=azure_id_to_dict(config.public_ip_address.id).get('publicIPAddresses'),
                public_ip_allocation_method=config.public_ip_address.public_ip_allocation_method
            ) if config.public_ip_address else None
        ) for config in nic.ip_configurations
    ]
    return dict(
        id=nic.id,
        name=nic.name,
        type=nic.type,
        location=nic.location,
        tags=nic.tags,
        network_security_group=dict(
            id=nic.network_security_group.id,
            name=azure_id_to_dict(nic.network_security_group.id).get('networkSecurityGroups')
        ) if nic.network_security_group else None,
        dns_settings=dict(
            dns_servers=nic.dns_settings.dns_servers,
            applied_dns_servers=nic.dns_settings.applied_dns_servers,
            internal_dns_name_label=nic.dns_settings.internal_dns_name_label,
            internal_fqdn=nic.dns_settings.internal_fqdn
        ),
        ip_configurations=ip_configurations,
        ip_configuration=ip_configurations[0] if len(ip_configurations) == 1 else None,  # for compatiable issue, keep this field
        mac_address=nic.mac_address,
        enable_ip_forwarding=nic.enable_ip_forwarding,
        provisioning_state=nic.provisioning_state,
        etag=nic.etag,
    )


ip_configuration_spec = dict(
    name=dict(type='str', required=True),
    private_ip_address=dict(type='str'),
    private_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
    public_ip_address_name=dict(type='str', aliases=['public_ip_address', 'public_ip_name']),
    public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
    primary=dict(type='bool', default=False)
)


class AzureRMNetworkInterface(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            location=dict(type='str'),
            security_group_name=dict(type='str', aliases=['security_group']),
            state=dict(default='present', choices=['present', 'absent']),
            private_ip_address=dict(type='str'),
            private_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
            public_ip_address_name=dict(type='str', aliases=['public_ip_address', 'public_ip_name']),
            public_ip=dict(type='bool', default=True),
            subnet_name=dict(type='str', aliases=['subnet']),
            virtual_network_resource_group=dict(type='str'),
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
            ip_configurations=dict(type='list', default=None, elements='dict', options=ip_configuration_spec),
            os_type=dict(type='str', choices=['Windows', 'Linux'], default='Linux'),
            open_ports=dict(type='list'),
        )

        required_if = [
            ('state', 'present', ['subnet_name', 'virtual_network_name'])
        ]

        self.resource_group = None
        self.name = None
        self.location = None
        self.security_group_name = None
        self.private_ip_address = None
        self.private_ip_allocation_method = None
        self.public_ip_address_name = None
        self.public_ip = None
        self.subnet_name = None
        self.virtual_network_resource_group = None
        self.virtual_network_name = None
        self.public_ip_allocation_method = None
        self.state = None
        self.tags = None
        self.security_group_name = None
        self.os_type = None
        self.open_ports = None
        self.ip_configurations = None

        self.results = dict(
            changed=False,
            state=dict(),
        )

        super(AzureRMNetworkInterface, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True,
                                                      required_if=required_if)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = None
        changed = False
        nic = None
        nsg = None

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        # parse the virtual network resource group and name
        virtual_network_dict = parse_resource_id(self.virtual_network_name)
        virtual_network_name = virtual_network_dict.get('name')
        virtual_network_resource_group = virtual_network_dict.get('resource_group', self.virtual_network_resource_group)

        if virtual_network_resource_group is None:
            virtual_network_resource_group = self.resource_group

        # if not set the security group name, use nic name for default
        self.security_group_name = self.security_group_name or self.name

        if self.state == 'present' and not self.ip_configurations:
            # construct the ip_configurations array for compatiable
            self.deprecate('Setting ip_configuration flatten is deprecated and will be removed.'
                           ' Using ip_configurations list to define the ip configuration', version='2.9')
            self.ip_configurations = [
                dict(
                    private_ip_address=self.private_ip_address,
                    private_ip_allocation_method=self.private_ip_allocation_method,
                    public_ip_address_name=self.public_ip_address_name if self.public_ip else None,
                    public_ip_allocation_method=self.public_ip_allocation_method,
                    name='default',
                    primary=True
                )
            ]

        try:
            self.log('Fetching network interface {0}'.format(self.name))
            nic = self.network_client.network_interfaces.get(self.resource_group, self.name)

            self.log('Network interface {0} exists'.format(self.name))
            self.check_provisioning_state(nic, self.state)
            results = nic_to_dict(nic)
            self.log(results, pretty_print=True)

            nsg = None
            if self.state == 'present':
                # check for update
                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True

                nsg = self.get_security_group(self.security_group_name)
                if nsg and results.get('network_security_group') and results['network_security_group'].get('id') != nsg.id:
                    self.log("CHANGED: network interface {0} network security group".format(self.name))
                    changed = True

                if results['ip_configurations'][0]['subnet']['virtual_network_name'] != virtual_network_name:
                    self.log("CHANGED: network interface {0} virtual network name".format(self.name))
                    changed = True

                if results['ip_configurations'][0]['subnet']['resource_group'] != virtual_network_resource_group:
                    self.log("CHANGED: network interface {0} virtual network resource group".format(self.name))
                    changed = True

                if results['ip_configurations'][0]['subnet']['name'] != self.subnet_name:
                    self.log("CHANGED: network interface {0} subnet name".format(self.name))
                    changed = True

                # check the ip_configuration is changed
                # construct two set with the same structure and then compare
                # the list should contains:
                # name, private_ip_address, public_ip_address_name, private_ip_allocation_method, subnet_name
                ip_configuration_result = self.construct_ip_configuration_set(results['ip_configurations'])
                ip_configuration_request = self.construct_ip_configuration_set(self.ip_configurations)
                if ip_configuration_result != ip_configuration_request:
                    self.log("CHANGED: network interface {0} ip configurations".format(self.name))
                    changed = True

            elif self.state == 'absent':
                self.log("CHANGED: network interface {0} exists but requested state is 'absent'".format(self.name))
                changed = True
        except CloudError:
            self.log('Network interface {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: network interface {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                subnet = self.network_models.SubResource(
                    '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}/subnets/{3}'.format(
                        self.subscription_id,
                        virtual_network_resource_group,
                        virtual_network_name,
                        self.subnet_name))

                nic_ip_configurations = [
                    self.network_models.NetworkInterfaceIPConfiguration(
                        private_ip_allocation_method=ip_config.get('private_ip_allocation_method'),
                        private_ip_address=ip_config.get('private_ip_address'),
                        name=ip_config.get('name'),
                        subnet=subnet,
                        public_ip_address=self.get_or_create_public_ip_address(ip_config),
                        primary=ip_config.get('primary')
                    ) for ip_config in self.ip_configurations
                ]

                nsg = self.create_default_securitygroup(self.resource_group,
                                                        self.location,
                                                        self.security_group_name,
                                                        self.os_type,
                                                        self.open_ports)
                self.log('Creating or updating network interface {0}'.format(self.name))
                nic = self.network_models.NetworkInterface(
                    id=results['id'] if results else None,
                    location=self.location,
                    tags=self.tags,
                    ip_configurations=nic_ip_configurations,
                    network_security_group=nsg
                )
                self.results['state'] = self.create_or_update_nic(nic)
            elif self.state == 'absent':
                self.log('Deleting network interface {0}'.format(self.name))
                self.delete_nic()
                # Delete doesn't return anything. If we get this far, assume success
                self.results['state']['status'] = 'Deleted'

        return self.results

    def get_or_create_public_ip_address(self, ip_config):
        name = ip_config.get('public_ip_address_name')

        if not (self.public_ip and name):
            return None

        pip = self.get_public_ip_address(name)
        if not pip:
            params = self.network_models.PublicIPAddress(
                location=self.location,
                public_ip_allocation_method=ip_config.get('public_ip_allocation_method'),
            )
            try:
                poller = self.network_client.public_ip_addresses.create_or_update(self.resource_group, name, params)
                pip = self.get_poller_result(poller)
            except CloudError as exc:
                self.fail("Error creating {0} - {1}".format(name, str(exc)))
        return pip

    def create_or_update_nic(self, nic):
        try:
            poller = self.network_client.network_interfaces.create_or_update(self.resource_group, self.name, nic)
            new_nic = self.get_poller_result(poller)
            return nic_to_dict(new_nic)
        except Exception as exc:
            self.fail("Error creating or updating network interface {0} - {1}".format(self.name, str(exc)))

    def delete_nic(self):
        try:
            poller = self.network_client.network_interfaces.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting network interface {0} - {1}".format(self.name, str(exc)))
        return True

    def get_public_ip_address(self, name):
        self.log("Fetching public ip address {0}".format(name))
        try:
            return self.network_client.public_ip_addresses.get(self.resource_group, name)
        except Exception as exc:
            return None

    def get_security_group(self, name):
        self.log("Fetching security group {0}".format(name))
        try:
            return self.network_client.network_security_groups.get(self.resource_group, name)
        except Exception as exc:
            return None

    def construct_ip_configuration_set(self, raw):
        configurations = [str(dict(
            private_ip_allocation_method=to_native(item.get('private_ip_allocation_method')),
            public_ip_address_name=(to_native(item.get('public_ip_address').get('name'))
                                    if item.get('public_ip_address') else to_native(item.get('public_ip_address_name'))),
            primary=item.get('primary'),
            name=to_native(item.get('name'))
        )) for item in raw]
        return set(configurations)


def main():
    AzureRMNetworkInterface()


if __name__ == '__main__':
    main()
