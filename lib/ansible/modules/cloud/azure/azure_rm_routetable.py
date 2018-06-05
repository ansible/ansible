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
    route_table:
        description:
            - The name of the route table.
        required: true


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

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, normalize_location_name


route_spec=dict(
    name=dict(type='str', required=True),
    address_prefix=dict(type='str'),
    next_hop_type=dict(type='str', choices=['VirtualNetworkGateway', 'VnetLocal', 'Internet', 'VirtualAppliance', 'None'], required=True),
    next_hop_ip_address=dict(type='str')
)


def is_same_route(x, y):
    if x.next_hop_type != y.next_hop_type:
        return False
    if x.next_hop_ip_address != y.next_hop_ip_address:
        return False
    if x.address_prefix != y.next_hop_type:
        return False
    return True


def route_to_dict(route):
    return dict(
        id=route.id,
        name=route.name,
        address_prefix=route.address_prefix,
        next_hop_type=route.next_hop_type,
        next_hop_ip_address=route.next_hop_ip_address
    )


def route_table_to_dict(table):
    return dict(
        id=table.id,
        name=table.name,
        routes=[route_to_dict(i) for i in table.routes] if table.routes else [],
        disable_bgp_route_propagation=table.disable_bgp_route_propagation,
        tags=table.tags
    )


class AzureRMRouteTable(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            routes=dict(type='list', elements='dict', options=route_spec),
            disable_bgp_route_propagation=dict(type='bool')
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.routes = None
        self.tags = None
        self.disable_bgp_route_propagation = None

        self.results = dict(
            changed=False
        )

        super(AzureRMRouteTable, self).__init__(self.module_arg_spec,
                                                supports_check_mode=True)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location
        self.location = normalize_location_name(self.location)

        self.results['check_mode'] = self.check_mode

        result = dict()
        changed = False

        result = self.get_table()
        self.routes = self.routes or []
        routes = []
        if self.state == 'absent' and result:
            changed = True
            self.delete_table()
        elif self.state == 'present':
            if not result:
                changed = True  # create new route table
                # create all route for the new table
                for i in self.routes:
                    route = self.network_models.route(name=i.name,
                                                      address_prefix=i.address_prefix,
                                                      next_hop_type=i.next_hop_type,
                                                      next_hop_ip_address=i.next_hop_ip_address)
                    route = self.create_or_update_route(route)
                    routes.append(route)
            else:  # check update
                update_tags, self.tags = self.update_tags(result.tags)
                if update_tags:
                    changed = True
                if self.disable_bgp_route_propagation != result.disable_bgp_route_propagation:
                    changed = True
                # compare route list, create the new or updated ones
                for route in self.routes:
                    route_matched = False
                    route_change = False
                    for origin in (result.routes or []):
                        if origin.name == route.name:
                            route_matched = True
                            route_change = not is_same_route(route, origin)
                    if not route_matched or route_change:
                        route = self.create_or_update_route(route)
                        routes.append(route)

                # delete the removing one
                for origin in (result.routes or []):
                    route_matched = False
                    for route in self.routes:
                        if origin.name == route.name:
                            route_matched = True
                    if not route_matched:
                        self.delete_route(origin.name)

            if changed:
                result = self.network_models.route_table(name=self.name,
                                                         location=self.location,
                                                         tags=self.tags,
                                                         disable_bgp_route_propagation=self.disable_bgp_route_propagation,
                                                         routes=routes)
                result = self.create_or_update_table(result)

        self.results = route_to_dict(result)
        self.results['changed'] = changed                
        return self.results

    def create_or_update_table(self, param):
        if self.check_mode:
            return param
        try:
            poller = self.network_client.route_tables.create_or_update(self.resource_group, self.name, param)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating route table {0} - {1}".format(self.name, str(exc)))

    def delete_table(self):
        if self.check_mode:
            return True
        try:
            poller = self.network_client.route_tables.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
            return result            
        except Exception as exc:
            self.fail("Error deleting virtual network {0} - {1}".format(self.name, str(exc)))

    def get_table(self):
        try:
            return self.network_client.route_tables.get(self.resource_group, self.name)
        except Exception as exc:
            self.log('Error getting route {0} - {1}'.format(self.name, str(exc)))
            return None

    def create_or_update_route(self, param):
        if self.check_mode:
            return param
        try:
            poller = self.network_client.routes.create_or_update(self.resource_group, self.name, param.name, param)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating route {0} under {1} - {2}".format(param.name, self.name, str(exc)))

    def delete_route(self, route_name):
        if self.check_mode:
            return True
        try:
            poller = self.network_client.routes.delete(self.resource_group, self.name, route_name)
            result = self.get_poller_result(poller)
            return result            
        except Exception as exc:
            self.fail("Error deleting virtual network {0} under {1} - {2}".format(route_name, self.name, str(exc)))

    def get_route(self, route_name):
        try:
            return self.network_client.routes.get(self.resource_group, self.name, route_name)
        except Exception as exc:
            self.log('Error getting route {0} under {1} - {2}'.format(route_name, self.name, str(exc)))
            return None

def main():
    AzureRMRouteTable()

if __name__ == '__main__':
    main()
