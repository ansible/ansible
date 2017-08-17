#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_trafficmanager
version_added: "2.1"
short_description: Manage Azure Traffic Manager (profile).
description:
    - Create, update and delete a traffic manager profile.
options:
    name:
        description:
            - Remove a resource group and all associated resources. Use with state 'absent' to delete a resource
              group that contains resources.
        default: false
        required: false
    location:
        description:
            - Azure location for the resource group. Required when creating a new resource group. Cannot
              be changed once resource group is created.
        required: false
        default: null
    name:
        description:
            - Name of the resource group.
        required: true
    state:
        description:
            - Assert the state of the resource group. Use 'present' to create or update and
              'absent' to delete. When 'absent' a resource group containing resources will not be removed unless the
              force option is used.
        default: present
        choices:
            - absent
            - present
        required: false
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Create a resource group
      azure_rm_trafficmanagerprofile:
        name: "Testing"
        resource_group: "rg"
        properties:
            profileStatus: Testing
            trafficRoutingMethod: westus
            dnsConfig:
                relativeName: testing
                ttl: never
            monitorConfig:
                protocol: "HTTP" 
                path: "/testpath.aspx"
            endpoits:
                - id
                - id
        location: "global"
        tags: 
                - tag1
                - tag2
        status: "Enabled"


    - name: Delete a resource group
      azure_rm_resourcegroup:
        name: Testing
        state: absent
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
    from azure.mgmt.trafficmanager.models import DnsConfig, Profile, MonitorConfig
except ImportError:
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def trafficmanagerprofile_group_to_dict(tm):
    return dict(
        id=tm.id,
        name=tm.name,
        resource_group=tm.resource_group,
        location=tm.location,
        tags=tm.tags,
    )


class AzureRMTrafficManager(AzureRMModuleBase):

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
            state=dict(),
        )

        super(AzureRMTrafficManager, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        # Collect all the tags and add them to the attributes
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # Get resource group using Azure Python SDK
        resource_group = self.get_resource_group(self.resource_group)

        # Initialize the Ansible return
        results = dict()
        changed = False
        traffic_manager = None
        # contains_endpoints = False


        try:
            self.log('Fetching traffic manager {0}'.format(self.name))
            # Get the resource group to verify it exist
            # traffic_manager = self.get_traffic_manager_profile(self.resource_group, self.name)
            self.create_or_update_traffic_manager_profile(self.resource_group, self.name,
                                                          self.location, self.properties)
            changed = True
            #Retrieve the sate of the tm
            # self.check_provisioning_state(tm, self.state)
            # contains_resources = self.resources_exist()

            # results = resource_group_to_dict(self.resource_group)
            # if self.state == 'absent':
            #     changed = True
            # elif self.state == 'present':
            #     update_tags, results['tags'] = self.update_tags(results['tags'])
            #     if update_tags:
            #         changed = True

            #     if self.location and self.location != results['location']:
            #         self.fail("traffic manager '{0}' already exists in location '{1}' and cannot be "
            #                   "moved.".format(self.name, results['location']))
        except CloudError:
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        # if changed:
        #     if self.state == 'present':
        #         if not rg:
        #             # Create resource group
        #             self.log("Creating resource group {0}".format(self.name))
        #             if not self.location:
        #                 self.fail("Parameter error: location is required when creating a resource group.")
        #             if self.name_exists():
        #                 self.fail("Error: a resource group with the name {0} already exists in your subscription."
        #                           .format(self.name))
        #             params = ResourceGroup(
        #                 location=self.location,
        #                 tags=self.tags
        #             )
        #         else:
        #             # Update resource group
        #             params = ResourceGroup(
        #                 location=results['location'],
        #                 tags=results['tags']
        #             )
        #         self.results['state'] = self.create_or_update_resource_group(params)
        #     elif self.state == 'absent':
        #         if contains_resources and not self.force:
        #             self.fail("Error removing resource group {0}. Resources exist within the group.".format(self.name))
        #         self.delete_resource_group()

        return self.results

    # def create_or_update_resource_group(self, params):
    #     try:
    #         result = self.rm_client.resource_groups.create_or_update(self.name, params)
    #     except Exception as exc:
    #         self.fail("Error creating or updating resource group {0} - {1}".format(self.name, str(exc)))
    #     return resource_group_to_dict(result)

    # def delete_resource_group(self):
    #     try:
    #         poller = self.rm_client.resource_groups.delete(self.name)
    #         self.get_poller_result(poller)
    #     except Exception as exc:
    #         self.fail("Error delete resource group {0} - {1}".format(self.name, str(exc)))

    #     # The delete operation doesn't return anything.
    #     # If we got here, assume all is good
    #     self.results['state']['status'] = 'Deleted'
    #     return True


    # def trafficmanagerprofile_exist(self):
    #     found = False
    #     try:
    #         response = self.trafficmanager_client.list_by_resource_group(self.resource_group)
    #     except Exception as exc:
    #         self.fail("Error checking for resource existence in {0} - {1}".format(self.name, str(exc)))

    #     for item in response:
    #         found = True
    #         break
    #     return found

    # def name_exists(self):
    #     try:
    #         exists = self.rm_client.resource_groups.check_existence(self.name)
    #     except Exception as exc:
    #         self.fail("Error checking for existence of name {0} - {1}".format(self.name, str(exc)))
    #     return exists

    def get_traffic_manager_profile(self, resource_group, name):
        '''
        Fetch a traffic manager profile.

        :param name: name of a traffic  manager
        :return: traffic manage object
        '''
        try:
            profiles = self.trafficmanager_client.profile.list_by_resource_group(resource_group)
           
            #  Check the profiles and return the one that matches the name
            for profile in profiles:
                if profile is name:
                    return self.trafficmanager_client.profiles.get(resource_group, name)
            return None  # if there is no profile returns None
        except CloudError as ce:
            self.fail("Error getting traffic manager profile with nanme: {0}.  {1}".format(name, ce))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(name, str(exc)))


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


        #MonitorConfig
        monitor_properties = properties.get('monitor_config', None)
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

        #DnsConfig
        dns_config_properties = properties.get('dns_config', None)
        relative_name = dns_config_properties.get('relative_name', None)
        ttl = dns_config_properties.get('ttl', None)
        dns_config = DnsConfig(relative_name, ttl)

        profile = Profile(tags, location, profile_status, traffic_routing_method,
                          dns_config, monitor_config, endpoints)
       
        try:
            return self.trafficmanager_client.profiles.create_or_update(resource_group, name, profile)
        except CloudError as cloudError:
            self.fail("Error creating or updating traffic manager profile with name {0}.  {1}"
                      .format(name, cloudError))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(name, str(exc)))
        


def main():
    AzureRMTrafficManager()

if __name__ == '__main__':
    main()
