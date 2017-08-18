#!/usr/bin/python
#
# Copyright (c) 2016 Julio Colon, <julio.colon@microsoft.com>
#                    Diego Casati, <diego.casati@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerendpoints
version_added: "2.4"
short_description: Manage Azure Traffic Manager (endpoints).
description:
    - Create, update and delete a traffic manager endpoints.
options:

    name:
        description:
             - The name of the Traffic Manager endpoints.
        default: false
        required: true
    resource_group:
        description:
             - The name of the resource group containing the Traffic Manager endpoints.
        required: true
    endpoint_status:
        description:
            - The status of the Traffic Manager endpoints. 
            choices:
                - Enabled
                - Disabled
    traffic_routing_method:
        description:
            - The traffic routing method of the Traffic Manager endpoints. Possible 
            values include: 'Performance', 'Priority', 'Weighted', 'Geographic'.
    dns_config:
        description:
            - The DNS settings of the Traffic Manager endpoints. This section includes
            relative_name and ttl.
        required: true
        suboptions:
            ttl:
                description:
                    - The DNS Time-To-Live (TTL), in seconds. This informs the 
                    local DNS resolvers and DNS clients how long to cache DNS 
                    responses provided by this Traffic Manager endpoints.
    monitor_config:
        description:
            - The endpoint monitoring settings of the Traffic Manager endpoints.
        required: true
	suboptions:
            status:
                description:
                    - The endpoints-level monitoring status of the Traffic Manager endpoints. 
                    choices:
                        - CheckingEndpoints
                        - Online
                        - Degraded
                        - Disabled
                        - Inactive
            protocol:
                description:
                    - The protocol (HTTP, HTTPS or TCP) used to probe for endpoint health. 
                    choices:
                        - HTTP
                        - HTTPS
                        - TCP
            port:
                description:
                    - The TCP port used to probe for endpoint health.
            path:
                description:
                    - The path relative to the endpoint domain name used to probe for 
                    endpoint health.
            interval_in_seconds:
                description:
                    - The monitor interval for endpoints in this endpoints. This is the interval 
                    at which Traffic Manager will check the health of each endpoint in this endpoints.
            timeout_in_seconds:
                description:
                    - The monitor timeout for endpoints in this endpoints. This is the time that 
                    Traffic Manager allows endpoints in this endpoints to response to the health check.
            tolerated_number_of_failures:
                description:
                    - The number of consecutive failed health check that Traffic Manager tolerates 
                    before declaring an endpoint in this endpoints Degraded after the next failed health check.
    state:
        description:
            - Assert the state of the resource group. Use 'present' to create or update and
              'absent' to delete. When 'absent' a resource group containing resources 
              will not be removed unless the force option is used.
        default: present
        choices:
            - absent
            - present
        required: false
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Julio Colon (@code4clouds)"
    - "Diego Casati (@diegocasati)"

'''

EXAMPLES = '''
    - name: Create Traffic Manager Profile
      azure_rm_trafficmanagerendpoints:
        name: "contoso.com"
        state: "present"
        resource_group: "ContosoRG"
        properties:
          endpoint_status: "Enabled"
          traffic_routing_method: "Performance"
          dns_config:
            ttl: "300"
          monitor_config:
            protocol: "HTTP"
            port: 80
            path: "/monitor/index.html"
            status: "Active"
            interval_in_seconds: 30
            timeout_in_seconds: 10
            tolerated_number_of_failures: 3
          endpoint_type: ""
          tags:
            project: "My Project"
  
    - name: Delete a Traffic Manager Profile
      azure_rm_trafficmanagerendpoints:
        name: "contoso.com"
        state: "absent"

'''
RETURN = '''
contains_resources:
    description: Contains associated resources.
    returned: always
    type: bool
    sample: True
state:
    description: Current state of the resource group.
    returned: always
    type: dict
    sample: {
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing",
        "location": "westus",
        "name": "Testing",
        "provisioning_state": "Succeeded",
        "tags": {
            "delete": "on-exit",
            "testing": "no"
        }
    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.trafficmanager.models import Endpoint, DnsConfig, Profile, MonitorConfig
except ImportError:
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def trafficmanagerendpoints_group_to_dict(tm):
    return dict(
        id=tm.id,
        name=tm.name,
        resource_group=tm.resource_group,
        endpoint_type=tm.endpoint_type,
        tags=tm.tags,
    )


class AzureRMTrafficManagerEndpoints(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            profile_name=dict(type='str', required=True),
            endpoint_type=dict(type='str'),
            endpoint_name=dict(type='str'),
            properties=dict(type='dict'),
            status=dict(type='str', default='Enabled', choices=['Enabled', 'Disabled']),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        self.resource_group = None
        self.profile_name = None
        self.endpoint_type = None
        self.endpoint_name = None
        self.properties = None
        self.status = None
        self.state = None

        self.results = dict(
            changed=False,
            contains_endpoints=False,
            state=dict(),
        )

        super(AzureRMTrafficManagerEndpoints, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        # Collect all the tags and add them to the attributes
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # Initialize the Ansible return
        results = dict()
        changed = False


        try:
            if self.state == 'present':
                self.log('Fetching traffic manager profile {0}'.format(self.profile_name))

                endpoint = self.create_or_update_traffic_manager_endpoints(self.resource_group, self.profile_name,
                                                                self.endpoint_type, self.endpoint_name, self.properties)

                #TODO
                #results = self.endpoint_to_dict(endpoint, self.resource_group, self.profile_name,
                #                                       self.endpoint_type, self.endpoint_name, self.properties)
                changed = True
                if endpoint is None:
                    results['status'] = 'Created'
                else:
                    results['status'] = 'Updated'

            elif self.state == 'absent':
                self.log('Deleting traffic manager endpoint {0}'.format(self.endpoint_name))
                endpoint = self.trafficmanager_client.endpoints.get(self.resource_group, self.profile_name,
                                                                    self.endpoint_type, self.endpoint_name)

                if endpoint is not None:
                    # Deletes the traffic manager and set change variable
                    endpoint = self.trafficmanager_client.endpoints.delete(self.resource_group, self.profile_name,
                                                                            self.endpoint_type, self.endpoint_name)
                    changed = True
                    results['status'] = 'Deleted'

        except CloudError:
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        return self.results

    def endpoint_to_dict(self, endpoint, resource_group, profile_name,
                            endpoint_type, endpoint_name, properties):

        '''
        Converts a traffic manager endpoint to a dictionary

        :param name: name of a traffic  manager endpoint
        :return: traffic manage object
        '''


    def create_or_update_traffic_manager_endpoints(self, resource_group, profile_name, endpoint_type, endpoint_name, parameters):
        '''
        Create or update a traffic manager endpoints.

        :param profile_name: name of a traffic  manager
        :return: traffic manage object
        '''

        target_resource_id = parameters.get('target_resource_id', None)
        target = parameters.get('target', None)
        endpoint_status = parameters.get('endpoint_status', None)
        weight = parameters.get('weight', None)
        priority = parameters.get('priority', None)
        endpoint_location = parameters.get('endpoint_location', None)
        endpoint_monitor_status = parameters.get('endpoint_monitor_status', None)
        min_child_endpoints = parameters.get('min_child_endpoints', None)
        geo_mapping = parameters.get('geo_mapping', None)

        endpoint_parameters = Endpoint(target_resource_id, target, endpoint_status, weight, priority, endpoint_location,
                                        endpoint_monitor_status, min_child_endpoints, geo_mapping)

        try:
            return self.trafficmanager_client.endpoints.create_or_update(resource_group, profile_name, endpoint_type, endpoint_name, endpoint_parameters)
        except CloudError as cloudError:
            self.fail("Error creating or updating traffic manager endpoints with name {0}.  {1}"
                      .format(profile_name, cloudError))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(profile_name, str(exc)))



def main():
    AzureRMTrafficManagerEndpoints()

if __name__ == '__main__':
    main()
