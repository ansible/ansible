#!/usr/bin/python
#
# Copyright (c) 2019 Fan Qiu, <fanqiu@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_eventhubconsumergroup
version_added: "2.9"
short_description: Create, update and delete consumergroup for event hub
description:
    - Create, update and delete consumergroup for event hub.

options:
    resource_group:
        description:
            - The resource group to search for the desired eventhub.
        type: str
        required: true
    namespace:
        description:
            - Name of the eventhub namespace.
        type: str
        required: true
    eventhub:
        description:
            - Name of the event hub.
        type: str
        required: true
    consumer_group:
        description:
            - Name of the consumer group.
        type: str
        required: true
    state:
        description:
            - State of the eventhub consumer group. Use C(present) to create or update an eventhub consumer group and C(absent) to delete it.
        type: str
        default: present
        choices:
            - absent
            - present
    user_metadata:
        description:
            - A placeholder to store user-defined string data with maximum length 1024.
            - It can be used to store descriptive data.
            - Such as list of teams and their contact information also user-defined configuration settings can be stored.
        type: str

extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
    - name: Create a consumer group for an event hub
      azure_rm_eventhubconsumergroup:
        resource_group: myResourceGroup
        namespace: testingnamespace
        eventhub: testing
        consumer_group: myGroup
    - name: Update a consumer group for an event hub
      azure_rm_eventhubconsumergroup:
        resource_group: myResourceGroup
        namespace: testingnamespace
        eventhub: testing
        consumer_group: myGroup
        user_metadata: This_is_a_test
    - name: Delete a consumer group for an event hub
      azure_rm_eventhubconsumergroup:
        resource_group: myResourceGroup
        namespace: testingnamespace
        eventhub: testing
        consumer_group: myGroup
        state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID of the consumer group.
    returned: when I(state=present)
    type: str
    sample:
        - "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup
          /providers/Microsoft.EventHub/namespaces/testingnamespace/eventhubs/testing/consumergroups/myGroup"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHubConsumerGroup(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            namespace=dict(
                type='str',
                required=True
            ),
            eventhub=dict(
                type='str',
                required=True
            ),
            consumer_group=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            user_metadata=dict(
                tyep='str'
            )
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.resource_group = None
        self.namespace = None
        self.eventhub = None
        self.consumer_group = None
        self.state = None
        self.user_metadata = None

        super(AzureRMEventHubConsumerGroup, self).__init__(self.module_arg_spec, supports_check_mode=True, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False
        results = None

        consumer_group = self.get_consumer_group()
        if self.state == 'present':
            if not consumer_group:
                changed = True
                self.log('Creating a consumer group')
                if not self.check_mode:
                    consumer_group = self.create_or_update_consumer_group()
            else:
                # Compare user_metadata
                if self.user_metadata and self.user_metadata != consumer_group.user_metadata:
                    changed = True

                if changed and not self.check_mode:
                    consumer_group = self.create_or_update_consumer_group()
            results = consumer_group.as_dict()['id'] if consumer_group else None
        elif consumer_group:
            changed = True
            if not self.check_mode:
                self.delete_consumer_group()

        self.results['changed'] = changed
        self.results['id'] = results
        return self.results

    def get_consumer_group(self):
        try:
            self.log('Gather facts for a consumer group')
            return self.eventhub_client.consumer_groups.get(resource_group_name=self.resource_group,
                                                            namespace_name=self.namespace,
                                                            event_hub_name=self.eventhub,
                                                            consumer_group_name=self.consumer_group)
        except Exception as exc:
            pass
            return None

    def create_or_update_consumer_group(self):
        try:
            self.log('Create or update a consumer group')
            return self.eventhub_client.consumer_groups.create_or_update(resource_group_name=self.resource_group,
                                                                         namespace_name=self.namespace,
                                                                         event_hub_name=self.eventhub,
                                                                         consumer_group_name=self.consumer_group,
                                                                         user_metadata=self.user_metadata)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error creating or updating consumer group{0}: {1}'.format(self.consumer_group, str(exc.inner_exception) or exc.message or str(exc)))

    def delete_consumer_group(self):
        try:
            self.log('Delete a consumer group')
            return self.eventhub_client.consumer_groups.delete(resource_group_name=self.resource_group,
                                                               namespace_name=self.namespace,
                                                               event_hub_name=self.eventhub,
                                                               consumer_group_name=self.consumer_group)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error deleting consumer group{0}: {1}'.format(self.consumer_group, str(exc.inner_exception) or exc.message or str(exc)))


def main():
    AzureRMEventHubConsumerGroup()


if __name__ == '__main__':
    main()
