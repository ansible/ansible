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
module: azure_rm_containerregistrywebhook_facts
version_added: "2.5"
short_description: Get Webhook facts.
description:
    - Get facts of Webhook.

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

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Webhook
    azure_rm_containerregistrywebhook_facts:
      resource_group: resource_group_name
      registry_name: registry_name
      webhook_name: webhook_name
'''

RETURN = '''
webhooks:
    description: A list of dict results where the key is the name of the Webhook and the values are the facts for that Webhook.
    returned: always
    type: complex
    contains:
        webhook_name:
            description: The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - The resource ID.
                    returned: always
                    type: str
                    sample: "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.ContainerRegistry/registr
                            ies/myRegistry/webhooks/myWebhook"
                name:
                    description:
                        - The name of the resource.
                    returned: always
                    type: str
                    sample: myWebhook
                type:
                    description:
                        - The type of the resource.
                    returned: always
                    type: str
                    sample: Microsoft.ContainerRegistry/registries/webhooks
                location:
                    description:
                        - The location of the resource. This cannot be changed after the resource is created.
                    returned: always
                    type: str
                    sample: westus
                status:
                    description:
                        - "The status of the webhook at the time the operation was called. Possible values include: 'enabled', 'disabled'"
                    returned: always
                    type: str
                    sample: enabled
                scope:
                    description:
                        - "The scope of repositories where the event can be triggered. For example, 'foo:*' means events for all tags under repository 'foo'.
                           'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to 'foo:latest'. Empty means all events."
                    returned:
                    type: str
                    sample: myRepository
                actions:
                    description:
                        - The list of actions that trigger the webhook to post notifications.
                    returned: always
                    type: str
                    sample: "[\n\n  'push'\n\n]"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMWebhooksFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
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
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict()
        )
        self.mgmt_client = None
        self.resource_group = None
        self.registry_name = None
        self.webhook_name = None
        super(AzureRMWebhooksFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(ContainerRegistryManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.registry_name is not None and
                self.webhook_name is not None):
            self.results['webhooks'] = self.get()
        return self.results

    def get(self):
        '''
        Gets facts of the specified Webhook.

        :return: deserialized Webhookinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.webhooks.get(resource_group_name=self.resource_group,
                                                     registry_name=self.registry_name,
                                                     webhook_name=self.webhook_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Webhooks.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results


def main():
    AzureRMWebhooksFacts()
if __name__ == '__main__':
    main()
