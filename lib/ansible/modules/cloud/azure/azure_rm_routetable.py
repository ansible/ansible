#!/usr/bin/python
#
# Copyright (c) 2018 Tom Vachon, <github@thomasvachon.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: azure_rm_routetable
version_added: "2.5"
short_description: Manage Azure route tables.
description:
    - Create, update or delete a route tables. Allows setting and updating the available routes with cidr, type, and destination
options:
    resource_group:
        description:
            - name of resource group.
        required: true
    routes:
        description:
            - A list of mappings which has name, address_prefix, next_hop_type, and next_hop_ip_address set to populate the
              routes in the route table. Required if I(state=present)
        default: null
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    name:
        description:
            - name of the virtual network.
        required: true
    purge_routes:
        description:
            - Use with state present to remove any existing routes and replace with defined routes
        default: false
    state:
        description:
            - Assert the state of the virtual network. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Thomas Vachon (@TomVachon)"

'''

EXAMPLES = '''
    - name: Create a virtual network
      azure_rm_routetable:
        name: foobar
        resource_group: Testing
        routes:
            -
                name: "My Route Table"
                address_prefix: "10.0.0.0/16"
                next_hop_type: "VirtualAppliance"
                next_hop_ip_address: "1.2.3.4"
        tags:
            testing: testing
            delete: on-exit

    - name: Delete a route table
      azure_rm_routetable:
        name: foobar
        resource_group: Testing
        state: absent
'''

RETURN = '''
state:
    description: Current state of the route table
    returned: always
    type: dict
    sample: {
      "routes": [
        {
            "name": "myrt",
            "address_prefix": "10.0.0.0/16",
            "next_hop_type": "VirtualAppliance",
            "next_hop_ip_address": "1.2.3.4",
            "provisioning_state": "Succeeded",
            "etag": 'W/"0712e87c-f02f-4bb3-8b9e-2da0390a3886"',
            "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/routeTables/myrt/routes/my_route_name"
        }],
        "etag": 'W/"0712e87c-f02f-4bb3-8b9e-2da0390a3886"',
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/routet/Testing/providers/Microsoft.Network/routeTables/myrt",
        "location": "eastus",
        "name": "my_route_table",
        "provisioning_state": "Succeeded",
        "tags": null,
        "type": "Microsoft.Network/routeTables"
    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import RouteTable, Route
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN

NEXT_HOP_TYPE = ['VirtualNetworkGateway', 'VnetLocal', 'Internet', 'VirtualAppliance']


def route_table_to_dict(routetable):
    '''
    Convert a route table object to a dict.
    :param routetable: RouteTable object
    :return: dict
    '''
    results = dict(
        id=routetable.id,
        name=routetable.name,
        location=routetable.location,
        type=routetable.type,
        tags=routetable.tags,
        provisioning_state=routetable.provisioning_state,
        etag=routetable.etag
    )
    if routetable.routes and len(routetable.routes) > 0:
        results['routes'] = []
        for route in routetable.routes:
            route_to_dict = dict(
                name=route.name,
                next_hop_type=route.next_hop_type,
                address_prefix=route.address_prefix,
                next_hop_ip_address=route.next_hop_ip_address,
                provisioning_state=route.provisioning_state,
                etag=route.etag,
                id=route.id
            )
            results['routes'].append(route_to_dict)
    return results


class AzureRMRouteTable(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            routes=dict(default=[], required=False, type='list'),
            purge_routes=dict(type='bool', default=False, aliases=['purge'])
        )

        required_if = [
            ['purge_routes', True, ['routes']],
            ["state", "present", ['routes']]
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.routes = None
        self.purge_routes = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMRouteTable, self).__init__(self.module_arg_spec,
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

        if self.state == 'present':

            if self.purge_routes and not self.routes:
                self.fail("Purge routes requires routes to be set")

            for route in self.routes:
                if not CIDR_PATTERN.match(route.get('address_prefix')):
                    self.fail("Parameter error: invalid address prefix value {0}".format(route['address_prefix']))
                if not route.get('next_hop_type') in NEXT_HOP_TYPE:
                    self.fail("Parameter error: invalid next hop value {0}".format(route['next_hop_type']))
                if not route.get('name'):
                    self.fail("Parameter error: invalid name value {0}".format(route['name']))
                if route['next_hop_type'] == 'VirtualAppliance' and not route.get('next_hop_ip_address'):
                    self.fail("Parameter error: Next Hop Required for VirtualAppliance")

        changed = False
        results = dict()

        try:
            self.log('Fetching route table {0}'.format(self.name))
            routetable = self.network_client.route_tables.get(self.resource_group, self.name)
            results = route_table_to_dict(routetable)
            self.log('Route Table exists {0}'.format(self.name))
            self.log(results, pretty_print=True)
            self.check_provisioning_state(routetable, self.state)

            if self.state == 'present':
                if self.routes:
                    requested_routing_entries = self.routes

                    existing_route_entries = []
                    for existing_route in routetable.routes:
                        existing_route_entries.append(dict(
                            address_prefix=existing_route.address_prefix,
                            next_hop_type=existing_route.next_hop_type,
                            next_hop_ip_address=existing_route.next_hop_ip_address,
                            name=existing_route.name))

                    missing_routes = [x for x in requested_routing_entries if x not in existing_route_entries]
                    extra_routes = [x for x in existing_route_entries if x not in requested_routing_entries]

                    for route in self.routes:
                        for extra_route in extra_routes:
                            if route['name'] in extra_route['name'] and not self.purge_routes:
                                self.fail('Duplicate route entry name detected, purge routes required')

                    if len(missing_routes) > 0:
                        self.log('CHANGED: there are missing routes')
                        changed = True
                        if not self.purge_routes:
                            # add the missing routes
                            for route in missing_routes:
                                results['routes'] + extra_routes
                                results['routes'].append(route)

                    if len(extra_routes) > 0 and self.purge_routes:
                        self.log('CHANGED: there are routes to purge')
                        changed = True
                        # replace existing routes with requested set
                        results['routes'] = self.routes

            update_tags, results['tags'] = self.update_tags(results['tags'])
            if update_tags:
                changed = True

            elif self.state == 'absent':
                self.log("CHANGED: routes exists but requested state is 'absent'")
                changed = True
        except CloudError:
            self.log('Route {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: route {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                if not results:
                    # create a new route table
                    self.log("Create route table {0}".format(self.name))
                    routetable = RouteTable(
                        location=self.location
                    )
                    if self.routes:
                        route_entries = []
                        for route in self.routes:
                            routing_entry = Route(
                                name=route['name'],
                                next_hop_type=route['next_hop_type'],
                                address_prefix=route['address_prefix'],
                                next_hop_ip_address=route.get('next_hop_ip_address')
                            )
                            route_entries.append(routing_entry)
                        routetable.routes = route_entries
                    if self.tags:
                        routetable.tags = self.tags
                    self.results['state'] = self.create_or_update_routetable(routetable)
                else:
                    # update existing route table
                    self.log("Update route table {0}".format(self.name))
                    routetable = RouteTable(
                        location=results['location'],
                        tags=results['tags']
                    )
                    if results['routes']:
                        route_entries = []
                        for route in results['routes']:
                            routing_entry = Route(
                                name=route['name'],
                                next_hop_type=route['next_hop_type'],
                                address_prefix=route['address_prefix'],
                                next_hop_ip_address=route.get('next_hop_ip_address')
                            )
                            route_entries.append(routing_entry)
                    routetable.routes = route_entries
                    self.results['state'] = self.create_or_update_routetable(routetable)

            elif self.state == 'absent':
                self.delete_route_table()

        return self.results

    def create_or_update_routetable(self, routetable):
        try:
            poller = self.network_client.route_tables.create_or_update(self.resource_group, self.name, routetable)
            new_routetable = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating route table {0} - {1}".format(self.name, str(exc)))
        return route_table_to_dict(new_routetable)

    def delete_route_table(self):
        try:
            poller = self.network_client.route_tables.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting route table {0} - {1}".format(self.name, str(exc)))
        return result


def main():
    AzureRMRouteTable()

if __name__ == '__main__':
    main()
