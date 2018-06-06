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
    disable_bgp_route_propagation:
        description:
            - Gets or sets whether to disable the routes learned by BGP on that route table.
            - True means disable.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Create a route
      azure_rm_routetable:
        name: foobar
        resource_group: Testing
        disable_bgp_route_propagation: False

    - name: Delete a route
      azure_rm_routetable:
        name: foobar
        resource_group: Testing
        state: absent
'''
RETURN = '''
state:
    description: Current state of the route table.
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


def route_table_to_dict(table):
    return dict(
        id=table.id,
        name=table.name,
        routes=[dict(id=i.id, name=i.name) for i in table.routes] if table.routes else [],
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
            disable_bgp_route_propagation=dict(type='bool')
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
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
        if self.state == 'absent' and result:
            changed = True
            self.delete_table()
        elif self.state == 'present':
            if not result:
                changed = True  # create new route table
            else:  # check update
                update_tags, self.tags = self.update_tags(result.tags)
                if update_tags:
                    changed = True
                if self.disable_bgp_route_propagation != result.disable_bgp_route_propagation:
                    changed = True

            if changed:
                result = self.network_models.RouteTable(name=self.name,
                                                        location=self.location,
                                                        tags=self.tags,
                                                        disable_bgp_route_propagation=self.disable_bgp_route_propagation)
                if not self.check_mode:
                    result = self.create_or_update_table(result)

        self.results = route_table_to_dict(result)
        self.results['changed'] = changed                
        return self.results

    def create_or_update_table(self, param):
        try:
            poller = self.network_client.route_tables.create_or_update(self.resource_group, self.name, param)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating route table {0} - {1}".format(self.name, str(exc)))

    def delete_table(self):
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


def main():
    AzureRMRouteTable()

if __name__ == '__main__':
    main()
