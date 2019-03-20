#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_applicationsecuritygroup
version_added: "2.8"
short_description: Manage Azure Application Security Group.
description:
    - Create, update and delete instance of Azure Application Security Group.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the application security group.
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    state:
      description:
        - Assert the state of the Application Security Group.
        - Use C(present) to create or update an Application Security Group and C(absent) to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yunge Zhu (@yungezz)"

'''

EXAMPLES = '''
  - name: Create application security group
    azure_rm_applicationsecuritygroup:
      resource_group: myResourceGroup
      name: mySecurityGroup
      location: eastus
      tags:
        foo: bar
'''

RETURN = '''
id:
    description:
        - Resource id of the application security group.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/applicationSecurityGroups/
             mySecurityGroup"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, CreateOrUpdate, Delete = range(3)


class AzureRMApplicationSecurityGroup(AzureRMModuleBase):
    """Configuration class for an Azure RM Application Security Group resource"""

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
            location=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.location = None
        self.name = None
        self.tags = None

        self.state = None

        self.results = dict(changed=False)

        self.to_do = Actions.NoAction

        super(AzureRMApplicationSecurityGroup, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                              supports_check_mode=True,
                                                              supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        resource_group = self.get_resource_group(self.resource_group)

        if not self.location:
            self.location = resource_group.location

        old_response = self.get_applicationsecuritygroup()

        if not old_response:
            self.log("Application Security Group instance doesn't exist")
            if self.state == 'present':
                self.to_do = Actions.CreateOrUpdate
            else:
                self.log("Old instance didn't exist")
        else:
            self.log("Application Security Group instance already exists")
            if self.state == 'present':
                if self.check_update(old_response):
                    self.to_do = Actions.CreateOrUpdate

                update_tags, self.tags = self.update_tags(old_response.get('tags', None))
                if update_tags:
                    self.to_do = Actions.CreateOrUpdate

            elif self.state == 'absent':
                self.to_do = Actions.Delete

        if self.to_do == Actions.CreateOrUpdate:
            self.log("Need to Create / Update the Application Security Group instance")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            response = self.create_update_applicationsecuritygroup()
            self.results['id'] = response['id']

        elif self.to_do == Actions.Delete:
            self.log("Delete Application Security Group instance")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_applicationsecuritygroup()

        return self.results

    def check_update(self, existing_asg):
        if self.location and self.location.lower() != existing_asg['location'].lower():
            self.module.warn("location cannot be updated. Existing {0}, input {1}".format(existing_asg['location'], self.location))
        return False

    def create_update_applicationsecuritygroup(self):
        '''
        Create or update Application Security Group.

        :return: deserialized Application Security Group instance state dictionary
        '''
        self.log("Creating / Updating the Application Security Group instance {0}".format(self.name))

        param = dict(name=self.name,
                     tags=self.tags,
                     location=self.location)
        try:
            response = self.network_client.application_security_groups.create_or_update(resource_group_name=self.resource_group,
                                                                                        application_security_group_name=self.name,
                                                                                        parameters=param)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error creating/updating Application Security Group instance.')
            self.fail("Error creating/updating Application Security Group instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_applicationsecuritygroup(self):
        '''
        Deletes specified Application Security Group instance.

        :return: True
        '''
        self.log("Deleting the Application Security Group instance {0}".format(self.name))
        try:
            response = self.network_client.application_security_groups.delete(resource_group_name=self.resource_group,
                                                                              application_security_group_name=self.name)
        except CloudError as e:
            self.log('Error deleting the Application Security Group instance.')
            self.fail("Error deleting the Application Security Group instance: {0}".format(str(e)))

        return True

    def get_applicationsecuritygroup(self):
        '''
        Gets the properties of the specified Application Security Group.

        :return: deserialized Application Security Group instance state dictionary
        '''
        self.log("Checking if the Application Security Group instance {0} is present".format(self.name))
        found = False
        try:
            response = self.network_client.application_security_groups.get(resource_group_name=self.resource_group,
                                                                           application_security_group_name=self.name)
            self.log("Response : {0}".format(response))
            self.log("Application Security Group instance : {0} found".format(response.name))
            return response.as_dict()
        except CloudError as e:
            self.log('Did not find the Application Security Group instance.')
        return False


def main():
    """Main execution"""
    AzureRMApplicationSecurityGroup()


if __name__ == '__main__':
    main()
