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
module: azure_rm_routetable
version_added: "2.7"
short_description: Manage Azure route table resource.
description:
    - Create, update or delete a route table.
options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the route table.
        required: true
    state:
        description:
            - Assert the state of the route table. Use C(present) to create or update and
              C(absent) to delete.
        default: present
        choices:
            - absent
            - present
    disable_bgp_route_propagation:
        description:
            - Specified whether to disable the routes learned by BGP on that route table.
        type: bool
        default: False
    location:
        description:
            - Region of the resource.
            - Derived from C(resource_group) if not specified

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Create a route table
      azure_rm_routetable:
        resource_group: myResourceGroup
        name: myRouteTable
        disable_bgp_route_propagation: False
        tags:
          purpose: testing

    - name: Delete a route table
      azure_rm_routetable:
        resource_group: myResourceGroup
        name: myRouteTable
        state: absent
'''
RETURN = '''
changed:
    description: Whether the resource is changed.
    returned: always
    type: bool
id:
    description: resource id.
    returned: success
    type: str
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, normalize_location_name


class AzureRMRouteTable(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            disable_bgp_route_propagation=dict(type='bool', default=False)
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

        result = dict()
        changed = False

        result = self.get_table()
        if self.state == 'absent' and result:
            changed = True
            if not self.check_mode:
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
                result = self.network_models.RouteTable(location=self.location,
                                                        tags=self.tags,
                                                        disable_bgp_route_propagation=self.disable_bgp_route_propagation)
                if not self.check_mode:
                    result = self.create_or_update_table(result)

        self.results['id'] = result.id if result else None
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
        except CloudError as cloud_err:
            # Return None iff the resource is not found
            if cloud_err.status_code == 404:
                self.log('{0}'.format(str(cloud_err)))
                return None
            self.fail('Error: failed to get resource {0} - {1}'.format(self.name, str(cloud_err)))
        except Exception as exc:
            self.fail('Error: failed to get resource {0} - {1}'.format(self.name, str(exc)))


def main():
    AzureRMRouteTable()


if __name__ == '__main__':
    main()
