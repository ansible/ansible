#!/usr/bin/python
#
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_loadbalancer

version_added: "2.5"

short_description: Manage Azure load balancers.

description:
    - Create, update and delete Azure load balancers with single frontend, backend, rule or inbound nat rule.
      For complicated use case, please use azure_rm_deployment.

options:
    resource_group:
        description:
            - Name of a resource group where the load balancer exists or will be created.
        required: true
    subnet_resource_group:
        description:
            - Name of a resource group where the subnet exists.
        required: false
        default: resource_group
    name:
        description:
            - Name of the load balancer.
        required: true
    state:
        description:
            - Assert the state of the load balancer. Use 'present' to create or update a load balancer and 'absent' to delete a load balancer.
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
    public_ip_address_name:
        description:
            - Name of an existing public IP address object to associate with the security group.
        aliases:
            - public_ip_address
            - public_ip_name
            - public_ip
        required: false
    probe_port:
        description:
            - The port that the health probe will use.
        required: false
    probe_protocol:
        description:
            - The protocol to use for the health probe.
        required: false
        choices:
            - Tcp
            - Http
    probe_interval:
        description:
            - How much time (in seconds) to probe the endpoint for health.
        default: 15
        required: false
    probe_fail_count:
        description:
            - The amount of probe failures for the load balancer to make a health determination.
        default: 3
        required: false
    probe_request_path:
        description:
            - The URL that an HTTP probe will use (only relevant if probe_protocol is set to Http).
        required: false
    protocol:
        description:
            - The protocol (TCP or UDP) that the load balancer will use.
        required: false
        choices:
            - Tcp
            - Udp
    load_distribution:
        description:
            - The type of load distribution that the load balancer will employ.
        required: false
        default: Default
        choices:
            - Default
            - SourceIP
            - SourceIPProtocol
    frontend_port:
        description:
            - Frontend port that will be exposed for the load balancer.
        required: false
    backend_port:
        description:
            - Backend port that will be exposed for the load balancer.
        required: false
    idle_timeout:
        description:
            - Timeout for TCP idle connection in minutes.
        default: 4
        required: false
    natpool_frontend_port_start:
        description:
            - Start of the port range for a NAT pool. Deprecated soon!
        required: false
    natpool_frontend_port_end:
        description:
            - End of the port range for a NAT pool. Deprecated soon!
        required: false
    natpool_backend_port:
        description:
            - Backend port used by the NAT pool. Deprecated soon!
        required: false
    natpool_protocol:
        description:
            - The protocol for the NAT pool. Deprecated soon!
        required: false
    subnet_name:
        description:
            - Name of an existing subnet within the specified virtual network. Required when virtual_network_name is given.
        aliases:
            - subnet
        required: false
        default: null
    virtual_network_name:
        description:
            - Name of an existing virtual network. Required when subnet_name is given.
        aliases:
            - virtual_network
            - vnet
        required: false
        default: null
    backend_address_pool_name:
        description:
            - Name of the backend address pool.
        required: false
        default: LoadBalancerBackEnd
    frontend_ip_config_name:
        description:
            - Name of the frontend ip configuration.
        required: false
        default: LoadBalancerFrontEnd
    probe_name:
        description:
            - Name of the health probe
        required: false
        default: LoadBalancerProbe
    load_balancing_rule_name:
        description:
            - Name of the load balancing rule.
        required: false
        default: LoadBalancerRule
    private_ip_allocation_method:
        description:
            - The allocation method when using private IP as frontend
        required: false
        default: Dynamic
        choices:
            - Dynamic
            - Static
    inbound_nat_pool_name:
        description:
            - Name of the inbound nat pool name. Deprecated soon!
        required: false
        default: LoadBalancerInboundNatPool
    nat_name:
        description:
            - Name of the inbound nat rule.
        required: false
        default: LoadBalancerInboundNatRule
    nat_protocol:
        description:
            - The protocol (TCP or UDP) that the inbount nat rule will use.
        required: false
        choices:
            - Tcp
            - Udp
    nat_frontend_port:
        description:
            - Frontend port that will be exposed for the inbound nat rule. Required when nat_protocol is given.
        required: false
    nat_backend_port:
        description:
            - Backend port that will be exposed for the inbound nat rule. Default to nat_frontend_port.
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Xiaoming Zheng (@siaomingjeng)"
    - "Thomas Stringer (@tstringer)"
'''

EXAMPLES = '''
    - name: Create a load balancer configuring the frontend using internal private IP from a subnet of a different resource group.
      azure_rm_loadbalancer:
        name: myloadbalancer
        location: australiasoutheast
        resource_group: rg-aus-demo-test
        subnet_resource_group: rg-aus-demo-net
        virtual_network_name: vn-aus-demo-net
        subnet_name: sn-aus-demo-lb
        probe_protocol: Tcp
        probe_port: 80
        probe_interval: 10
        probe_fail_count: 3
        protocol: Tcp
        load_distribution: Default
        frontend_port: 80
        backend_port: 8080
        idle_timeout: 4
        private_ip_address: 10.10.10.10
        private_ip_allocation_method: Static

    - name: Create a load balancer with public frontend and inbound nat rule.
      azure_rm_loadbalancer:
        name: myloadbalancer
        resource_group: rg-aus-demo-test
        public_ip: mypublicip
        nat_frontend_port: 80
        nat_pool_protocol: Tcp
'''

RETURN = '''
state:
    description: Current state of the load balancer
    returned: always
    type: dict
changed:
    description: Whether or not the resource has changed
    returned: always
    type: bool
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import (
        LoadBalancer,
        FrontendIPConfiguration,
        BackendAddressPool,
        Probe,
        LoadBalancingRule,
        SubResource,
        InboundNatPool,
        InboundNatRule,
        Subnet
    )
except ImportError:
    # This is handled in azure_rm_common
    pass


class DiffErr(Exception):
    """Used to stop value compare when finding one"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AzureRMLoadBalancer(AzureRMModuleBase):
    """Configuration class for an Azure RM load balancer resource"""

    def __init__(self):
        self.module_args = dict(
            resource_group=dict(type='str', required=True),
            subnet_resource_group=dict(type='str'),
            name=dict(type='str', required=True),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            location=dict(type='str', required=False),
            public_ip_address_name=dict(type='str', required=False, aliases=['public_ip_address', 'public_ip_name', 'public_ip']),
            private_ip_address=dict(type='str', required=False, aliases=['private_ip']),  # #
            probe_port=dict(type='int', required=False),
            probe_protocol=dict(type='str', required=False, choices=['Tcp', 'Http']),
            probe_interval=dict(type='int', default=15),
            probe_fail_count=dict(type='int', default=3),
            probe_request_path=dict(type='str', required=False),
            protocol=dict(type='str', required=False, choices=['Tcp', 'Udp']),
            load_distribution=dict(type='str', required=False, default='Default', choices=['Default', 'SourceIP', 'SourceIPProtocol']),
            frontend_port=dict(type='int', required=False),
            backend_port=dict(type='int', required=False),
            idle_timeout=dict(type='int', default=4),
            natpool_frontend_port_start=dict(type='int'),
            natpool_frontend_port_end=dict(type='int'),
            natpool_backend_port=dict(type='int'),
            natpool_protocol=dict(type='str'),
            subnet_name=dict(type='str', aliases=['subnet']),
            virtual_network_name=dict(type='str', aliases=['virtual_network', 'vnet']),
            backend_address_pool_name=dict(type='str', default='LoadBalancerBackEnd'),
            frontend_ip_config_name=dict(type='str', default='LoadBalancerFrontEnd'),
            probe_name=dict(type='str', default='LoadBalancerProbe'),
            load_balancing_rule_name=dict(type='str', default='LoadBalancerRule'),
            inbound_nat_pool_name=dict(tyep='str', default='LoadBalancerInboundNatPool'),
            private_ip_allocation_method=dict(type='str', default='Dynamic', choices=['Static', 'Dynamic']),
            nat_name=dict(type='str', default='LoadBalancerInboundNatRule'),
            nat_frontend_port=dict(type='int'),
            nat_backend_port=dict(type='int'),
            nat_protocol=dict(type='str', choices=['Tcp', 'Udp']),
        )

        self.resource_group = None
        self.subnet_resource_group = None
        self.name = None
        self.location = None
        self.public_ip_address_name = None
        self.private_ip_address = None
        self.state = None
        self.probe_port = None
        self.probe_protocol = None
        self.probe_interval = None
        self.probe_fail_count = None
        self.probe_request_path = None
        self.protocol = None
        self.load_distribution = None
        self.frontend_port = None
        self.backend_port = None
        self.idle_timeout = None
        self.natpool_frontend_port_start = None
        self.natpool_frontend_port_end = None
        self.natpool_backend_port = None
        self.natpool_protocol = None
        self.subnet_name = None
        self.virtual_network_name = None
        self.backend_address_pool_name = None
        self.frontend_ip_config_name = None
        self.probe_name = None
        self.load_balancing_rule_name = None
        self.inbound_nat_pool_name = None
        self.private_ip_allocation_method = None
        self.nat_name = None
        self.nat_frontend_port = None
        self.nat_backend_port = None
        self.nat_protocol = None
        self.tags = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMLoadBalancer, self).__init__(
            derived_arg_spec=self.module_args,
            supports_check_mode=True
        )

    def exec_module(self, **kwargs):
        """Main module execution method"""
        for key in self.module_args.keys():
            setattr(self, key, kwargs[key])

        if self.state == 'absent':
            try:
                self.network_client.load_balancers.delete(resource_group_name=self.resource_group, load_balancer_name=self.name).wait()
                changed = True
            except CloudError:
                changed = False
            self.results['changed'] = changed
            return self.results

        # From now on, suppose state==present
        if bool(self.subnet_name) != bool(self.virtual_network_name):
            self.fail('subnet_name and virtual_network_name must come together. The current values are {0} and {1}'.format(
                      self.subnet_name, self.virtual_network_name))
        if not self.subnet_resource_group:
            self.subnet_resource_group = self.resource_group
        if self.protocol:
            if not self.frontend_port:
                self.fail('frontend_port is {0} but some of the following are missing: frontend_port, backend_port'.format(self.protocol))
            if not self.backend_port:
                self.backend_port = self.frontend_port
        if self.nat_protocol:
            if not self.nat_frontend_port:
                self.fail("nat_protocol is {0} but some of the following are missing: nat_frontend_port, nat_backend_port".format(self.nat_protocol))
            if not self.nat_backend_port:
                self.nat_backend_port = self.nat_frontend_port
        if not self.public_ip_address_name and (not self.subnet_name or not self.virtual_network_name):
            self.fail('subnet_name and virtual_network_name must be given when using priviate ip frontend!')
        if not self.public_ip_address_name and not self.private_ip_address and self.private_ip_allocation_method == 'Static':
            self.fail('private_ip_allocation_method must be Dynamic when neither public_ip_address_name nor private_ip_address is given!')

        results = dict()
        changed = False
        pip = None
        subnet = None
        load_balancer_props = dict()

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location
        load_balancer_props['location'] = self.location
        if self.subnet_name and self.virtual_network_name:
            subnet = get_subnet(self, self.subnet_resource_group, self.virtual_network_name, self.subnet_name)

        # handle present status
        try:
            # before we do anything, we need to attempt to retrieve the load balancer and compare with current parameters
            self.log('Fetching load balancer {}'.format(self.name))
            load_balancer = self.network_client.load_balancers.get(self.resource_group, self.name)
            self.log('Load balancer {} exists'.format(self.name))
            self.check_provisioning_state(load_balancer, self.state)
            results = load_balancer_to_dict(load_balancer)
            self.log(results, pretty_print=True)
            update_tags, load_balancer_props['tags'] = self.update_tags(results['tags'])
            if update_tags:
                changed = True
            # check difference with current status
            # check frontend ip configurations: subnet_id, name, public_ip_address, private_ip_address, private_ip_allocation_method.
            if not results['frontend_ip_configurations']:  # a frontend must be there
                raise DiffErr('load balancer {0} frontend'.format(self.name))
            if self.subnet_name and subnet.id != results['frontend_ip_configurations'][0]['subnet']['id']:
                raise DiffErr('load balancer {0} subnet id'.format(self.name))
            if self.frontend_ip_config_name and self.frontend_ip_config_name != results['frontend_ip_configurations'][0]['name']:
                raise DiffErr('load balancer {0} probe request frontend_ip_config_name'.format(self.name))
            if self.public_ip_address_name and self.public_ip_address_name != results['frontend_ip_configurations'][0]['public_ip_address']:
                raise DiffErr('load balancer {0} public ip'.format(self.name))
            if self.private_ip_address and self.private_ip_address != results['frontend_ip_configurations'][0]['private_ip_address']:
                raise DiffErr('load balancer {0} private ip'.format(self.name))
            if self.private_ip_allocation_method and self.private_ip_allocation_method != \
                    results['frontend_ip_configurations'][0]['private_ip_allocation_method']:
                raise DiffErr('load balancer {0} probe request private_ip_allocation_method'.format(self.name))
            # check probe configurations: port, protocol, interval, number of probes, request_path, name
            if self.probe_protocol and not results['probes']:
                raise DiffErr('load balancer {0} probe'.format(self.name))
            if self.probe_port and self.probe_port != results['probes'][0]['port']:
                raise DiffErr('load balancer {0} probe_port'.format(self.name))
            if self.probe_protocol and self.probe_protocol != results['probes'][0]['protocol']:
                raise DiffErr('load balancer {0} probe_protocol'.format(self.name))
            if self.probe_interval and self.probe_interval != results['probes'][0]['interval_in_seconds']:
                raise DiffErr('load balancer {0} probe_interval'.format(self.name))
            if self.probe_fail_count and self.probe_fail_count != results['probes'][0]['number_of_probes']:
                raise DiffErr('load balancer {0} probe_fail_count'.format(self.name))
            if self.probe_protocol == 'Http' and self.probe_request_path and self.probe_request_path != results['probes'][0]['request_path']:
                raise DiffErr('load balancer {0} probe_request_path'.format(self.name))
            if self.probe_name and self.probe_name != results['probes'][0]['name']:
                raise DiffErr('load balancer {0} probe request probe_name'.format(self.name))
            # check load balancing rule configurations: protocol, distribution, frontend port, backend port, idle, name
            if self.protocol:
                if not results['load_balancing_rules']:
                    raise DiffErr('load balancer {0} load balancing rule'.format(self.name))
                if self.protocol != results['load_balancing_rules'][0]['protocol']:
                    raise DiffErr('load balancer {0} probe request protocol'.format(self.name))
                if self.load_distribution != results['load_balancing_rules'][0]['load_distribution']:
                    raise DiffErr('load balancer {0} probe request load_distribution'.format(self.name))
                if self.frontend_port and self.frontend_port != results['load_balancing_rules'][0]['frontend_port']:
                    raise DiffErr('load balancer {0} probe request frontend_port'.format(self.name))
                if self.backend_port != results['load_balancing_rules'][0]['backend_port']:
                    raise DiffErr('load balancer {0} probe request backend_port'.format(self.name))
                if self.idle_timeout != results['load_balancing_rules'][0]['idle_timeout_in_minutes']:
                    raise DiffErr('load balancer {0} probe request idel_timeout'.format(self.name))
                if self.load_balancing_rule_name != results['load_balancing_rules'][0]['name']:
                    raise DiffErr('load balancer {0} probe request load_balancing_rule_name'.format(self.name))
            # check backend address pool configuration: name only, which will be used by NIC module
            if self.backend_address_pool_name and not results['backend_address_pools']:
                raise DiffErr('load balancer {0} backend address pool'.format(self.name))
            if self.backend_address_pool_name and self.backend_address_pool_name != results['backend_address_pools'][0]['name']:
                raise DiffErr('load balancer {0} probe request backend_address_pool_name'.format(self.name))
            # check inbound nat rule:
            if self.nat_protocol:
                if not results['inbound_nat_rules']:
                    raise DiffErr('load balancer {0} inbound nat rule'.format(self.name))
                if self.nat_protocol != results['inbound_nat_rules'][0]['protocol']:
                    raise DiffErr('load balancer {0} inbound nat_protocol'.format(self.name))
                if self.nat_name != results['inbound_nat_rules'][0]['name']:
                    raise DiffErr('load balancer {0} inbound nat_name'.format(self.name))
                if self.nat_frontend_port != results['inbound_nat_rules'][0]['frontend_port']:
                    raise DiffErr('load balancer {0} inbound nat_frontend_port'.format(self.name))
                if self.nat_backend_port != results['inbound_nat_rules'][0]['backend_port']:
                    raise DiffErr('load balancer {0} inbound nat_backend_port'.format(self.name))
        except (IndexError, KeyError, DiffErr) as e:
            self.log('CHANGED: {0}'.format(e))
            changed = True
        except CloudError:
            self.log('CHANGED: load balancer {} does not exist but requested status \'present\''.format(self.name))
            changed = True

        if not changed or self.check_mode:
            self.results['changed'] = changed
            self.results['state'] = results
            return self.results

        # From now changed==True
        frontend_ip_config_id = frontend_ip_configuration_id(
            subscription_id=self.subscription_id,
            resource_group_name=self.resource_group,
            load_balancer_name=self.name,
            name=self.frontend_ip_config_name
        )
        if self.public_ip_address_name:
            pip = self.get_public_ip_address(self.public_ip_address_name)
            load_balancer_props['frontend_ip_configurations'] = [
                FrontendIPConfiguration(
                    name=self.frontend_ip_config_name,
                    public_ip_address=pip
                )
            ]
        elif self.private_ip_address or self.private_ip_allocation_method == 'Dynamic':
            load_balancer_props['frontend_ip_configurations'] = [
                FrontendIPConfiguration(
                    name=self.frontend_ip_config_name,
                    private_ip_address=self.private_ip_address,
                    private_ip_allocation_method=self.private_ip_allocation_method,
                    subnet=get_subnet(self, self.subnet_resource_group, self.virtual_network_name, self.subnet_name)
                )
            ]
        backend_addr_pool_id = backend_address_pool_id(
            subscription_id=self.subscription_id,
            resource_group_name=self.resource_group,
            load_balancer_name=self.name,
            name=self.backend_address_pool_name
        )
        load_balancer_props['backend_address_pools'] = [BackendAddressPool(name=self.backend_address_pool_name)]

        prb_id = probe_id(
            subscription_id=self.subscription_id,
            resource_group_name=self.resource_group,
            load_balancer_name=self.name,
            name=self.probe_name
        )

        if self.probe_protocol:
            load_balancer_props['probes'] = [
                Probe(
                    name=self.probe_name,
                    protocol=self.probe_protocol,
                    port=self.probe_port,
                    interval_in_seconds=self.probe_interval,
                    number_of_probes=self.probe_fail_count,
                    request_path=self.probe_request_path
                )
            ]

        if self.protocol:
            load_balancer_props['load_balancing_rules'] = [
                LoadBalancingRule(
                    name=self.load_balancing_rule_name,
                    frontend_ip_configuration=SubResource(id=frontend_ip_config_id),
                    backend_address_pool=SubResource(id=backend_addr_pool_id),
                    probe=SubResource(id=prb_id),
                    protocol=self.protocol,
                    load_distribution=self.load_distribution,
                    frontend_port=self.frontend_port,
                    backend_port=self.backend_port,
                    idle_timeout_in_minutes=self.idle_timeout,
                    enable_floating_ip=False
                )
            ]

        if self.nat_protocol:
            load_balancer_props['inbound_nat_rules'] = [
                InboundNatRule(
                    name=self.nat_name,
                    frontend_ip_configuration=SubResource(id=frontend_ip_config_id),
                    frontend_port=self.nat_frontend_port,
                    backend_port=self.nat_backend_port,
                    protocol=self.nat_protocol,
                    enable_floating_ip=False
                )
            ]

        if frontend_ip_config_id and self.natpool_protocol:
            load_balancer_props['inbound_nat_pools'] = [
                InboundNatPool(
                    name=self.inbound_nat_pool_name,
                    frontend_ip_configuration=Subnet(id=frontend_ip_config_id),
                    protocol=self.natpool_protocol,
                    frontend_port_range_start=self.natpool_frontend_port_start,
                    frontend_port_range_end=self.natpool_frontend_port_end,
                    backend_port=self.natpool_backend_port
                )
            ]

        self.results['changed'] = changed
        self.results['state'] = load_balancer_to_dict(LoadBalancer(**load_balancer_props))

        try:
            self.network_client.load_balancers.create_or_update(
                resource_group_name=self.resource_group,
                load_balancer_name=self.name,
                parameters=LoadBalancer(**load_balancer_props)
            ).wait()
        except CloudError as err:
            self.fail('Error creating load balancer {}'.format(err))

        return self.results

    def get_public_ip_address(self, name):
        """Get a reference to the public ip address resource"""

        self.log('Fetching public ip address {}'.format(name))
        try:
            public_ip = self.network_client.public_ip_addresses.get(self.resource_group, name)
        except CloudError as err:
            self.fail('Error fetching public ip address {} - {}'.format(name, str(err)))
        return public_ip


def load_balancer_to_dict(load_balancer):
    """Seralialize a LoadBalancer object to a dict"""

    result = dict(
        id=load_balancer.id,
        name=load_balancer.name,
        location=load_balancer.location,
        tags=load_balancer.tags,
        provisioning_state=load_balancer.provisioning_state,
        etag=load_balancer.etag,
        frontend_ip_configurations=[],
        backend_address_pools=[],
        load_balancing_rules=[],
        probes=[],
        inbound_nat_rules=[],
        inbound_nat_pools=[],
        outbound_nat_rules=[]
    )

    if load_balancer.frontend_ip_configurations:
        result['frontend_ip_configurations'] = [dict(
            id=_.id,
            name=_.name,
            etag=_.etag,
            provisioning_state=_.provisioning_state,
            private_ip_address=_.private_ip_address,
            private_ip_allocation_method=_.private_ip_allocation_method,
            subnet=dict(
                id=_.subnet.id,
                name=_.subnet.name,
                address_prefix=_.subnet.address_prefix
            ) if _.subnet else None,
            public_ip_address=dict(
                id=_.public_ip_address.id,
                location=_.public_ip_address.location,
                public_ip_allocation_method=_.public_ip_address.public_ip_allocation_method,
                ip_address=_.public_ip_address.ip_address
            ) if _.public_ip_address else None
        ) for _ in load_balancer.frontend_ip_configurations]

    if load_balancer.backend_address_pools:
        result['backend_address_pools'] = [dict(
            id=_.id,
            name=_.name,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.backend_address_pools]

    if load_balancer.load_balancing_rules:
        result['load_balancing_rules'] = [dict(
            id=_.id,
            name=_.name,
            protocol=_.protocol,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            backend_address_pool_id=_.backend_address_pool.id,
            probe_id=_.probe.id,
            load_distribution=_.load_distribution,
            frontend_port=_.frontend_port,
            backend_port=_.backend_port,
            idle_timeout_in_minutes=_.idle_timeout_in_minutes,
            enable_floating_ip=_.enable_floating_ip,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.load_balancing_rules]

    if load_balancer.probes:
        result['probes'] = [dict(
            id=_.id,
            name=_.name,
            protocol=_.protocol,
            port=_.port,
            interval_in_seconds=_.interval_in_seconds,
            number_of_probes=_.number_of_probes,
            request_path=_.request_path,
            provisioning_state=_.provisioning_state
        ) for _ in load_balancer.probes]

    if load_balancer.inbound_nat_rules:
        result['inbound_nat_rules'] = [dict(
            id=_.id,
            name=_.name,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            protocol=_.protocol,
            frontend_port=_.frontend_port,
            backend_port=_.backend_port,
            idle_timeout_in_minutes=_.idle_timeout_in_minutes,
            enable_floating_point_ip=_.enable_floating_point_ip if hasattr(_, 'enable_floating_point_ip') else None,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.inbound_nat_rules]

    if load_balancer.inbound_nat_pools:
        result['inbound_nat_pools'] = [dict(
            id=_.id,
            name=_.name,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            protocol=_.protocol,
            frontend_port_range_start=_.frontend_port_range_start,
            frontend_port_range_end=_.frontend_port_range_end,
            backend_port=_.backend_port,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.inbound_nat_pools]

    if load_balancer.outbound_nat_rules:
        result['outbound_nat_rules'] = [dict(
            id=_.id,
            name=_.name,
            allocated_outbound_ports=_.allocated_outbound_ports,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            backend_address_pool=_.backend_address_pool.id,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.outbound_nat_rules]

    return result


def frontend_ip_configuration_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a frontend ip configuration"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def backend_address_pool_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a backend address pool"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/backendAddressPools/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def probe_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a probe"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/probes/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def get_subnet(self, resource_group, vnet_name, subnet_name):
    self.log("Fetching subnet {0} in virtual network {1}".format(subnet_name, vnet_name))
    try:
        subnet = self.network_client.subnets.get(resource_group, vnet_name, subnet_name)
    except Exception as exc:
        self.fail("Error: fetching subnet {0} in virtual network {1} - {2}".format(subnet_name, vnet_name, str(exc)))
    return subnet


def main():
    """Main execution"""
    AzureRMLoadBalancer()

if __name__ == '__main__':
    main()
