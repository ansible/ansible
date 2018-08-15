#!/usr/bin/python
#
# Copyright (c) 2018 Xiaoming Zheng, <xiaoming.zheng@icloud.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerprofile
version_added: "2.7"
short_description: Manage Azure Traffic Manager (profile).

description:
    - Create, update and delete a Traffic Manager profile. Python module azure-mgmt-trafficmanager >=0.50.0 is required.

options:
    name:
        description:
            - The name of the Traffic Manager profile.
        required: true
    resource_group:
        description:
            - The name of the resource group containing the Traffic Manager profile.
        required: true
    profile_status:
        description:
            - The status of the Traffic Manager profile.
        choices:
            - Enabled
            - Disabled
        default: Enabled
    traffic_routing_method:
        description:
            - The traffic routing method of the Traffic Manager profile.
        choices:
            - Performance
            - Priority
            - Weighted
            - Geographic
        default: Performance
    traffic_view_enrollment_status:
        description:
            - The traffic view enrollment status.
        choices:
            - Disabled
            - Enabled
        default: Disabled
    dns_config:
        description:
            - The configuration of DNS
        suboptions:
            relative_name:
                description:
                    - The name used to form FQDN. Defaut to Profile Name.
            ttl:
                description:
                    - The DNS Time-To-Live (TTL), in seconds. This informs the local DNS resolvers
                      and DNS clients how long to cache DNS responses provided by this Traffic Manager profile.
                default: 60
    monitor_config:
        description:
            - The endpoint monitoring settings of the Traffic Manager profile.
        required: true
        suboptions:
            protocol:
                description:
                    - The protocol (HTTP, HTTPS or TCP) used to probe for endpoint health.
                choices:
                    - Http
                    - Https
                    - Tcp
                    - HTTP
                    - HTTPS
                    - TCP
                default: HTTP
            port:
                description:
                    - The TCP port used to probe for endpoint health.
                default: 80
            path:
                description:
                    - The path relative to the endpoint domain name used to probe for
                      endpoint health.
                default: '/'
            interval_in_seconds:
                description:
                    - The monitor interval for endpoints in this profile. This is the interval
                      at which Traffic Manager will check the health of each endpoint in this profile.
                default: 30
            tolerated_number_of_failures:
                description:
                    - The number of consecutive failed health check that Traffic Manager tolerates
                      before declaring an endpoint in this profile Degraded after the next failed health check.
                default: 3
            timeout_in_seconds:
                description:
                    - The monitor timeout for endpoints in this profile. This is the time that
                      Traffic Manager allows endpoints in this profile to response to the health check.
                      The value must be greater than 4 and less than 'interval_in_seconds'.
                default: 10
    endpoints:
        description:
            - The list of endpoints in the Traffic Manager profile.
        suboptions:
            name:
                description:
                    - The name of the endpoint.
                required: true
            type:
                description:
                    - The type of the endpoint.
                choices:
                    - azureEndpoints
                    - externalEndpoints
                    - nestedEndpoints
                default: azureEndpoints
                required: true
            target:
                description:
                    - The fully-qualified DNS name or IP address of the endpoint.
                      Traffic Manager returns this value in DNS responses to direct traffic to this endpoint.
                required: true
            priority:
                description:
                    - The priority of this endpoint when using the 'Priority' traffic routing method.
                      Possible values are from 1 to 1000, lower values represent higher priority.
                      This is an optional parameter.  If specified, it must be specified on all endpoints,
                      and no two endpoints can share the same priority value.
            weight:
                description:
                    - The weight of this endpoint when using the 'Weighted' traffic routing method.
                      Possible values are from 1 to 1000.
            endpoint_location:
                description:
                    - Specifies the location of the external or nested endpoints when using the 'Performance' traffic routing method.
            target_resource_id:
                description:
                    - The Azure Resource URI of the of the endpoint.  Not applicable to endpoints of type 'ExternalEndpoints'.
            endpoint_status:
                description:
                    - The status of the endpoint.
                      If the endpoint is enabled, it is probed for endpoint health and is included in the traffic routing method.
                choices:
                    - Enabled
                    - Disabled
                default: Enabled
            min_child_endpoints:
                description:
                    - The minimum number of endpoints that must be available in the child profile in order for
                      the parent profile to be considered available. Only applicable to endpoint of type 'NestedEndpoints'.
            geo_mapping:
                description:
                    - The list of countries/regions mapped to this endpoint when using the 'Geographic' traffic routing method.

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
    - "Xiaoming Zheng(@siaomingjeng)"
'''

EXAMPLES = '''
    - name: Create Traffic Manager Profile
      azure_rm_trafficmanagerprofile:
        name: "xiaoming-tm"
        state: "present"
        resource_group: "telstra-rg"
        profile_status: "Enabled"
        traffic_routing_method: "Priority"
        dns_config:
            ttl: "300"
        monitor_config:
            protocol: "HTTP"
            port: 80
            path: "/monitor/index.html"
            interval_in_seconds: 30
            timeout_in_seconds: 10
            tolerated_number_of_failures: 3
        endpoints:
            - name: 'raymond'
              type: 'azureEndpoints'
              priority: 1
              target: 'raymond.australiasoutheast.cloudapp.azure.com'
              target_resource_id: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/XX/providers/Microsoft.Network/publicIPAddresses/raymond"
            - name: 'zheng'
              type: externalEndpoints
              weight: 2
              target: raymond.telstra.com
        tags:
            project: "API Project"

    - name: Delete a Traffic Manager Profile
      azure_rm_trafficmanagerprofile:
        name: "contoso.com"
        state: "absent"
'''

RETURN = '''
state:
    description: Current state of the Traffic Manager.
    returned: always
    type: dict
    sample: {
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing",
        "location": "global",
        "name": "Testing",
        "tags": {
            "delete": "on-exit",
            "testing": "no"
        }
    }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.trafficmanager.models import DnsConfig, Profile, MonitorConfig, Endpoint
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
except ImportError:
    pass


class AzureRMTrafficManager(AzureRMModuleBase):
    # Main Traffic Manager class

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(type='str', required=True),
            resource_group=dict(type='str', required=True),
            profile_status=dict(type='str', default='Enabled', choices=['Enabled', 'Disabled']),
            traffic_routing_method=dict(type='str', default='Performance', choices=['Performance', 'Priority', 'Weighted', 'Geographic']),
            traffic_view_enrollment_status=dict(type='str', default='Disabled', choices=['Disabled', 'Enabled']),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            dns_config=dict(type='dict', options=dict(
                relative_name=dict(type='str', required=False),
                ttl=dict(type='int', default=60)
            )),
            monitor_config=dict(type='dict', required=True, options=dict(
                protocol=dict(type='str', default='HTTP', choices=['Http', 'Https', 'Tcp', 'HTTP', 'HTTPS', 'TCP']),
                port=dict(type='int', default=80),
                path=dict(type='str', default='/'),
                interval_in_seconds=dict(type='int', default=30),
                tolerated_number_of_failures=dict(type='int', default=3),
                timeout_in_seconds=dict(type='int', default=10)
            )),
            endpoints=dict(type='list', elements='dict', options=dict(
                name=dict(type='str'),
                type=dict(type='str', default='azureEndpoints'),
                target=dict(type='str'),
                priority=dict(type='int'),
                target_resource_id=dict(type='str'),
                weight=dict(type='int'),
                endpoint_location=dict(type='str'),
                endpoint_status=dict(type='str', default='Enabled'),
                min_child_endpoints=dict(type='int'),
                geo_mapping=dict(type='list'))
            ))
        self.name = None
        self.resource_group = None
        self.profile_status = None
        self.traffic_routing_method = None
        self.traffic_view_enrollment_status = None
        self.dns_config = None
        self.monitor_config = None
        self.endpoints = None
        self.tags = None
        self.state = None
        self.results = dict(
            changed=False,
            state=dict())

        super(AzureRMTrafficManager, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):
        # Collect all the parameters and add them to the attributes
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        # Set default parameters
        if self.dns_config.get('relative_name') is None:
            self.dns_config['relative_name'] = self.name
        for end in self.endpoints:
            if end.get('type'):
                end['type'] = 'Microsoft.Network/trafficManagerProfiles/' + end['type']
        self.monitor_config['protocol'] = self.monitor_config['protocol'].upper()

        self.results['check_mode'] = self.check_mode
        # Initialize the Ansible return
        results = dict(resource_group=self.resource_group)
        changed = False

        # Get the existing Traffic Manager
        existing_traffic_manager = self.get_traffic_manager_profile(self.resource_group, self.name)
        if not self.check_mode:
            if self.state == 'present' and self.is_different(existing_traffic_manager):
                traffic_manager_as_dict = self.create_or_update_traffic_manager_profile(bool(existing_traffic_manager))
                results.update(traffic_manager_as_dict)
                changed = True
            elif self.state == 'absent' and bool(existing_traffic_manager):
                # Deletes the Traffic Manager and set change variable
                self.remove_traffic_manager_profile()
                changed = True
        self.results['changed'] = changed
        self.results['state'] = results
        return self.results

    def get_traffic_manager_profile(self, resource_group, name):
        '''
        Fetch a Traffic Manager profile. Return Traffic Manager object.
        '''
        try:
            self.log('Fetching Traffic Manager {0}'.format(name))
            self.trafficmanager_client = self.get_mgmt_svc_client(TrafficManagerManagementClient)
            profiles = self.trafficmanager_client.profiles.list_by_resource_group(resource_group)
            #  Check the profiles and return the one that matches the name
            for profile in profiles:
                if profile.name == name:
                    return self.trafficmanager_client.profiles.get(resource_group, name)
            return None  # if there is no profile returns None
        except CloudError as cloud_error:
            self.fail(
                "Error getting Traffic Manager profile with nanme: {0}. {1}".format(name, cloud_error))
        except Exception as exc:
            self.fail("Error retrieving Traffic Manager {0} - {1}".format(name, str(exc)))

    def remove_traffic_manager_profile(self):
        '''
        Remove the Traffic Manager profile. Return boolean True on successful deletion.
        '''
        self.log('Deleting Traffic Manager {0}'.format(self.name))
        try:
            self.trafficmanager_client.profiles.delete(self.resource_group, self.name)
        except CloudError as cloud_error:
            self.fail('Error getting Traffic Manager profile with nanme: {0}. {1}'.format(self.name, cloud_error))
        except Exception as exc:
            self.fail('Error retrieving Traffic Manager {0} - {1}'.format(self.name, str(exc)))

    def create_or_update_traffic_manager_profile(self, update):
        '''
        Create or update a Traffic Manager profile.
        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        self.log('Creating or updating Traffic Manager {0}'.format(self.name))
        try:
            # Create MonitorConfig
            monitor_config = MonitorConfig(protocol=self.monitor_config.get('protocol', 'HTTP'),
                                           port=self.monitor_config.get('port', 80),
                                           path=self.monitor_config.get('path', '/'),
                                           timeout_in_seconds=self.monitor_config.get('timeout_in_seconds', 10),
                                           interval_in_seconds=self.monitor_config.get('interval_in_seconds', 30),
                                           tolerated_number_of_failures=self.monitor_config.get('tolerated_number_of_failures', 3))
            # Create DnsConfig
            dns_config = DnsConfig(relative_name=self.dns_config.get('relative_name', self.name), ttl=self.dns_config.get('ttl', 60))

            # Create Endpoints
            endpoints = []
            for end in self.endpoints:
                endpoint_instance = Endpoint(name=end.get('name'), type=end.get('type'),
                                             target=end.get('target'), endpoint_status=end.get('endpoint_status', 'Enabled'),
                                             weight=end.get('weight'), priority=end.get('priority'),
                                             target_resource_id=end.get('target_resource_id'),
                                             endpoint_location=end.get('endpoint_location'),
                                             min_child_endpoints=end.get('min_child_endpoints'),
                                             geo_mapping=end.get('geo_mapping'))
                endpoints.append(endpoint_instance)

            profile = Profile(tags=self.tags, location="global", profile_status=self.profile_status,
                              traffic_routing_method=self.traffic_routing_method, dns_config=dns_config,
                              monitor_config=monitor_config,
                              endpoints=endpoints)
            return self.trafficmanager_client.profiles.create_or_update(self.resource_group, self.name, profile).as_dict()
        except CloudError as cloud_error:
            if update:
                self.fail('Error Updating the Traffic Manager: {0}. {1}'.format(self.name, str(cloud_error)))
            else:
                self.fail('Error Creating the Traffic Manager: {0}. {1}'.format(self.name, str(cloud_error)))
        except Exception as exc:
            self.fail('Error retrieving Traffic Manager {0} - {1}'.format(self.name, str(exc)))

    def is_different(self, existing_traffic_manager):
        '''
        Check if there is any difference between existing_traffic_manager and input parameters.
        Return True when existing_traffic_manager is empty or is different from self.trafficmanager_client.
        '''
        if bool(existing_traffic_manager):
            existing_profile = existing_traffic_manager.as_dict()
            for item in ['name', 'tags', 'traffic_view_enrollment_status', 'traffic_routing_method', 'profile_status']:
                value = getattr(self, item)
                if value and value != existing_profile.get(item):
                    return True
            for item in self.monitor_config.keys():
                value_given = self.monitor_config.get(item)
                if value_given:
                    value_cmp = existing_profile['monitor_config'].get(item)
                    if value_given != value_cmp:
                        return True
            if bool(self.dns_config):
                if self.dns_config.get('ttl', 60) != existing_profile['dns_config'].get('ttl') or \
                        self.dns_config.get('relative_name', self.name) != existing_profile['dns_config'].get('relative_name'):
                    return True

            if bool(self.endpoints):
                if not bool(existing_profile['endpoints']):
                    return True
                else:
                    value_cmp = self.list_to_dict(existing_profile['endpoints'])
                    value_given = self.list_to_dict(self.endpoints)
                    if not (set(value_cmp.keys()) <= set(value_given.keys())):
                        return True
                    for item in value_given.keys():
                        for k, v in value_given[item].items():
                            if v and v != value_cmp[item].get(k):
                                return True
            return False
        else:
            return True

    def list_to_dict(self, endpoints):
        result = {}
        for item in endpoints:
            result[item['name']] = item
        return result


def main():
    AzureRMTrafficManager()


if __name__ == '__main__':
    main()
