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
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_networkinterface

version_added: '2.1'

short_description: Manage Azure network interfaces

description:
    - Create, update or delete a network interface.
    - When creating a network interface you must provide the name of an existing virtual network, the name of an existing subnet within the virtual network.
    - A default security group and public IP address will be created automatically.
    - Or you can provide the name of an existing security group and public IP address.
    - See the examples below for more details.

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
            - Assert the state of the network interface. Use C(present) to create or update an interface and
              C(absent) to delete an interface.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    virtual_network:
        description:
            - An existing virtual network with which the network interface will be associated. Required when creating a network interface.
            - It can be the virtual network's name.
            - Make sure your virtual network is in the same resource group as NIC when you give only the name.
            - It can be the virtual network's resource id.
            - It can be a dict which contains I(name) and I(resource_group) of the virtual network.
        aliases:
            - virtual_network_name
        required: true
    subnet_name:
        description:
            - Name of an existing subnet within the specified virtual network. Required when creating a network interface.
            - Use the C(virtual_network)'s resource group.
        aliases:
            - subnet
        required: true
    os_type:
        description:
            - Determines any rules to be added to a default security group.
            - When creating a network interface, if no security group name is provided, a default security group will be created.
            - If the I(os_type=Windows), a rule allowing RDP access will be added.
            - If the I(os_type=Linux), a rule allowing SSH access will be added.
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
            - (Deprecate) Whether or not the assigned IP address is permanent.
            - When creating a network interface, if you specify I(private_ip_address=Static), you must provide a value for I(private_ip_address).
            - You can update the allocation method to C(Static) after a dynamic private IP address has been assigned.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        default: Dynamic
        choices:
            - Dynamic
            - Static
    public_ip:
        description:
            - (Deprecate) When creating a network interface, if no public IP address name is provided a default public IP address will be created.
            - Set to C(false) if you do not want a public IP address automatically created.
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
            - (Deprecate) If a I(public_ip_address_name) is not provided, a default public IP address will be created.
            - The allocation method determines whether or not the public IP address assigned to the network interface is permanent.
            - This option will be deprecated in 2.9, use I(ip_configurations) instead.
        choices:
            - Dynamic
            - Static
        default: Dynamic
    ip_configurations:
        description:
            - List of IP configurations. Each configuration object should include
              field I(private_ip_address), I(private_ip_allocation_method), I(public_ip_address_name), I(public_ip), I(public_ip_allocation_method), I(name).
        suboptions:
            name:
                description:
                    - Name of the IP configuration.
                required: true
            private_ip_address:
                description:
                    - Private IP address for the IP configuration.
            private_ip_allocation_method:
                description:
                    - Private IP allocation method.
                choices:
                    - Dynamic
                    - Static
                default: Dynamic
            public_ip_address_name:
                description:
                    - Name of the public IP address. None for disable IP address.
                aliases:
                    - public_ip_address
                    - public_ip_name
            public_ip_allocation_method:
                description:
                    - Public IP allocation method.
                choices:
                    - Dynamic
                    - Static
                default: Dynamic
            load_balancer_backend_address_pools:
                description:
                    - List of existing load-balancer backend address pools to associate with the network interface.
                    - Can be written as a resource ID.
                    - Also can be a dict of I(name) and I(load_balancer).
                version_added: '2.6'
            primary:
                description:
                    - Whether the IP configuration is the primary one in the list.
                type: bool
                default: 'no'
            application_security_groups:
                description:
                    - List of application security groups in which the IP configuration is included.
                    - Element of the list could be a resource id of application security group, or dict of I(resource_group) and I(name).
                version_added: '2.8'
        version_added: '2.5'
    enable_accelerated_networking:
        description:
            - Whether the network interface should be created with the accelerated networking feature or not.
        type: bool
        version_added: '2.7'
        default: False
    create_with_security_group:
        description:
            - Whether a security group should be be created with the NIC.
            - If this flag set to C(True) and no I(security_group) set, a default security group will be created.
        type: bool
        version_added: '2.6'
        default: True
    security_group:
        description:
            - An existing security group with which to associate the network interface.
            - If not provided, a default security group will be created when I(create_with_security_group=true).
            - It can be the name of security group.
            - Make sure the security group is in the same resource group when you only give its name.
            - It can be the resource id.
            - It can be a dict contains security_group's I(name) and I(resource_group).
        aliases:
            - security_group_name
    open_ports:
        description:
            - When a default security group is created for a Linux host a rule will be added allowing inbound TCP
              connections to the default SSH port C(22), and for a Windows host rules will be added allowing inbound
              access to RDP ports C(3389) and C(5986). Override the default ports by providing a list of open ports.
    enable_ip_forwarding:
        description:
            - Whether to enable IP forwarding.
        aliases:
            - ip_forwarding
        type: bool
        default: False
        version_added: '2.7'
    dns_servers:
        description:
            - Which DNS servers should the NIC lookup.
            - List of IP addresses.
        type: list
        version_added: '2.7'
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)
    - Yuwei Zhou (@yuwzho)
'''

EXAMPLES = '''
    - name: Create a network interface with minimal parameters
      azure_rm_networkinterface:
        name: nic001
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network interface with private IP address only (no Public IP)
      azure_rm_networkinterface:
        name: nic001
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        create_with_security_group: False
        ip_configurations:
          - name: ipconfig1
            primary: True

    - name: Create a network interface for use in a Windows host (opens RDP port) with custom RDP port
      azure_rm_networkinterface:
        name: nic002
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        os_type: Windows
        rdp_port: 3399
        security_group: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurit
                         yGroups/nsg001"
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network interface using existing security group and public IP
      azure_rm_networkinterface:
        name: nic003
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        security_group: secgroup001
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network with multiple ip configurations
      azure_rm_networkinterface:
        name: nic004
        resource_group: myResourceGroup
        subnet_name: subnet001
        virtual_network: vnet001
        security_group:
          name: testnic002
          resource_group: Testing1
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True
          - name: ipconfig2
            load_balancer_backend_address_pools:
              - "{{ loadbalancer001.state.backend_address_pools[0].id }}"
              - name: backendaddrpool1
                load_balancer: loadbalancer001

    - name: Create a network interface in accelerated networking mode
      azure_rm_networkinterface:
        name: nic005
        resource_group: myResourceGroup
        virtual_network_name: vnet001
        subnet_name: subnet001
        enable_accelerated_networking: True

    - name: Create a network interface with IP forwarding
      azure_rm_networkinterface:
        name: nic001
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        ip_forwarding: True
        ip_configurations:
          - name: ipconfig1
            public_ip_address_name: publicip001
            primary: True

    - name: Create a network interface with dns servers
      azure_rm_networkinterface:
        name: nic009
        resource_group: myResourceGroup
        virtual_network: vnet001
        subnet_name: subnet001
        dns_servers:
          - 8.8.8.8

    - name: Delete network interface
      azure_rm_networkinterface:
        resource_group: myResourceGroup
        name: nic003
        state: absent
'''

RETURN = '''
state:
    description:
        - The current state of the network interface.
    returned: always
    type: complex
    contains:
        dns_server:
            description:
                - Which DNS servers should the NIC lookup.
                - List of IP addresses.
            type: list
            sample: ['8.9.10.11', '7.8.9.10']
        dns_setting:
            description:
                - The DNS settings in network interface.
            type: dict
            sample: {
                "applied_dns_servers": [],
                "dns_servers": [
                    "8.9.10.11",
                    "7.8.9.10"
                ],
                "internal_dns_name_label": null,
                "internal_fqdn": null
                }
        enable_ip_forwarding:
            description:
                Whether to enable IP forwarding.
            type: bool
            sample: true
        etag:
            description:
                - A unique read-only string that changes whenever the resource is updated.
            type: str
            sample: 'W/"be115a43-2148-4545-a324-f33ad444c926"'
        id:
            description:
                - Id of the network interface.
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkInterfaces/nic003"
        enable_accelerated_networking:
            description:
                 - Whether the network interface should be created with the accelerated networking feature or not.
            type: bool
            sample: true
        ip_configurations:
            description:
                - List of IP configurations.
            type: complex
            contains:
                name:
                    description:
                        - Name of the IP configuration.
                    type: str
                    sample: default
                load_balancer_backend_address_pools:
                    description:
                        - List of existing load-balancer backend address pools to associate with the network interface.
                    type: list
                private_ip_address:
                    description:
                        - Private IP address for the IP configuration.
                    type: str
                    sample: "10.1.0.10"
                private_ip_allocation_method:
                    description:
                        - Private IP allocation method.
                    type: str
                    sample: "Static"
                public_ip_address:
                    description:
                        - Name of the public IP address. None for disable IP address.
                    type: dict
                    sample: {
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/publicIPAddresse
                        s/publicip001",
                        "name": "publicip001"
                        }
                subnet:
                    description:
                        - The reference of the subnet resource.
                    type: dict
                    sample: {
                        "id": "/subscriptions/xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/
                         myresourcegroup/providers/Microsoft.Network/virtualNetworks/tnb57dc95318/subnets/tnb57dc95318",
                        "name": "tnb57dc95318",
                        "resource_group": "myresourcegroup",
                        "virtual_network_name": "tnb57dc95318"
                        }
        location:
            description:
                - The network interface resource location.
            type: str
            sample: eastus
        mac_address:
            description:
                - The MAC address of the network interface.
            type: str
        name:
            description:
                - Name of the network interface.
            type: str
            sample: nic003
        network_security_group:
            description:
                - The reference of the network security group resource.
            type: dict
            sample: {
                "id": "/subscriptions//xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/
                myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/nsg001",
                "name": "nsg001"
                }
        primary:
            description:
                - Get whether this is a primary network interface on virtual machine.
            type: bool
            sample: true
        provisioning_state:
            description:
                - The provisioning state of the public IP resource.
            type: str
            sample: Succeeded
        tags:
            description:
                -Tags of the network interface.
            type: dict
            sample: { 'key': 'value' }
        type:
            description:
                - Type of the resource.
            type: str
            sample: "Microsoft.Network/networkInterfaces"
'''

try:
    from msrestazure.tools import parse_resource_id, resource_id, is_valid_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict, normalize_location_name, format_resource_id
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
            load_balancer_backend_address_pools=([item.id for item in config.load_balancer_backend_address_pools]
                                                 if config.load_balancer_backend_address_pools else None),
            public_ip_address=dict(
                id=config.public_ip_address.id,
                name=azure_id_to_dict(config.public_ip_address.id).get('publicIPAddresses'),
                public_ip_allocation_method=config.public_ip_address.public_ip_allocation_method
            ) if config.public_ip_address else None,
            application_security_groups=([asg.id for asg in config.application_security_groups]
                                         if config.application_security_groups else None)
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
        ip_configuration=ip_configurations[0] if len(ip_configurations) == 1 else None,  # for compatible issue, keep this field
        mac_address=nic.mac_address,
        enable_ip_forwarding=nic.enable_ip_forwarding,
        provisioning_state=nic.provisioning_state,
        etag=nic.etag,
        enable_accelerated_networking=nic.enable_accelerated_networking,
        dns_servers=nic.dns_settings.dns_servers,
    )


ip_configuration_spec = dict(
    name=dict(type='str', required=True),
    private_ip_address=dict(type='str'),
    private_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
    public_ip_address_name=dict(type='str', aliases=['public_ip_address', 'public_ip_name']),
    public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
    load_balancer_backend_address_pools=dict(type='list'),
    primary=dict(type='bool', default=False),
    application_security_groups=dict(type='list', elements='raw')
)


class AzureRMNetworkInterface(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            location=dict(type='str'),
            enable_accelerated_networking=dict(type='bool', default=False),
            create_with_security_group=dict(type='bool', default=True),
            security_group=dict(type='raw', aliases=['security_group_name']),
            state=dict(default='present', choices=['present', 'absent']),
            private_ip_address=dict(type='str'),
            private_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
            public_ip_address_name=dict(type='str', aliases=['public_ip_address', 'public_ip_name']),
            public_ip=dict(type='bool', default=True),
            subnet_name=dict(type='str', aliases=['subnet']),
            virtual_network=dict(type='raw', aliases=['virtual_network_name']),
            public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
            ip_configurations=dict(type='list', default=None, elements='dict', options=ip_configuration_spec),
            os_type=dict(type='str', choices=['Windows', 'Linux'], default='Linux'),
            open_ports=dict(type='list'),
            enable_ip_forwarding=dict(type='bool', aliases=['ip_forwarding'], default=False),
            dns_servers=dict(type='list'),
        )

        required_if = [
            ('state', 'present', ['subnet_name', 'virtual_network'])
        ]

        self.resource_group = None
        self.name = None
        self.location = None
        self.create_with_security_group = None
        self.enable_accelerated_networking = None
        self.security_group = None
        self.private_ip_address = None
        self.private_ip_allocation_method = None
        self.public_ip_address_name = None
        self.public_ip = None
        self.subnet_name = None
        self.virtual_network = None
        self.public_ip_allocation_method = None
        self.state = None
        self.tags = None
        self.os_type = None
        self.open_ports = None
        self.enable_ip_forwarding = None
        self.ip_configurations = None
        self.dns_servers = None

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
        self.location = normalize_location_name(self.location)

        # parse the virtual network resource group and name
        self.virtual_network = self.parse_resource_to_dict(self.virtual_network)

        # if not set the security group name, use nic name for default
        self.security_group = self.parse_resource_to_dict(self.security_group or self.name)

        # if application security groups set, convert to resource id format
        if self.ip_configurations:
            for config in self.ip_configurations:
                if config.get('application_security_groups'):
                    asgs = []
                    for asg in config['application_security_groups']:
                        asg_resource_id = asg
                        if isinstance(asg, str) and (not is_valid_resource_id(asg)):
                            asg = self.parse_resource_to_dict(asg)
                        if isinstance(asg, dict):
                            asg_resource_id = format_resource_id(val=asg['name'],
                                                                 subscription_id=self.subscription_id,
                                                                 namespace='Microsoft.Network',
                                                                 types='applicationSecurityGroups',
                                                                 resource_group=asg['resource_group'])
                        asgs.append(asg_resource_id)
                    if len(asgs) > 0:
                        config['application_security_groups'] = asgs

        if self.state == 'present' and not self.ip_configurations:
            # construct the ip_configurations array for compatible
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

                if self.create_with_security_group != bool(results.get('network_security_group')):
                    self.log("CHANGED: add or remove network interface {0} network security group".format(self.name))
                    changed = True

                if self.enable_accelerated_networking != bool(results.get('enable_accelerated_networking')):
                    self.log("CHANGED: Accelerated Networking set to {0} (previously {1})".format(
                        self.enable_accelerated_networking,
                        results.get('enable_accelerated_networking')))
                    changed = True

                if self.enable_ip_forwarding != bool(results.get('enable_ip_forwarding')):
                    self.log("CHANGED: IP forwarding set to {0} (previously {1})".format(
                        self.enable_ip_forwarding,
                        results.get('enable_ip_forwarding')))
                    changed = True

                # We need to ensure that dns_servers are list like
                dns_servers_res = results.get('dns_settings').get('dns_servers')
                _dns_servers_set = sorted(self.dns_servers) if isinstance(self.dns_servers, list) else list()
                _dns_servers_res = sorted(dns_servers_res) if isinstance(self.dns_servers, list) else list()
                if _dns_servers_set != _dns_servers_res:
                    self.log("CHANGED: DNS servers set to {0} (previously {1})".format(
                        ", ".join(_dns_servers_set),
                        ", ".join(_dns_servers_res)))
                    changed = True

                if not changed:
                    nsg = self.get_security_group(self.security_group['resource_group'], self.security_group['name'])
                    if nsg and results.get('network_security_group') and results['network_security_group'].get('id') != nsg.id:
                        self.log("CHANGED: network interface {0} network security group".format(self.name))
                        changed = True

                if results['ip_configurations'][0]['subnet']['virtual_network_name'] != self.virtual_network['name']:
                    self.log("CHANGED: network interface {0} virtual network name".format(self.name))
                    changed = True

                if results['ip_configurations'][0]['subnet']['resource_group'] != self.virtual_network['resource_group']:
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
                    id='/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}/subnets/{3}'.format(
                        self.virtual_network['subscription_id'],
                        self.virtual_network['resource_group'],
                        self.virtual_network['name'],
                        self.subnet_name))

                nic_ip_configurations = [
                    self.network_models.NetworkInterfaceIPConfiguration(
                        private_ip_allocation_method=ip_config.get('private_ip_allocation_method'),
                        private_ip_address=ip_config.get('private_ip_address'),
                        name=ip_config.get('name'),
                        subnet=subnet,
                        public_ip_address=self.get_or_create_public_ip_address(ip_config),
                        load_balancer_backend_address_pools=([self.network_models.BackendAddressPool(id=self.backend_addr_pool_id(bap_id))
                                                              for bap_id in ip_config.get('load_balancer_backend_address_pools')]
                                                             if ip_config.get('load_balancer_backend_address_pools') else None),
                        primary=ip_config.get('primary'),
                        application_security_groups=([self.network_models.ApplicationSecurityGroup(id=asg_id)
                                                      for asg_id in ip_config.get('application_security_groups')]
                                                     if ip_config.get('application_security_groups') else None)
                    ) for ip_config in self.ip_configurations
                ]

                nsg = self.create_default_securitygroup(self.security_group['resource_group'],
                                                        self.location,
                                                        self.security_group['name'],
                                                        self.os_type,
                                                        self.open_ports) if self.create_with_security_group else None

                self.log('Creating or updating network interface {0}'.format(self.name))
                nic = self.network_models.NetworkInterface(
                    id=results['id'] if results else None,
                    location=self.location,
                    tags=self.tags,
                    ip_configurations=nic_ip_configurations,
                    enable_accelerated_networking=self.enable_accelerated_networking,
                    enable_ip_forwarding=self.enable_ip_forwarding,
                    network_security_group=nsg
                )
                if self.dns_servers:
                    dns_settings = self.network_models.NetworkInterfaceDnsSettings(
                        dns_servers=self.dns_servers)
                    nic.dns_settings = dns_settings
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

    def get_security_group(self, resource_group, name):
        self.log("Fetching security group {0}".format(name))
        try:
            return self.network_client.network_security_groups.get(resource_group, name)
        except Exception as exc:
            return None

    def backend_addr_pool_id(self, val):
        if isinstance(val, dict):
            lb = val.get('load_balancer', None)
            name = val.get('name', None)
            if lb and name:
                return resource_id(subscription=self.subscription_id,
                                   resource_group=self.resource_group,
                                   namespace='Microsoft.Network',
                                   type='loadBalancers',
                                   name=lb,
                                   child_type_1='backendAddressPools',
                                   child_name_1=name)
        return val

    def construct_ip_configuration_set(self, raw):
        configurations = [str(dict(
            private_ip_allocation_method=to_native(item.get('private_ip_allocation_method')),
            public_ip_address_name=(to_native(item.get('public_ip_address').get('name'))
                                    if item.get('public_ip_address') else to_native(item.get('public_ip_address_name'))),
            primary=item.get('primary'),
            load_balancer_backend_address_pools=(set([to_native(self.backend_addr_pool_id(id))
                                                      for id in item.get('load_balancer_backend_address_pools')])
                                                 if item.get('load_balancer_backend_address_pools') else None),
            application_security_groups=(set([to_native(asg_id) for asg_id in item.get('application_security_groups')])
                                         if item.get('application_security_groups') else None),
            name=to_native(item.get('name'))
        )) for item in raw]
        return set(configurations)


def main():
    AzureRMNetworkInterface()


if __name__ == '__main__':
    main()
