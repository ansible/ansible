#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_appgwroutetable
version_added: "2.5"
short_description: Manage Route Table instance.
description:
    - Create, update and delete instance of Route Table.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    route_table_name:
        description:
            - The name of the route table.
        required: True
    id:
        description:
            - Resource ID.
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    routes:
        description:
            - Collection of routes contained within a route table.
        type: list
        suboptions:
            id:
                description:
                    - Resource ID.
            address_prefix:
                description:
                    - The destination CIDR to which the route applies.
            next_hop_type:
                description:
                    - "The type of Azure hop the packet should be sent to. Possible values are: 'C(virtual_network_gateway)', 'C(vnet_local)', 'C(internet)',
                       'C(virtual_appliance)', and 'C(none)'."
                required: True
                choices:
                    - 'virtual_network_gateway'
                    - 'vnet_local'
                    - 'internet'
                    - 'virtual_appliance'
                    - 'none'
            next_hop_ip_address:
                description:
                    - The IP address packets should be forwarded to. Next hop values are only allowed in routes where the next hop type is C(virtual_appliance).
            provisioning_state:
                description:
                    - "The provisioning state of the resource. Possible values are: 'Updating', 'Deleting', and 'Failed'."
            name:
                description:
                    - The name of the resource that is unique within a resource group. This name can be used to access the resource.
            etag:
                description:
                    - A unique read-only string that changes whenever the resource is updated.
    disable_bgp_route_propagation:
        description:
            - Gets or sets whether to disable the I(routes) learned by BGP on that route table. True means disable.
    provisioning_state:
        description:
            - "The provisioning state of the resource. Possible values are: 'Updating', 'Deleting', and 'Failed'."
    etag:
        description:
            - Gets a unique read-only string that changes whenever the resource is updated.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) Route Table
    azure_rm_appgwroutetable:
      resource_group: rg1
      route_table_name: testrt
      location: eastus
'''

RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: /subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/routeTables/testrt
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.network import NetworkManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMRouteTables(AzureRMModuleBase):
    """Configuration class for an Azure RM Route Table resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            route_table_name=dict(
                type='str',
                required=True
            ),
            id=dict(
                type='str'
            ),
            location=dict(
                type='str'
            ),
            routes=dict(
                type='list'
            ),
            disable_bgp_route_propagation=dict(
                type='str'
            ),
            provisioning_state=dict(
                type='str'
            ),
            etag=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.route_table_name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMRouteTables, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                 supports_check_mode=True,
                                                 supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "id":
                    self.parameters["id"] = kwargs[key]
                elif key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "routes":
                    ev = kwargs[key]
                    if 'next_hop_type' in ev:
                        if ev['next_hop_type'] == 'virtual_network_gateway':
                            ev['next_hop_type'] = 'VirtualNetworkGateway'
                        elif ev['next_hop_type'] == 'vnet_local':
                            ev['next_hop_type'] = 'VnetLocal'
                        elif ev['next_hop_type'] == 'internet':
                            ev['next_hop_type'] = 'Internet'
                        elif ev['next_hop_type'] == 'virtual_appliance':
                            ev['next_hop_type'] = 'VirtualAppliance'
                        elif ev['next_hop_type'] == 'none':
                            ev['next_hop_type'] = 'None'
                    self.parameters["routes"] = ev
                elif key == "disable_bgp_route_propagation":
                    self.parameters["disable_bgp_route_propagation"] = kwargs[key]
                elif key == "provisioning_state":
                    self.parameters["provisioning_state"] = kwargs[key]
                elif key == "etag":
                    self.parameters["etag"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(NetworkManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_routetable()

        if not old_response:
            self.log("Route Table instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Route Table instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Route Table instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Route Table instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_routetable()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Route Table instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_routetable()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_routetable():
                time.sleep(20)
        else:
            self.log("Route Table instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_routetable(self):
        '''
        Creates or updates Route Table with the specified configuration.

        :return: deserialized Route Table instance state dictionary
        '''
        self.log("Creating / Updating the Route Table instance {0}".format(self.route_table_name))

        try:
            response = self.mgmt_client.route_tables.create_or_update(resource_group_name=self.resource_group,
                                                                      route_table_name=self.route_table_name,
                                                                      parameters=self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Route Table instance.')
            self.fail("Error creating the Route Table instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_routetable(self):
        '''
        Deletes specified Route Table instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Route Table instance {0}".format(self.route_table_name))
        try:
            response = self.mgmt_client.route_tables.delete(resource_group_name=self.resource_group,
                                                            route_table_name=self.route_table_name)
        except CloudError as e:
            self.log('Error attempting to delete the Route Table instance.')
            self.fail("Error deleting the Route Table instance: {0}".format(str(e)))

        return True

    def get_routetable(self):
        '''
        Gets the properties of the specified Route Table.

        :return: deserialized Route Table instance state dictionary
        '''
        self.log("Checking if the Route Table instance {0} is present".format(self.route_table_name))
        found = False
        try:
            response = self.mgmt_client.route_tables.get(resource_group_name=self.resource_group,
                                                         route_table_name=self.route_table_name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Route Table instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Route Table instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMRouteTables()

if __name__ == '__main__':
    main()
