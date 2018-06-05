#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_route
version_added: "2.7"
short_description: Manage Azure route resource.
description:
    - Create, update or delete a route.
options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the virtual network.
        required: true
    state:
        description:
            - Assert the state of the virtual network. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
    address_prefix:
        description:
            - The destination CIDR to which the route applies.
    next_hop_type:
        description:
            - The type of Azure hop the packet should be sent to.
        choices:
            - VirtualNetworkGateway
            - VnetLocal
            - Internet
            - VirtualAppliance
            - None
    next_hop_ip_address:
        description:
            - The IP address packets should be forwarded to.
            - Next hop values are only allowed in routes where the next hop type is VirtualAppliance.


extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Create a route
      azure_rm_virtualnetwork:
        name: foobar
        resource_group: Testing
        address_prefix: "10.1.0.0/16"
        next_hop_type: "VirtualNetworkGateway"

    - name: Delete a route
      azure_rm_route:
        name: foobar
        resource_group: Testing
        state: absent
'''
RETURN = '''
state:
    description: Current state of the route.
    returned: always
    type: dict
    sample: {}
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def route_to_dict(route):
    return dict(
        id=route.id,
        name=route.name,
        address_prefix=route.address_prefix,
        next_hop_type=route.next_hop_type,
        next_hop_ip_address=route.next_hop_ip_address
    )


class AzureRMRoute(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            address_prefix=dict(type='str'),
            next_hop_type=dict(type='str', choices=['VirtualNetworkGateway', 'VnetLocal', 'Internet', 'VirtualAppliance', 'None']),
            next_hop_ip_address=dict(type='str')
        )

        required_if = [
            ('state', 'present', ['next_hop_type'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.address_prefix = None
        self.next_hop_type = None
        self.next_hop_ip_address = None

        self.results = dict(
            changed=False
        )

        super(AzureRMRoute, self).__init__(self.module_arg_spec,
                                           required_if=required_if,
                                           supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        result = dict()
        changed = False

        result = self.get_route()
        if self.state == 'absent' and result:
            changed = True
            if not self.check_mode:
                self.delete_route()
        elif self.state == 'present':
            if not result:
                changed = True  # create new route
            else:  # check update
                if result.next_hop_type != self.next_hop_type:
                    self.log('Update: {0} next_hop_type from {1} to {2}'.format(self.name, result.next_hop_type, self.next_hop_type))
                    changed = True
                if result.next_hop_ip_address != self.next_hop_ip_address:
                    self.log('Update: {0} next_hop_ip_address from {1} to {2}'.format(self.name, result.next_hop_ip_address, self.next_hop_ip_address))
                    changed = True
                if result.address_prefix != self.next_hop_type:
                    self.log('Update: {0} address_prefix from {1} to {2}'.format(self.name, result.address_prefix, self.address_prefix))
                    changed = True
            if changed:
                result = self.network_models.Route(name=self.name,
                                                   address_prefix=self.address_prefix,
                                                   next_hop_type=self.next_hop_type,
                                                   next_hop_ip_address=self.next_hop_ip_address)
                if not self.check_mode:
                    result = self.create_or_update_route(result)

        self.results = route_to_dict(result)
        self.results['changed'] = changed                
        return self.results

    def create_or_update_route(self, param):
        try:
            poller = self.network_client.routes.create_or_update(self.resource_group, self.name, param)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating route {0} - {1}".format(self.name, str(exc)))

    def delete_route(self):
        try:
            poller = self.network_client.routes.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
            return result            
        except Exception as exc:
            self.fail("Error deleting virtual network {0} - {1}".format(self.name, str(exc)))

    def get_route(self):
        try:
            return self.network_client.routes.get(self.resource_group, self.name)
        except Exception as exc:
            self.log('Error getting route {0} - {1}'.format(self.name, str(exc)))
            return None

def main():
    AzureRMRoute()

if __name__ == '__main__':
    main()
