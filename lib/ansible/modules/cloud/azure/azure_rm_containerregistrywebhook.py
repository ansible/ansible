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
module: azure_rm_containerregistrywebhook
version_added: "2.5"
short_description: Manage Webhook instance.
description:
    - Create, update and delete instance of Webhook.

options:
    resource_group:
        description:
            - The name of the resource group to which the container registry belongs.
        required: True
    registry_name:
        description:
            - The name of the container registry.
        required: True
    webhook_name:
        description:
            - The name of the webhook.
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    service_uri:
        description:
            - The service URI for the webhook to post notifications.
    custom_headers:
        description:
            - Custom headers that will be added to the webhook notifications.
    status:
        description:
            - The status of the webhook at the time the operation was called.
        choices:
            - 'enabled'
            - 'disabled'
    scope:
        description:
            - "The scope of repositories where the event can be triggered. For example, 'foo:*' means events for all tags under repository 'foo'. 'foo:bar' m
              eans events for 'foo:bar' only. 'foo' is equivalent to 'foo:latest'. Empty means all events."
    actions:
        description:
            - The list of actions that trigger the webhook to post notifications.
        type: list

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) Webhook
    azure_rm_containerregistrywebhook:
      resource_group: myResourceGroup
      registry_name: myRegistry
      webhook_name: myWebhook
      location: eastus
'''

RETURN = '''
id:
    description:
        - The resource ID.
    returned: always
    type: str
    sample: "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.ContainerRegistry/registries/myRegistry/w
            ebhooks/myWebhook"
status:
    description:
        - "The status of the webhook at the time the operation was called. Possible values include: 'enabled', 'disabled'"
    returned: always
    type: str
    sample: enabled
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMWebhooks(AzureRMModuleBase):
    """Configuration class for an Azure RM Webhook resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            registry_name=dict(
                type='str',
                required=True
            ),
            webhook_name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            service_uri=dict(
                type='str'
            ),
            custom_headers=dict(
                type='dict'
            ),
            status=dict(
                type='str',
                choices=['enabled',
                         'disabled']
            ),
            scope=dict(
                type='str'
            ),
            actions=dict(
                type='list'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.registry_name = None
        self.webhook_name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMWebhooks, self).__init__(derived_arg_spec=self.module_arg_spec,
                                              supports_check_mode=True,
                                              supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "service_uri":
                    self.parameters["service_uri"] = kwargs[key]
                elif key == "custom_headers":
                    self.parameters["custom_headers"] = kwargs[key]
                elif key == "status":
                    self.parameters["status"] = kwargs[key]
                elif key == "scope":
                    self.parameters["scope"] = kwargs[key]
                elif key == "actions":
                    self.parameters["actions"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(ContainerRegistryManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        old_response = self.get_webhook()

        if not old_response:
            self.log("Webhook instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Webhook instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Webhook instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Webhook instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_webhook()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Webhook instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_webhook()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_webhook():
                time.sleep(20)
        else:
            self.log("Webhook instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]
            self.results["status"] = response["status"]

        return self.results

    def create_update_webhook(self):
        '''
        Creates or updates Webhook with the specified configuration.

        :return: deserialized Webhook instance state dictionary
        '''
        self.log("Creating / Updating the Webhook instance {0}".format(self.webhook_name))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.webhooks.create(resource_group_name=self.resource_group,
                                                            registry_name=self.registry_name,
                                                            webhook_name=self.webhook_name,
                                                            webhook_create_parameters=self.parameters)
            else:
                response = self.mgmt_client.webhooks.update(resource_group_name=self.resource_group,
                                                            registry_name=self.registry_name,
                                                            webhook_name=self.webhook_name,
                                                            webhook_update_parameters=self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Webhook instance.')
            self.fail("Error creating the Webhook instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_webhook(self):
        '''
        Deletes specified Webhook instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Webhook instance {0}".format(self.webhook_name))
        try:
            response = self.mgmt_client.webhooks.delete(resource_group_name=self.resource_group,
                                                        registry_name=self.registry_name,
                                                        webhook_name=self.webhook_name)
        except CloudError as e:
            self.log('Error attempting to delete the Webhook instance.')
            self.fail("Error deleting the Webhook instance: {0}".format(str(e)))

        return True

    def get_webhook(self):
        '''
        Gets the properties of the specified Webhook.

        :return: deserialized Webhook instance state dictionary
        '''
        self.log("Checking if the Webhook instance {0} is present".format(self.webhook_name))
        found = False
        try:
            response = self.mgmt_client.webhooks.get(resource_group_name=self.resource_group,
                                                     registry_name=self.registry_name,
                                                     webhook_name=self.webhook_name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Webhook instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Webhook instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMWebhooks()

if __name__ == '__main__':
    main()
