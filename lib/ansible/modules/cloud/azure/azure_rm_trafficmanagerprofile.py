#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com> Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerprofile
version_added: "2.7"
short_description: Manage Azure Traffic Manager profile.
description:
    - Create, update and delete a Traffic Manager profile.

options:
    resource_group:
        description:
            - Name of a resource group where the Traffic Manager profile exists or will be created.
        required: true
    name:
        description:
            - Name of the Traffic Manager profile.
        required: true
    state:
        description:
            - Assert the state of the Traffic Manager profile. Use C(present) to create or update a Traffic Manager profile and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to 'global' because in default public Azure cloud, Traffic Manager profile can only be deployed globally.
            - Reference https://docs.microsoft.com/en-us/azure/traffic-manager/quickstart-create-traffic-manager-profile#create-a-traffic-manager-profile
        default: global
    profile_status:
        description:
            - The status of the Traffic Manager profile.
        default: enabled
        choices:
            - enabled
            - disabled
    routing_method:
        description:
            - The traffic routing method of the Traffic Manager profile.
        default: performance
        choices:
            - performance
            - priority
            - weighted
            - geographic
    dns_config:
        description:
            - The DNS settings of the Traffic Manager profile.
        suboptions:
            relative_name:
                description:
                    - The relative DNS name provided by this Traffic Manager profile.
                    - If not provided, name of the Traffic Manager will be used
            ttl:
                description:
                    - The DNS Time-To-Live (TTL), in seconds.
                default: 60
    monitor_config:
        description:
            - The endpoint monitoring settings of the Traffic Manager profile.
        suboptions:
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
                    - The path relative to the endpoint domain name used to probe for endpoint health.
            interval:
                description:
                    - The monitor interval for endpoints in this profile in seconds.
            timeout:
                description:
                    - The monitor timeout for endpoints in this profile in seconds.
            tolerated_failures:
                description:
                    - The number of consecutive failed health check before declaring an endpoint in this profile Degraded after the next failed health check.
        default:
            protocol: HTTP
            port: 80
            path: /

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Hai Cao (@caohai) <t-haicao@microsoft.com>"
    - "Yunge Zhu (@yungezz) <yungez@microsoft.com>"

'''

EXAMPLES = '''
    - name: Create a Traffic Manager Profile
      azure_rm_trafficmanagerprofile:
        name: tmtest
        resource_group: myResourceGroup
        location: global
        profile_status: enabled
        routing_method: priority
        dns_config:
          relative_name: tmtest
          ttl: 60
        monitor_config:
          protocol: HTTPS
          port: 80
          path: '/'
        tags:
          Environment: Test

    - name: Delete a Traffic Manager Profile
      azure_rm_trafficmanagerprofile:
        state: absent
        name: tmtest
        resource_group: myResourceGroup
'''
RETURN = '''
id:
    description: The ID of the traffic manager profile
    returned: when traffic manager profile exists
    type: str
    example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/tmt/providers/Microsoft.Network/trafficManagerProfiles/tmtest"
endpoints:
  description: List of endpoint IDs attached to the profile
  returned: when traffic manager endpoints exists
  type: list
  sample: [
        "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/tmt/providers/Microsoft.Network/trafficManagerProfiles/tm049b1ae293/exter
         nalEndpoints/e2",
        "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/tmt/providers/Microsoft.Network/trafficManagerProfiles/tm049b1ae293/exter
         nalEndpoints/e1"
    ]
'''
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, normalize_location_name

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.trafficmanager.models import (
        Profile, Endpoint, DnsConfig, MonitorConfig
    )
except ImportError:
    # This is handled in azure_rm_common
    pass


def shorten_traffic_manager_dict(tmd):
    return dict(
        id=tmd['id'],
        endpoints=[endpoint['id'] for endpoint in tmd['endpoints']] if tmd['endpoints'] else []
    )


def traffic_manager_profile_to_dict(tmp):
    result = dict(
        id=tmp.id,
        name=tmp.name,
        type=tmp.type,
        tags=tmp.tags,
        location=tmp.location,
        profile_status=tmp.profile_status,
        routing_method=tmp.traffic_routing_method,
        dns_config=dict(),
        monitor_config=dict(),
        endpoints=[]
    )
    if tmp.dns_config:
        result['dns_config']['relative_name'] = tmp.dns_config.relative_name
        result['dns_config']['fqdn'] = tmp.dns_config.fqdn
        result['dns_config']['ttl'] = tmp.dns_config.ttl
    if tmp.monitor_config:
        result['monitor_config']['profile_monitor_status'] = tmp.monitor_config.profile_monitor_status
        result['monitor_config']['protocol'] = tmp.monitor_config.protocol
        result['monitor_config']['port'] = tmp.monitor_config.port
        result['monitor_config']['path'] = tmp.monitor_config.path
        result['monitor_config']['interval'] = tmp.monitor_config.interval_in_seconds
        result['monitor_config']['timeout'] = tmp.monitor_config.timeout_in_seconds
        result['monitor_config']['tolerated_failures'] = tmp.monitor_config.tolerated_number_of_failures
    if tmp.endpoints:
        for endpoint in tmp.endpoints:
            result['endpoints'].append(dict(
                id=endpoint.id,
                name=endpoint.name,
                type=endpoint.type,
                target_resource_id=endpoint.target_resource_id,
                target=endpoint.target,
                endpoint_status=endpoint.endpoint_status,
                weight=endpoint.weight,
                priority=endpoint.priority,
                endpoint_location=endpoint.endpoint_location,
                endpoint_monitor_status=endpoint.endpoint_monitor_status,
                min_child_endpoints=endpoint.min_child_endpoints,
                geo_mapping=endpoint.geo_mapping
            ))
    return result


def create_dns_config_instance(dns_config):
    return DnsConfig(
        relative_name=dns_config['relative_name'],
        ttl=dns_config['ttl']
    )


def create_monitor_config_instance(monitor_config):
    return MonitorConfig(
        profile_monitor_status=monitor_config['profile_monitor_status'],
        protocol=monitor_config['protocol'],
        port=monitor_config['port'],
        path=monitor_config['path'],
        interval_in_seconds=monitor_config['interval'],
        timeout_in_seconds=monitor_config['timeout'],
        tolerated_number_of_failures=monitor_config['tolerated_failures']
    )


dns_config_spec = dict(
    relative_name=dict(type='str'),
    ttl=dict(type='int')
)

monitor_config_spec = dict(
    profile_monitor_status=dict(type='str'),
    protocol=dict(type='str'),
    port=dict(type='int'),
    path=dict(type='str'),
    interval=dict(type='int'),
    timeout=dict(type='int'),
    tolerated_failures=dict(type='int')
)


class AzureRMTrafficManagerProfile(AzureRMModuleBase):

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
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
                default='global'
            ),
            profile_status=dict(
                type='str',
                default='enabled',
                choices=['enabled', 'disabled']
            ),
            routing_method=dict(
                type='str',
                default='performance',
                choices=['performance', 'priority', 'weighted', 'geographic']
            ),
            dns_config=dict(
                type='dict',
                options=dns_config_spec
            ),
            monitor_config=dict(
                type='dict',
                default=dict(
                    protocol='HTTP',
                    port=80,
                    path='/'
                ),
                options=monitor_config_spec
            ),
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.tags = None
        self.location = None
        self.profile_status = None
        self.routing_method = None
        self.dns_config = None
        self.monitor_config = None
        self.endpoints_copy = None

        self.results = dict(
            changed=False
        )

        super(AzureRMTrafficManagerProfile, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                           supports_check_mode=True,
                                                           supports_tags=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        to_be_updated = False

        if not self.dns_config:
            self.dns_config = dict(
                relative_name=self.name,
                ttl=60
            )

        if not self.location:
            self.location = 'global'

        response = self.get_traffic_manager_profile()

        if self.state == 'present':
            if not response:
                to_be_updated = True
            else:
                self.results = shorten_traffic_manager_dict(response)
                self.log('Results : {0}'.format(response))
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if update_tags:
                    to_be_updated = True

                to_be_updated = to_be_updated or self.check_update(response)

            if to_be_updated:
                self.log("Need to Create / Update the Traffic Manager profile")

                if not self.check_mode:
                    self.results = shorten_traffic_manager_dict(self.create_update_traffic_manager_profile())
                    self.log("Creation / Update done.")

                self.results['changed'] = True
                return self.results

        elif self.state == 'absent' and response:
            self.log("Need to delete the Traffic Manager profile")
            self.results = shorten_traffic_manager_dict(response)
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_traffic_manager_profile()

            self.log("Traffic Manager profile deleted")

        return self.results

    def get_traffic_manager_profile(self):
        '''
        Gets the properties of the specified Traffic Manager profile

        :return: deserialized Traffic Manager profile dict
        '''
        self.log("Checking if Traffic Manager profile {0} is present".format(self.name))
        try:
            response = self.traffic_manager_management_client.profiles.get(self.resource_group, self.name)
            self.log("Response : {0}".format(response))
            self.log("Traffic Manager profile : {0} found".format(response.name))
            self.endpoints_copy = response.endpoints if response and response.endpoints else None
            return traffic_manager_profile_to_dict(response)
        except CloudError:
            self.log('Did not find the Traffic Manager profile.')
            return False

    def delete_traffic_manager_profile(self):
        '''
        Deletes the specified Traffic Manager profile in the specified subscription and resource group.
        :return: True
        '''

        self.log("Deleting the Traffic Manager profile {0}".format(self.name))
        try:
            operation_result = self.traffic_manager_management_client.profiles.delete(self.resource_group, self.name)
            return True
        except CloudError as e:
            self.log('Error attempting to delete the Traffic Manager profile.')
            self.fail("Error deleting the Traffic Manager profile: {0}".format(e.message))
            return False

    def create_update_traffic_manager_profile(self):
        '''
        Creates or updates a Traffic Manager profile.

        :return: deserialized Traffic Manager profile state dictionary
        '''
        self.log("Creating / Updating the Traffic Manager profile {0}".format(self.name))

        parameters = Profile(
            tags=self.tags,
            location=self.location,
            profile_status=self.profile_status,
            traffic_routing_method=self.routing_method,
            dns_config=create_dns_config_instance(self.dns_config) if self.dns_config else None,
            monitor_config=create_monitor_config_instance(self.monitor_config) if self.monitor_config else None,
            endpoints=self.endpoints_copy
        )
        try:
            response = self.traffic_manager_management_client.profiles.create_or_update(self.resource_group, self.name, parameters)
            return traffic_manager_profile_to_dict(response)
        except CloudError as exc:
            self.log('Error attempting to create the Traffic Manager.')
            self.fail("Error creating the Traffic Manager: {0}".format(exc.message))

    def check_update(self, response):
        if self.location and normalize_location_name(response['location']) != normalize_location_name(self.location):
            self.log("Location Diff - Origin {0} / Update {1}".format(response['location'], self.location))
            return True

        if self.profile_status and response['profile_status'].lower() != self.profile_status:
            self.log("Profile Status Diff - Origin {0} / Update {1}".format(response['profile_status'], self.profile_status))
            return True

        if self.routing_method and response['routing_method'].lower() != self.routing_method:
            self.log("Traffic Routing Method Diff - Origin {0} / Update {1}".format(response['routing_method'], self.routing_method))
            return True

        if self.dns_config and \
           (response['dns_config']['relative_name'] != self.dns_config['relative_name'] or response['dns_config']['ttl'] != self.dns_config['ttl']):
            self.log("DNS Config Diff - Origin {0} / Update {1}".format(response['dns_config'], self.dns_config))
            return True

        for k, v in self.monitor_config.items():
            if v:
                if str(v).lower() != str(response['monitor_config'][k]).lower():
                    self.log("Monitor Config Diff - Origin {0} / Update {1}".format(response['monitor_config'], self.monitor_config))
                    return True
        return False


def main():
    """Main execution"""
    AzureRMTrafficManagerProfile()


if __name__ == '__main__':
    main()
