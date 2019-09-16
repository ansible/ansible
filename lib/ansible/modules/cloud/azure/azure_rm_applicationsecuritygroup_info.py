#!/usr/bin/python
#
# Copyright (c) 2019 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_applicationsecuritygroup_info
version_added: "2.9"
short_description: Get Azure Application Security Group facts
description:
    - Get facts of Azure Application Security Group.

options:
    resource_group:
        description:
            - The name of the resource group.
    name:
        description:
            - The name of the application security group.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Yunge Zhu (@yungezz)

'''

EXAMPLES = '''
  - name: List application security groups in specific resource group
    azure_rm_applicationsecuritygroup_info:
      resource_group: myResourceGroup

  - name: List application security groups in specific subscription
    azure_rm_applicationsecuritygroup_info:

  - name: Get application security group by name
    azure_rm_applicationsecuritygroup_info:
        resource_group: myResourceGroup
        name: myApplicationSecurityGroup
        tags:
            - foo
'''

RETURN = '''
applicationsecuritygroups:
    description:
        - List of application security groups.
    returned: always
    type: complex
    contains:
        id:
            description: Id of the application security group.
            type: str
            returned: always
            sample:
                "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/applicationSecurityGroups/MyAsg"
        location:
            description:
                - Location of the application security group.
            type: str
            returned: always
            sample: eastus
        name:
            description:
                - Name of the resource.
            type: str
            returned: always
            sample: myAsg
        provisioning_state:
            description:
                - Provisioning state of application security group.
            type: str
            returned: always
            sample: Succeeded
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
except ImportError:
    # This is handled in azure_rm_common
    pass


def applicationsecuritygroup_to_dict(asg):
    return dict(
        id=asg.id,
        location=asg.location,
        name=asg.name,
        tags=asg.tags,
        provisioning_state=asg.provisioning_state
    )


class AzureRMApplicationSecurityGroupInfo(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            ),
            tags=dict(type='list')
        )

        self.resource_group = None
        self.name = None
        self.tags = None

        self.results = dict(changed=False)

        super(AzureRMApplicationSecurityGroupInfo, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                                  supports_check_mode=False,
                                                                  supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        is_old_facts = self.module._name == 'azure_rm_applicationsecuritygroup_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_applicationsecuritygroup_facts' module has been renamed to 'azure_rm_applicationsecuritygroup_info'",
                                  version='2.13')

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        if self.name:
            if self.resource_group:
                self.results['applicationsecuritygroups'] = self.get()
            else:
                self.fail("resource_group is required when filtering by name")
        elif self.resource_group:
            self.results['applicationsecuritygroups'] = self.list_by_resource_group()
        else:
            self.results['applicationsecuritygroups'] = self.list_all()

        return self.results

    def get(self):
        '''
        Gets the properties of the specified Application Security Group.

        :return: deserialized Application Security Group instance state dictionary
        '''
        self.log("Get the Application Security Group instance {0}".format(self.name))

        results = []
        try:
            response = self.network_client.application_security_groups.get(resource_group_name=self.resource_group,
                                                                           application_security_group_name=self.name)
            self.log("Response : {0}".format(response))

            if response and self.has_tags(response.tags, self.tags):
                results.append(applicationsecuritygroup_to_dict(response))
        except CloudError as e:
            self.fail('Did not find the Application Security Group instance.')
        return results

    def list_by_resource_group(self):
        '''
        Lists the properties of Application Security Groups in specific resource group.

        :return: deserialized Application Security Group instance state dictionary
        '''
        self.log("Get the Application Security Groups in resource group {0}".format(self.resource_group))

        results = []
        try:
            response = list(self.network_client.application_security_groups.list(resource_group_name=self.resource_group))
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(applicationsecuritygroup_to_dict(item))
        except CloudError as e:
            self.log('Did not find the Application Security Group instance.')
        return results

    def list_all(self):
        '''
        Lists the properties of Application Security Groups in specific subscription.

        :return: deserialized Application Security Group instance state dictionary
        '''
        self.log("Get the Application Security Groups in current subscription")

        results = []
        try:
            response = list(self.network_client.application_security_groups.list_all())
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(applicationsecuritygroup_to_dict(item))
        except CloudError as e:
            self.log('Did not find the Application Security Group instance.')
        return results


def main():
    """Main execution"""
    AzureRMApplicationSecurityGroupInfo()


if __name__ == '__main__':
    main()
