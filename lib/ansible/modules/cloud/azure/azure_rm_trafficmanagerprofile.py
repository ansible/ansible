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
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_trafficmanager
version_added: "2.4"
short_description: Manage Azure Traffic Manager (profile).
description:
    - Create, update and delete a traffic manager profile.
options:

    name:
        description:
             - The name of the Traffic Manager profile.
        default: false
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
    traffic_routing_method:
        description:
            - The traffic routing method of the Traffic Manager profile. Possible
            values include: 'Performance', 'Priority', 'Weighted', 'Geographic'.
    dns_config:
        description:
            - The DNS settings of the Traffic Manager profile. This section includes
            relative_name and ttl.
        required: true
        suboptions:
            ttl:
                description:
                    - The DNS Time-To-Live (TTL), in seconds. This informs the
                    local DNS resolvers and DNS clients how long to cache DNS
                    responses provided by this Traffic Manager profile.
    monitor_config:
        description:
            - The endpoint monitoring settings of the Traffic Manager profile.
        required: true
    suboptions:
        status:
            description:
                - The profile-level monitoring status of the Traffic Manager profile.
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
                - The monitor interval for endpoints in this profile. This is the interval
                at which Traffic Manager will check the health of each endpoint in this profile.
        timeout_in_seconds:
            description:
                - The monitor timeout for endpoints in this profile. This is the time that
                Traffic Manager allows endpoints in this profile to response to the health check.
        tolerated_number_of_failures:
            description:
                - The number of consecutive failed health check that Traffic Manager tolerates
                before declaring an endpoint in this profile Degraded after the next failed health check.
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
      azure_rm_trafficmanagerprofile:
        name: "contoso.com"
        state: "present"
        resource_group: "ContosoRG"
        properties:
          profile_status: "Enabled"
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
          location: "global"
          tags:
            project: "My Project"

    - name: Delete a Traffic Manager Profile
      azure_rm_trafficmanagerprofile:
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
    from azure.mgmt.trafficmanager.models import DnsConfig, Profile, MonitorConfig, Endpoint
except ImportError:
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def trafficmanagerprofile_group_to_dict(tm):
    return dict(
        id=tm.id,
        name=tm.name,
        resource_group=tm.resource_group,
        location=tm.location,
        tags=tm.tags)


class AzureRMTrafficManager(AzureRMModuleBase):
    # Main Traffic Manager class

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(type='str', required=True),
            resource_group=dict(type='str', required=True),
            properties=dict(type='dict'),
            location=dict(type='str'),
            status=dict(type='str', default='Enabled', choices=['Enabled', 'Disabled']),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        self.name = None
        self.resource_group = None
        self.properties = None
        self.location = None
        self.status = None
        self.state = None

        self.results = dict(
            changed=False,
            contains_endpoints=False,
            state=dict())

        super(AzureRMTrafficManager, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        # Collect all the tags and add them to the attributes
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # Before we proceed, verify that the resource group exists.
        try:
            self.get_resource_group(self.resource_group)

        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))

        # Initialize the Ansible return
        results = dict()
        changed = False
        current_traffic_manager = self.get_traffic_manager_profile(
            self.resource_group,
            self.name)

        results = self.traffic_manager_to_dict(
            current_traffic_manager,
            self.resource_group,
            self.name, self.location,
            self.properties)

        try:
            if self.state == 'present':
                self.log('Fetching traffic manager {0}'.format(self.name))
                # dry-run.
                if self.check_mode:
                    # if the current_traffic_manager is empty it means we will
                    # create a new profile. Return a profile object to the user
                    if not bool(current_traffic_manager):
                        self.results['state'] = results
                    # if the profile exists, compare and report back the differences
                    else:
                        self.results['state'] = self.compare_profiles(
                            current_traffic_manager,
                            self.properties)
                    return self.results

                # Not in check_mode. This will create the profile.
                else:
                    if not bool(current_traffic_manager):
                        # profile doesn't exist. We will created it.
                        # Traffic Manager uses DNS, we need to check if the
                        # name used in the DNS prefix is available
                        try:
                            dns_available = dict()
                            dns_available = self.trafficmanager_client.profiles.check_traffic_manager_relative_dns_name_availability(
                                self.name, 'Microsoft.Network/trafficManagerProfiles')
                            if bool(dns_available.name_available):
                                pass

                        except CloudError as cloud_error:
                            self.fail('Error checking the traffic manager DNS: {0}. {1}'.format(self.name, str(cloud_error)))

                        traffic_manager = self.create_or_update_traffic_manager_profile(
                            self.resource_group,
                            self.name,
                            self.location,
                            self.properties)

                    results = self.traffic_manager_to_dict(
                        traffic_manager,
                        self.resource_group,
                        self.name,
                        self.location,
                        self.properties
                    )
                    changed = True

            elif self.state == 'absent':
                self.log('Deleting traffic manager {0}'.format(self.name))
                # dry-run. report back to the user.
                if self.check_mode:
                    self.results['state'] = dict(
                        resouce_group=self.resource_group,
                        name=self.name)
                    return self.results
                if bool(current_traffic_manager):
                    # Deletes the traffic manager and set change variable
                    self.remove_traffic_manager_profile(
                        self.resource_group,
                        self.name)
                    changed = True
        except CloudError:
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        return self.results

    def compare_profiles(self, profile, properties):
        """Compare profiles"""

        result = dict(
            dns_config=dict(ttl=None),
            monitor_config=dict(
                interval_in_seconds=None,
                path=None,
                port=None,
                protocol=None,
                status=None,
                timeout_in_seconds=None,
                tolerated_number_of_failures=None
            ),
            profile_status=None,
            traffic_routing_method=None
        )

        azure_profile = dict()

        # Check to see if the profile properties have changed
        if azure_profile.get('profile_status') != properties.get('profile_status'):
            result['profile_status'] = properties.get('profile_status')

        if azure_profile.get('dns_config', {}).get('ttl') != properties.get('dns_config', {}).get('ttl'):
            result['dns_config']['ttl'] = properties.get('dns_config', {}).get('ttl')

        monitor_config_list = [
            'interval_in_seconds',
            'path',
            'port',
            'protocol',
            'status',
            'timeout_in_seconds',
            'tolerated_number_of_failures']
        for item in monitor_config_list:
            if azure_profile.get('monitor_config', {}).get(item) != properties.get('monitor_config', {}).get(item):
                if bool(properties.get('monitor_config', {}).get(item)):
                    result['monitor_config'][item] = properties.get('monitor_config', {}).get(item)

        return result

    def traffic_manager_to_dict(self, traffic_manager, resource_group, name, location, properties):
        '''
        Converts a traffic manager profile to a dictionary

        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        if not bool(traffic_manager):  # Create a stub if there is no traffic manager
            if bool(properties) and len(properties) > 0:
                monitor_config = properties.get('monitor_config', [])
                dns_config = properties.get('dns_config', [])
                tags = properties.get('tags', [])
            else:
                name = None
                resource_group = None
                dns_config = {}
                monitor_config = {}
                tags = []
                properties = dict(
                    dns_config=dns_config,
                    monitor_config=monitor_config,
                    tags=tags)

            return dict(
                # id=traffic_manager.profile.id,
                name=name,
                resource_group=resource_group,
                location=location,
                properties=properties)

        elif traffic_manager:  # Create a dictionary from the Azure traffic manager
            properties = dict(tags=traffic_manager.tags)
            return dict(
                id=traffic_manager.id,
                name=traffic_manager.name,
                location=traffic_manager.location,
                properties=properties)

    def get_traffic_manager_profile(self, resource_group, name):
        '''
        Fetch a traffic manager profile.

        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        try:
            profiles = self.trafficmanager_client.profiles.list_by_resource_group(resource_group)
            #  Check the profiles and return the one that matches the name
            for profile in profiles:
                if profile.name == name:
                    return self.trafficmanager_client.profiles.get(resource_group, name)
            return None  # if there is no profile returns None
        except CloudError as cloud_error:
            self.fail(
                "Error getting traffic manager profile with nanme: {0}. {1}".format(name, cloud_error))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(name, str(exc)))

    def exist_traffic_manager_profile(self, resource_group, name):
        '''
        Fetch a traffic manager profile.

        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        try:
            profiles = self.trafficmanager_client.profiles.list_by_resource_group(resource_group)

            #  Check the profiles and returns true if exist
            for profile in profiles:
                if profile.name == name:
                    return True
            return False
        except CloudError as cloud_error:
            self.fail(
                "Error getting traffic manager profile with nanme: {0}. {1}".format(name, cloud_error))
        except Exception as exc:
            self.fail(
                "Error retrieving traffic manager {0} - {1}".format(name, str(exc)))

    def remove_traffic_manager_profile(self, resource_group, name):
        '''
        Remove the traffic manager profile.

        :param resource_group:: name of the traffic manager resource group
        :param name: name of a traffic manager profile
        :return: boolean True on successful deletion
        '''
        try:
            self.trafficmanager_client.profiles.delete(resource_group, name)
        except CloudError as cloud_error:
            self.fail(
                "Error getting traffic manager profile with nanme: {0}. {1}".format(name, cloud_error))
        except Exception as exc:
            self.fail(
                "Error retrieving traffic manager {0} - {1}".format(name, str(exc)))

    def create_or_update_traffic_manager_profile(self, resource_group, name, location, properties):
        '''
        Create or update a traffic manager profile.

        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        tags = properties.get('tags', None)
        location = properties.get('location', "global")
        profile_status = properties.get('profile_status', None)
        traffic_routing_method = properties.get('traffic_routing_method', None)
        endpoints = properties.get('endpoints', [])

        # Create MonitorConfig
        monitor_config = self.create_monitor_config(properties)

        # Create DnsConfig
        dns_config = self.create_dns_config(properties, name)

        # Create Endpoints
        endpoints_config = self.create_endpoints(endpoints)

        profile = Profile(
            tags,
            location,
            profile_status,
            traffic_routing_method,
            dns_config,
            monitor_config,
            endpoints_config)

        try:
            return self.trafficmanager_client.profiles.create_or_update(resource_group, name, profile)
        except CloudError as cloud_error:
            self.fail("Error creating or updating traffic manager profile with name {0}. {1}"
                      .format(name, cloud_error))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(name, str(exc)))

    def create_endpoints(self, endpoint_list):
        '''
        Create a dns configuration from properties.

        :param name: name of a traffic  manager
        :return: DnsConfig object
        '''
        endpoint_list_config = []
        for endpoint_properties in endpoint_list:
            target_resource_id = endpoint_properties.get('target_resource_id', None)
            target = endpoint_properties.get('target', None)
            endpoint_status = endpoint_properties.get('endpoint_status', None)
            weight = endpoint_properties.get('weight', None)
            priority = endpoint_properties.get('priority', None)
            endpoint_location = endpoint_properties.get('endpoint_location', None)
            endpoint_monitor_status = endpoint_properties.get('endpoint_monitor_status', None)
            min_child_endpoints = endpoint_properties.get('min_child_endpoints', None)
            geo_mapping = endpoint_properties.get('geo_mapping', None)

            # create an endpoint instance of type endpoint filled with the properties
            endpoint_instance = Endpoint(target_resource_id, target, endpoint_status,
                                         weight, priority, endpoint_location,
                                         endpoint_monitor_status, min_child_endpoints,
                                         geo_mapping)

            endpoint_list_config.append(endpoint_instance)  # add instance to the list

        return endpoint_list_config

    def create_dns_config(self, properties, name):
        '''
        Create a dns configuration from properties.

        :param name: name of a traffic  manager
        :return: DnsConfig object
        '''
        if properties is None:
            properties = {}
        dns_config_properties = properties.get('dns_config', {})
        relative_name = dns_config_properties.get('relative_name', name)
        ttl = dns_config_properties.get('ttl', None)
        dns_config = DnsConfig(relative_name, ttl)
        return dns_config

    def create_monitor_config(self, properties):
        '''
        Create a monitor configuration from properties.

        :param name: name of a traffic  manager
        :return: MonitorConfig object
        '''
        if properties is None:
            properties = {}
        monitor_properties = properties.get('monitor_config', {})
        monitor_protocol = monitor_properties.get('protocol', None)
        monitor_port = monitor_properties.get('port', None)
        monitor_path = monitor_properties.get('path', None)
        monitor_status = monitor_properties.get('status', None)
        monitor_interval_in_seconds = monitor_properties.get('interval_in_seconds', 5)
        monitor_timeout_in_seconds = monitor_properties.get('timeout_in_seconds', None)
        monitor_tolerated_failures = monitor_properties.get('tolerated_number_of_failures', None)
        monitor_config = MonitorConfig(monitor_status, monitor_protocol, monitor_port,
                                       monitor_path, monitor_interval_in_seconds,
                                       monitor_timeout_in_seconds, monitor_tolerated_failures)
        return monitor_config


def main():
    AzureRMTrafficManager()

if __name__ == '__main__':
    main()
