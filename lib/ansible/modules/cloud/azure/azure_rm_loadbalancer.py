#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_loadbalancer

version_added: "2.4"

short_description: Manage Azure load balancers.

description:
    -

options:
    resource_group:
        description:
            - Name of a resource group where the load balancer exists or will be created.
        required: true
    name:
        description:
            - Name of the load balancer.
        required: true
    state:
        description:
            - Assert the state of the load balancer. Use 'present' to create or update a load balancer and
              'absent' to delete a load balancer.
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
        required: false
        default: null
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Thomas Stringer (@tr_stringer)"
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import random

from ansible.module_utils.basic import *
from ansible.module_utils.azure_rm_common import *

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import LoadBalancer, FrontendIPConfiguration, BackendAddressPool
except ImportError:
    # This is handled in azure_rm_common
    pass

class AzureRMLoadBalancer(AzureRMModuleBase):
    """Configuration class for an Azure RM load balancer resource"""

    def __init__(self):
        self.module_args = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(type='str', required=False),
            public_ip_address_name=dict(
                type='str',
                required=False,
                aliases=['public_ip_address', 'public_ip_name', 'public_ip']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.public_ip_address_name = None
        self.state = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMLoadBalancer, self).__init__(
            derived_arg_spec=self.module_args,
            supports_check_mode=True
        )

    def exec_module(self, **kwargs):
        """Main module execution method"""
        for key in self.module_args.keys():
            setattr(self, key, kwargs[key])

        results = dict()
        changed = False
        pip = None
        load_balancer_props = dict()

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))

        if not self.location:
            self.location = resource_group.location
        load_balancer_props['location'] = self.location

        if self.state == 'present':
            # handle present status
            if self.public_ip_address_name:
                pip = self.get_public_ip_address(self.public_ip_address_name)
                load_balancer_props['frontend_ip_configurations'] = [
                    FrontendIPConfiguration(
                        name=random_name('feipconfig'),
                        public_ip_address=pip
                    )
                ]
        elif self.state == 'absent':
            try:
                self.network_client.load_balancers.delete(
                    resource_group_name=self.resource_group,
                    load_balancer_name=self.name
                ).wait()
                changed = True
            except CloudError:
                changed = False

            self.results['changed'] = changed
            return self.results

        try:
            # before we do anything, we need to attempt to retrieve the load balancer
            # knowing whether or not it exists will tell us what to do in the future
            self.log('Fetching load balancer {}'.format(self.name))
            load_balancer = self.network_client.load_balancers.get(self.resource_group, self.name)

            self.log('Load balancer {} exists'.format(self.name))
            self.check_provisioning_state(load_balancer, self.state)
            results = load_balancer_to_dict(load_balancer)
            self.log(results, pretty_print=True)

            if self.state == 'present':
                update_tags, results['tags'] = self.update_tags(results['tags'])

                if update_tags:
                    changed = True
        except CloudError:
            self.log('Load balancer {} does not exist'.format(self.name))
            if self.state == 'present':
                self.log(
                    'CHANGED: load balancer {} does not exist but requested status \'present\''
                    .format(self.name)
                )
                changed = True

        load_balancer_props['backend_address_pools'] = [BackendAddressPool(name=random_name('beap'))]

        self.results['changed'] = changed
        self.results['state'] = (
            results if results
            else load_balancer_to_dict(LoadBalancer(**load_balancer_props))
        )

        if self.check_mode:
            return self.results

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
            idle_time_in_minutes=_.idle_time_in_minutes,
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
            enable_floating_point_ip=_.enable_floating_point_ip,
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

def random_name(prefix):
    return '{}{}'.format(prefix, random.randint(10000, 99999))

def main():
    AzureRMLoadBalancer()

if __name__ == '__main__':
    main()
