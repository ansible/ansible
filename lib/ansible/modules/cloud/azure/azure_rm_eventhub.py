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
module: azure_rm_eventhub
version_added: "2.9"
short_description: Manage Azure Event hub.
description:
    - Create, update and delete an Azure Event hub.

options:
    resource_group:
        description:
            - Name of a resource group where the Event hub exists or will be created.
        required: true
    name:
        description:
            - Name of the Event hub.
        required: true
    state:
        description:
            - Assert the state of the Event hub. Use C(present) to create or update an event hub and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    namespace:
        description:
            - The Namespace name
        required: true
    message_retention_in_days:
        description:
            - Number of days to retain the events for this Event Hub, value should be 1 to 7 days
    partition_count:
        description:
            - Number of partitions created for the Event Hub, allowed values are from 1 to 32 partitions.
            - Is not changeable after the creation
    status:
        description:
            - Enumerates the possible values for the status of the Event Hub.
        choices:
            - active
            - disabled
            - send_disabled
            - receive_disabled

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
    - name: Create an event hub with default
      azure_rm_eventhub:
        name: Testing
        resource_group: myResourceGroup
        namespace: testingnamespace

    - name: Create an event hub with partition_count
      azure_rm_eventhub:
        name: Testing
        resource_group: myResourceGroup
        namespace: testingnamespace
        partition_count: 8

    - name: Delete the event hub
      azure_rm_eventhub:
        name: Testing
        resource_group: myResourceGroup
        namespace: testingnamespace
        state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID of the event hub.
    returned: state is present
    type: str
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup/providers/Microsoft.EventHub/namespaces/Testing"
name:
    description:
        - Name of the event hub.
    returned: state is present
    type: str
    sample: Testing
message_retention_in_days:
    description:
        - Number of days to retain the events for this Event Hub, value should be 1 to 7 days
    returned: state is present
    type: int
    sample: 7
status:
    description:
        - Enumerates the possible values for the status of the Event Hub.
    returned: state is present
    type: str
    sample: Active
partition_count:
    description:
        - Number of partitions created for the Event Hub, allowed values are from 1 to 32 partitions.
    returned: state is present
    type: str
    sample: 4
partition_ids:
    description:
        - Current number of shards on the Event Hub.
    returned: state is present
    type: list
type:
    description:
        - Resource type
    returned: state is present
    type: str
    sample: "Microsoft.EventHub/Namespaces/EventHubs"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHub(AzureRMModuleBase):
    """Configuration class for an Azure RM Event hub resource"""

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
            namespace=dict(
                type='str',
                required=True
            ),
            message_retention_in_days=dict(
                type='int'
            ),
            partition_count=dict(
                type='int'
            ),
            status=dict(
                type='str',
                choices=['active', 'disabled', 'send_disabled', 'receive_disabled']
            )
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        # TODO: Add support for capture_description
        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
        self.message_retention_in_days = None
        self.partition_count = None
        self.status = None

        super(AzureRMEventHub, self).__init__(self.module_arg_spec, supports_check_mode=True, supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False

        self.status = self.eventhub_models.EntityStatus[self.status] if self.status else None
        event_hub = self.get_event_hub()

        if self.state == 'present':
            # TODO: Add support for capture_description
            if not event_hub:
                changed = True
                self.log('Creating a new event hub')
                event_hub = self.eventhub_models.Eventhub(message_retention_in_days=self.message_retention_in_days,
                                                          partition_count=self.partition_count,
                                                          status=self.status)
                if not self.check_mode:
                    event_hub = self.create_or_update_event_hub(event_hub)

            else:
                # Compare message_retention_in_days
                if self.message_retention_in_days and self.message_retention_in_days != event_hub.message_retention_in_days:
                    changed = True
                    event_hub.message_retention_in_days = self.message_retention_in_days

                # Compare partition_count
                if self.partition_count and self.partition_count != event_hub.partition_count:
                    self.module.warn("partition_count is not changeable after the creation!")

                # Compare status
                if self.status and self.status != event_hub.status:
                    changed = True
                    event_hub.status = self.status

                if not self.check_mode:
                    event_hub = self.create_or_update_event_hub(event_hub)
            self.results = self.to_dict(event_hub)
        elif event_hub:
            changed = True
            if not self.check_mode:
                self.delete_event_hub()
        self.results['changed'] = changed
        return self.results

    def get_event_hub(self):
        try:
            return self.eventhub_client.event_hubs.get(self.resource_group, self.namespace, self.name)
        except Exception as exc:
            pass
            return None

    def create_or_update_event_hub(self, event_hub):
        try:
            return self.eventhub_client.event_hubs.create_or_update(self.resource_group, self.namespace, self.name, event_hub)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error creating or updating Event Hub{0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def delete_event_hub(self):
        try:
            return self.eventhub_client.event_hubs.delete(self.resource_group, self.namespace, self.name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error deleting Event Hub{0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, event_hub):
        return event_hub.as_dict()


def main():
    AzureRMEventHub()


if __name__ == '__main__':
    main()
