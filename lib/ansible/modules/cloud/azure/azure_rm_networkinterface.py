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
        default: resource_group location
        required: false
    virtual_network_name:
        description:
            - Name of an existing virtual network with which the network interface will be associated. Required
              when creating a network interface.
        aliases:
            - virtual_network
        required: true
        default: null
    subnet_name:
        description:
            - Name of an existing subnet within the specified virtual network. Required when creating a network
              interface
        aliases:
            - subnet
        required: true
        default: null
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
        required: false
    private_ip_address:
        description:
            - Valid IPv4 address that falls within the specified subnet.
        required: false
    private_ip_allocation_method:
        description:
            - "Specify whether or not the assigned IP address is permanent. NOTE: when creating a network interface
              specifying a value of 'Static' requires that a private_ip_address value be provided. You can update
              the allocation method to 'Static' after a dynamic private ip address has been assigned."
        default: Dynamic
        choices:
            - Dynamic
            - Static
        required: false
    public_ip:
        description:
            - When creating a network interface, if no public IP address name is provided a default public IP
              address will be created. Set to false, if you do not want a public IP address automatically created.
        default: true
        required: false
    public_ip_address_name:
        description:
            - Name of an existing public IP address object to associate with the security group.
        aliases:
            - public_ip_address
            - public_ip_name
        required: false
        default: null
    public_ip_allocation_method:
        description:
            - If a public_ip_address_name is not provided, a default public IP address will be created. The allocation
              method determines whether or not the public IP address assigned to the network interface is permanent.
        choices:
            - Dynamic
            - Static
        default: Dynamic
        required: false
    security_group_name:
        description:
            - Name of an existing security group with which to associate the network interface. If not provided, a
              default security group will be created.
        aliases:
            - security_group
        required: false
        default: null
    open_ports:
        description:
            - When a default security group is created for a Linux host a rule will be added allowing inbound TCP
              connections to the default SSH port 22, and for a Windows host rules will be added allowing inbound
              access to RDP ports 3389 and 5986. Override the default ports by providing a list of open ports.
        required: false
        default: null
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"
'''

EXAMPLES = '''
    - name: Create a network interface with minimal parameters
      azure_rm_networkinterface:
            name: nic001
            resource_group: Testing
            virtual_network_name: vnet001
            subnet_name: subnet001

    - name: Create a network interface with private IP address only (no Public IP)
      azure_rm_networkinterface:
            name: nic001
            resource_group: Testing
            virtual_network_name: vnet001
            subnet_name: subnet001
            public_ip: no

    - name: Create a network interface for use in a Windows host (opens RDP port) with custom RDP port
      azure_rm_networkinterface:
            name: nic002
            resource_group: Testing
            virtual_network_name: vnet001
            subnet_name: subnet001
            os_type: Windows
            rdp_port: 3399

    - name: Create a network interface using existing security group and public IP
      azure_rm_networkinterface:
            name: nic003
            resource_group: Testing
            virtual_network_name: vnet001
            subnet_name: subnet001
            security_group_name: secgroup001
            public_ip_address_name: publicip001

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
        "ip_configuration": {
            "name": "default",
            "private_ip_address": "10.1.0.10",
            "private_ip_allocation_method": "Static",
            "public_ip_address": {
                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/publicip001",
                "name": "publicip001"
            },
            "subnet": {}
        },
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
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, Subnet, \
        PublicIPAddress, NetworkSecurityGroup
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict


def nic_to_dict(nic):
    result = dict(
        id=nic.id,
        name=nic.name,
        type=nic.type,
        location=nic.location,
        tags=nic.tags,
        network_security_group=dict(),
        ip_configuration=dict(
            name=nic.ip_configurations[0].name,
            private_ip_address=nic.ip_configurations[0].private_ip_address,
            private_ip_allocation_method=nic.ip_configurations[0].private_ip_allocation_method,
            subnet=dict(),
            public_ip_address=dict(),
        ),
        dns_settings=dict(
            dns_servers=nic.dns_settings.dns_servers,
            applied_dns_servers=nic.dns_settings.applied_dns_servers,
            internal_dns_name_label=nic.dns_settings.internal_dns_name_label,
            internal_fqdn=nic.dns_settings.internal_fqdn
        ),
        mac_address=nic.mac_address,
        primary=nic.primary,
        enable_ip_forwarding=nic.enable_ip_forwarding,
        provisioning_state=nic.provisioning_state,
        etag=nic.etag,
    )

    if nic.network_security_group:
        result['network_security_group']['id'] = nic.network_security_group.id
        id_keys = azure_id_to_dict(nic.network_security_group.id)
        result['network_security_group']['name'] = id_keys['networkSecurityGroups']

    if nic.ip_configurations[0].subnet:
        result['ip_configuration']['subnet']['id'] = \
            nic.ip_configurations[0].subnet.id
        id_keys = azure_id_to_dict(nic.ip_configurations[0].subnet.id)
        result['ip_configuration']['subnet']['virtual_network_name'] = id_keys['virtualNetworks']
        result['ip_configuration']['subnet']['name'] = id_keys['subnets']

    if nic.ip_configurations[0].public_ip_address:
        result['ip_configuration']['public_ip_address']['id'] = \
            nic.ip_configurations[0].public_ip_address.id
        id_keys = azure_id_to_dict(nic.ip_configurations[0].public_ip_address.id)
        result['ip_configuration']['public_ip_address']['name'] = id_keys['publicIPAddresses']

    return result


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
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            os_type=dict(type='str', choices=['Windows', 'Linux'], default='Linux'),
            open_ports=dict(type='list'),
            public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.security_group_name = None
        self.private_ip_address = None
        self.private_ip_allocation_method = None
        self.public_ip_address_name = None
        self.state = None
        self.subnet_name = None
        self.tags = None
        self.virtual_network_name = None
        self.security_group_name = None
        self.os_type = None
        self.open_ports = None
        self.public_ip_allocation_method = None
        self.public_ip = None

        self.results = dict(
            changed=False,
            state=dict(),
        )

        super(AzureRMNetworkInterface, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = dict()
        changed = False
        nic = None
        subnet = None
        nsg = None
        pip = None

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if self.state == 'present':
            if self.virtual_network_name and not self.subnet_name:
                self.fail("Parameter error: a subnet is required when passing a virtual_network_name.")

            if self.subnet_name and not self.virtual_network_name:
                self.fail("Parameter error: virtual_network_name is required when passing a subnet value.")

            if self.virtual_network_name and self.subnet_name:
                subnet = self.get_subnet(self.virtual_network_name, self.subnet_name)

            if self.public_ip_address_name:
                pip = self.get_public_ip_address(self.public_ip_address_name)

            if self.security_group_name:
                nsg = self.get_security_group(self.security_group_name)

        try:
            self.log('Fetching network interface {0}'.format(self.name))
            nic = self.network_client.network_interfaces.get(self.resource_group, self.name)

            self.log('Network interface {0} exists'.format(self.name))
            self.check_provisioning_state(nic, self.state)
            results = nic_to_dict(nic)
            self.log(results, pretty_print=True)

            if self.state == 'present':

                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True

                if self.private_ip_address:
                    if results['ip_configuration']['private_ip_address'] != self.private_ip_address:
                        self.log("CHANGED: network interface {0} private ip".format(self.name))
                        changed = True
                        results['ip_configuration']['private_ip_address'] = self.private_ip_address

                if self.public_ip_address_name:
                    if results['ip_configuration']['public_ip_address'].get('id') != pip.id:
                        self.log("CHANGED: network interface {0} public ip".format(self.name))
                        changed = True
                        results['ip_configuration']['public_ip_address']['id'] = pip.id
                        results['ip_configuration']['public_ip_address']['name'] = pip.name

                if self.security_group_name:
                    if results['network_security_group'].get('id') != nsg.id:
                        self.log("CHANGED: network interface {0} network security group".format(self.name))
                        changed = True
                        results['network_security_group']['id'] = nsg.id
                        results['network_security_group']['name'] = nsg.name

                if self.private_ip_allocation_method:
                    if results['ip_configuration']['private_ip_allocation_method'] != self.private_ip_allocation_method:
                        self.log("CHANGED: network interface {0} private ip allocation".format(self.name))
                        changed = True
                        results['ip_configuration']['private_ip_allocation_method'] = self.private_ip_allocation_method
                        if self.private_ip_allocation_method == 'Dynamic':
                            results['ip_configuration']['private_ip_address'] = None

                if self.subnet_name:
                    if results['ip_configuration']['subnet'].get('id') != subnet.id:
                        changed = True
                        self.log("CHANGED: network interface {0} subnet".format(self.name))
                        results['ip_configuration']['subnet']['id'] = subnet.id
                        results['ip_configuration']['subnet']['name'] = subnet.name
                        results['ip_configuration']['subnet']['virtual_network_name'] = self.virtual_network_name

            elif self.state == 'absent':
                self.log("CHANGED: network interface {0} exists but requested state is 'absent'".format(self.name))
                changed = True
        except CloudError:
            self.log('Network interface {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: network interface {0} does not exist but requested state is "
                         "'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                if not nic:
                    # create network interface
                    self.log("Creating network interface {0}.".format(self.name))

                    # check required parameters
                    if not self.subnet_name:
                        self.fail("parameter error: subnet_name required when creating a network interface.")
                    if not self.virtual_network_name:
                        self.fail("parameter error: virtual_network_name required when creating a network interface.")

                    if not self.security_group_name:
                        # create default security group
                        nsg = self.create_default_securitygroup(self.resource_group, self.location, self.name,
                                                                self.os_type, self.open_ports)

                    if not pip and self.public_ip:
                        # create a default public_ip
                        pip = self.create_default_pip(self.resource_group, self.location, self.name,
                                                      self.public_ip_allocation_method)

                    nic = NetworkInterface(
                        location=self.location,
                        tags=self.tags,
                        ip_configurations=[
                            NetworkInterfaceIPConfiguration(
                                private_ip_allocation_method=self.private_ip_allocation_method,
                            )
                        ]
                    )
                    # nic.name = self.name
                    nic.ip_configurations[0].subnet = Subnet(id=subnet.id)
                    nic.ip_configurations[0].name = 'default'
                    nic.network_security_group = NetworkSecurityGroup(id=nsg.id,
                                                                      location=nsg.location,
                                                                      resource_guid=nsg.resource_guid)
                    if self.private_ip_address:
                        nic.ip_configurations[0].private_ip_address = self.private_ip_address

                    if pip:
                        nic.ip_configurations[0].public_ip_address = PublicIPAddress(
                            id=pip.id,
                            location=pip.location,
                            resource_guid=pip.resource_guid)
                else:
                    self.log("Updating network interface {0}.".format(self.name))
                    nic = NetworkInterface(
                        id=results['id'],
                        location=results['location'],
                        tags=results['tags'],
                        ip_configurations=[
                            NetworkInterfaceIPConfiguration(
                                private_ip_allocation_method=results['ip_configuration']['private_ip_allocation_method']
                            )
                        ]
                    )
                    subnet = self.get_subnet(results['ip_configuration']['subnet']['virtual_network_name'],
                                             results['ip_configuration']['subnet']['name'])
                    nic.ip_configurations[0].subnet = Subnet(id=subnet.id)
                    nic.ip_configurations[0].name = results['ip_configuration']['name']
                    # nic.name = name=results['name'],

                    if results['ip_configuration'].get('private_ip_address'):
                        nic.ip_configurations[0].private_ip_address = results['ip_configuration']['private_ip_address']

                    if results['ip_configuration']['public_ip_address'].get('id'):
                        pip = \
                            self.get_public_ip_address(results['ip_configuration']['public_ip_address']['name'])
                        nic.ip_configurations[0].public_ip_address = PublicIPAddress(
                            id=pip.id,
                            location=pip.location,
                            resource_guid=pip.resource_guid)
                    # name=pip.name,

                    if results['network_security_group'].get('id'):
                        nsg = self.get_security_group(results['network_security_group']['name'])
                        nic.network_security_group = NetworkSecurityGroup(id=nsg.id,
                                                                          location=nsg.location,
                                                                          resource_guid=nsg.resource_guid)

                # See what actually gets sent to the API
                request = self.serialize_obj(nic, 'NetworkInterface')
                self.log(request, pretty_print=True)

                self.results['state'] = self.create_or_update_nic(nic)

            elif self.state == 'absent':
                self.log('Deleting network interface {0}'.format(self.name))
                self.delete_nic()

        return self.results

    def create_or_update_nic(self, nic):
        try:
            poller = self.network_client.network_interfaces.create_or_update(self.resource_group, self.name, nic)
            new_nic = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating network interface {0} - {1}".format(self.name, str(exc)))

        return nic_to_dict(new_nic)

    def delete_nic(self):
        try:
            poller = self.network_client.network_interfaces.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting network interface {0} - {1}".format(self.name, str(exc)))
        # Delete doesn't return anything. If we get this far, assume success
        self.results['state']['status'] = 'Deleted'
        return True

    def get_public_ip_address(self, name):
        self.log("Fetching public ip address {0}".format(name))
        try:
            public_ip = self.network_client.public_ip_addresses.get(self.resource_group, name)
        except Exception as exc:
            self.fail("Error: fetching public ip address {0} - {1}".format(self.name, str(exc)))
        return public_ip

    def get_subnet(self, vnet_name, subnet_name):
        self.log("Fetching subnet {0} in virtual network {1}".format(subnet_name, vnet_name))
        try:
            subnet = self.network_client.subnets.get(self.resource_group, vnet_name, subnet_name)
        except Exception as exc:
            self.fail("Error: fetching subnet {0} in virtual network {1} - {2}".format(subnet_name,
                                                                                       vnet_name,
                                                                                       str(exc)))
        return subnet

    def get_security_group(self, name):
        self.log("Fetching security group {0}".format(name))
        try:
            nsg = self.network_client.network_security_groups.get(self.resource_group, name)
        except Exception as exc:
            self.fail("Error: fetching network security group {0} - {1}.".format(name, str(exc)))
        return nsg


def main():
    AzureRMNetworkInterface()


if __name__ == '__main__':
    main()
