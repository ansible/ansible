#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>, Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerendpoint
version_added: "2.7"
short_description: Manage Azure Traffic Manager endpoint
description:
    - Create, update and delete Azure Traffic Manager endpoint.

options:
    resource_group:
        description:
            - Name of a resource group where the Traffic Manager endpoint exists or will be created.
        type: str
        required: true
    name:
        description:
            - The name of the endpoint.
        type: str
        required: true
    profile_name:
        description:
            - Name of Traffic Manager profile where this endpoints attaches to.
        type: str
        required: true
    type:
        description:
            - The type of the endpoint.
        required: true
        choices:
            - azure_endpoints
            - external_endpoints
            - nested_endpoints
    target_resource_id:
        description:
            - The Azure Resource URI of the of the endpoint.
            - Not applicable to endpoints of I(type=external_endpoints).
        type: str
    target:
        description:
            - The fully-qualified DNS name of the endpoint.
        type: str
    enabled:
        description:
            - The status of the endpoint.
        type: bool
        default: true
    weight:
        description:
            - The weight of this endpoint when traffic manager profile has routing_method of C(weighted).
            - Possible values are from 1 to 1000.
        type: int
    priority:
        description:
            - The priority of this endpoint when traffic manager profile has routing_method of I(priority).
            - Possible values are from 1 to 1000, lower values represent higher priority.
            - This is an optional parameter. If specified, it must be specified on all endpoints.
            - No two endpoints can share the same priority value.
        type: int
    location:
        description:
            - Specifies the location of the external or nested endpoints when using the 'Performance' traffic routing method.
        type: str
    min_child_endpoints:
        description:
            - The minimum number of endpoints that must be available in the child profile in order for the parent profile to be considered available.
            - Only applicable to endpoint of I(type=nested_endpoints).
        type: int
    geo_mapping:
        description:
            - The list of countries/regions mapped to this endpoint when traffic manager profile has routing_method of C(geographic).
        type: list
    state:
        description:
            - Assert the state of the Traffic Manager endpoint. Use C(present) to create or update a Traffic Manager endpoint and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - Hai Cao (@caohai)
    - Yunge Zhu (@yungezz)

'''

EXAMPLES = '''
  - name: create a endpoint for a traffic manager profile
    azure_rm_trafficmanagerendpoint:
        resource_group: testresourcegroup
        profile_name: myprofilename
        name: testendpoint1
        type: external_endpoints
        location: westus
        priority: 2
        weight: 1
        target: 1.2.3.4
'''

RETURN = '''
id:
    description:
        - The ID of the traffic manager endpoint.
    returned: when traffic manager endpoint exists
    type: str
    example:
        "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/trafficManagerProfiles/testProfil
        e/externalEndpoints/testendpoint"
'''
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, normalize_location_name
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.trafficmanager.models import (
        Endpoint, DnsConfig, MonitorConfig
    )
except ImportError:
    # This is handled in azure_rm_common
    pass


def traffic_manager_endpoint_to_dict(endpoint):
    return dict(
        id=endpoint.id,
        name=endpoint.name,
        type=endpoint.type,
        target_resource_id=endpoint.target_resource_id,
        target=endpoint.target,
        status=endpoint.endpoint_status,
        weight=endpoint.weight,
        priority=endpoint.priority,
        location=endpoint.endpoint_location,
        monitor_status=endpoint.endpoint_monitor_status,
        min_child_endpoints=endpoint.min_child_endpoints,
        geo_mapping=endpoint.geo_mapping
    )


class Actions:
    NoAction, CreateOrUpdate, Delete = range(3)


class AzureRMTrafficManagerEndpoint(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            profile_name=dict(
                type='str',
                required=True
            ),
            type=dict(
                type='str',
                choices=['azure_endpoints', 'external_endpoints', 'nested_endpoints'],
                required=True
            ),
            target=dict(type='str'),
            target_resource_id=dict(type='str'),
            enabled=dict(type='bool', default=True),
            weight=dict(type='int'),
            priority=dict(type='int'),
            location=dict(type='str'),
            min_child_endpoints=dict(type='int'),
            geo_mapping=dict(type='list', elements='str'),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
        )

        self.resource_group = None
        self.name = None
        self.state = None

        self.profile_name = None
        self.type = None
        self.target_resource_id = None
        self.enabled = None
        self.weight = None
        self.priority = None
        self.location = None
        self.min_child_endpoints = None
        self.geo_mapping = None
        self.endpoint_status = 'Enabled'

        self.action = Actions.NoAction

        self.results = dict(
            changed=False
        )

        super(AzureRMTrafficManagerEndpoint, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                            supports_check_mode=True,
                                                            supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        if self.type:
            self.type = _snake_to_camel(self.type)

        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        if self.enabled is not None and self.enabled is False:
            self.endpoint_status = 'Disabled'

        response = self.get_traffic_manager_endpoint()

        if response:
            self.log('Results : {0}'.format(response))
            self.results['id'] = response['id']
            if self.state == 'present':
                # check update
                to_be_update = self.check_update(response)
                if to_be_update:
                    self.action = Actions.CreateOrUpdate

            elif self.state == 'absent':
                # delete
                self.action = Actions.Delete
        else:
            if self.state == 'present':
                self.action = Actions.CreateOrUpdate
            elif self.state == 'absent':
                # delete when no exists
                self.fail("Traffic Manager endpoint {0} not exists.".format(self.name))

        if self.action == Actions.CreateOrUpdate:
            self.results['changed'] = True
            if self.check_mode:
                return self.results

            response = self.create_update_traffic_manager_endpoint()
            self.results['id'] = response['id']

        if self.action == Actions.Delete:
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            response = self.delete_traffic_manager_endpoint()

        return self.results

    def get_traffic_manager_endpoint(self):
        '''
        Gets the properties of the specified Traffic Manager endpoint

        :return: deserialized Traffic Manager endpoint dict
        '''
        self.log("Checking if Traffic Manager endpoint {0} is present".format(self.name))
        try:
            response = self.traffic_manager_management_client.endpoints.get(self.resource_group, self.profile_name, self.type, self.name)
            self.log("Response : {0}".format(response))
            return traffic_manager_endpoint_to_dict(response)
        except CloudError:
            self.log('Did not find the Traffic Manager endpoint.')
            return False

    def delete_traffic_manager_endpoint(self):
        '''
        Deletes the specified Traffic Manager endpoint.
        :return: True
        '''

        self.log("Deleting the Traffic Manager endpoint {0}".format(self.name))
        try:
            operation_result = self.traffic_manager_management_client.endpoints.delete(self.resource_group, self.profile_name, self.type, self.name)
            return True
        except CloudError as exc:
            request_id = exc.request_id if exc.request_id else ''
            self.fail("Error deleting the Traffic Manager endpoint {0}, request id {1} - {2}".format(self.name, request_id, str(exc)))
            return False

    def create_update_traffic_manager_endpoint(self):
        '''
        Creates or updates a Traffic Manager endpoint.

        :return: deserialized Traffic Manager endpoint state dictionary
        '''
        self.log("Creating / Updating the Traffic Manager endpoint {0}".format(self.name))

        parameters = Endpoint(target_resource_id=self.target_resource_id,
                              target=self.target,
                              endpoint_status=self.endpoint_status,
                              weight=self.weight,
                              priority=self.priority,
                              endpoint_location=self.location,
                              min_child_endpoints=self.min_child_endpoints,
                              geo_mapping=self.geo_mapping)

        try:
            response = self.traffic_manager_management_client.endpoints.create_or_update(self.resource_group,
                                                                                         self.profile_name,
                                                                                         self.type,
                                                                                         self.name,
                                                                                         parameters)
            return traffic_manager_endpoint_to_dict(response)
        except CloudError as exc:
            request_id = exc.request_id if exc.request_id else ''
            self.fail("Error creating the Traffic Manager endpoint {0}, request id {1} - {2}".format(self.name, request_id, str(exc)))

    def check_update(self, response):
        if self.endpoint_status is not None and response['status'].lower() != self.endpoint_status.lower():
            self.log("Status Diff - Origin {0} / Update {1}".format(response['status'], self.endpoint_status))
            return True

        if self.type and response['type'].lower() != "Microsoft.network/TrafficManagerProfiles/{0}".format(self.type).lower():
            self.log("Type Diff - Origin {0} / Update {1}".format(response['type'], self.type))
            return True

        if self.target_resource_id and response['target_resource_id'] != self.target_resource_id:
            self.log("target_resource_id Diff - Origin {0} / Update {1}".format(response['target_resource_id'], self.target_resource_id))
            return True

        if self.target and response['target'] != self.target:
            self.log("target Diff - Origin {0} / Update {1}".format(response['target'], self.target))
            return True

        if self.weight and int(response['weight']) != self.weight:
            self.log("weight Diff - Origin {0} / Update {1}".format(response['weight'], self.weight))
            return True

        if self.priority and int(response['priority']) != self.priority:
            self.log("priority Diff - Origin {0} / Update {1}".format(response['priority'], self.priority))
            return True

        if self.min_child_endpoints and int(response['min_child_endpoints']) != self.min_child_endpoints:
            self.log("min_child_endpoints Diff - Origin {0} / Update {1}".format(response['min_child_endpoints'], self.min_child_endpoints))
            return True

        if self.geo_mapping and response['geo_mapping'] != self.geo_mapping:
            self.log("geo_mapping Diff - Origin {0} / Update {1}".format(response['geo_mapping'], self.geo_mapping))
            return True

        return False


def main():
    """Main execution"""
    AzureRMTrafficManagerEndpoint()


if __name__ == '__main__':
    main()
