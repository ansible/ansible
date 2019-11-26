#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_servicebus_info

version_added: "2.9"

short_description: Get servicebus facts

description:
    - Get facts for a specific servicebus or all servicebus in a resource group or subscription.

options:
    name:
        description:
            - Limit results to a specific servicebus.
    resource_group:
        description:
            - Limit results in a specific resource group.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    namespace:
        description:
            - Servicebus namespace name.
            - A namespace is a scoping container for all messaging components.
            - Multiple queues and topics can reside within a single namespace, and namespaces often serve as application containers.
            - Required when I(type=namespace).
    type:
        description:
            - Type of the resource.
        choices:
            - namespace
            - queue
            - topic
            - subscription
    topic:
        description:
            - Topic name.
            - Required when I(type=subscription).
    show_sas_policies:
        description:
            - Whether to show the SAS policies.
            - Not support when I(type=subscription).
            - Note if enable this option, the facts module will raise two more HTTP call for each resources, need more network overhead.
        type: bool
extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Get all namespaces under a resource group
  azure_rm_servicebus_info:
    resource_group: myResourceGroup
    type: namespace

- name: Get all topics under a namespace
  azure_rm_servicebus_info:
    resource_group: myResourceGroup
    namespace: bar
    type: topic

- name: Get a single queue with SAS policies
  azure_rm_servicebus_info:
    resource_group: myResourceGroup
    namespace: bar
    type: queue
    name: sbqueue
    show_sas_policies: true

- name: Get all subscriptions under a resource group
  azure_rm_servicebus_info:
    resource_group: myResourceGroup
    type: subscription
    namespace: bar
    topic: sbtopic
'''
RETURN = '''
servicebuses:
    description:
        - List of servicebus dicts.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/foo/providers/Microsoft.ServiceBus/
                     namespaces/bar/topics/baz/subscriptions/qux"
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: qux
        location:
            description:
                - The Geo-location where the resource lives.
            returned: always
            type: str
            sample: eastus
        namespace:
            description:
                - I(namespace) name of the C(queue) or C(topic), C(subscription).
            returned: always
            type: str
            sample: bar
        topic:
            description:
                - Topic name of a subscription.
            returned: always
            type: str
            sample: baz
        tags:
            description:
                - Resource tags.
            returned: always
            type: dict
            sample: {env: sandbox}
        sku:
            description:
                - Properties of namespace's SKU.
            returned: always
            type: str
            sample: Standard
        provisioning_state:
            description:
                - Provisioning state of the namespace.
            returned: always
            type: str
            sample: Succeeded
        service_bus_endpoint:
            description:
                - Endpoint you can use to perform Service Bus operations.
            returned: always
            type: str
            sample: "https://bar.servicebus.windows.net:443/"
        metric_id:
            description:
                - Identifier for Azure Insights metrics of namespace.
            returned: always
            type: str
            sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX:bar"
        type:
            description:
                - Resource type.
                - Namespace is a scoping container for all messaging components.
                - Queue enables you to store messages until the receiving application is available to receive and process them.
                - Topic and subscriptions enable 1:n relationships between publishers and subscribers.
            returned: always
            type: str
            sample: "Microsoft.ServiceBus/Namespaces/Topics"
        created_at:
            description:
                - Exact time the message was created.
            returned: always
            type: str
            sample: "2019-01-25 02:46:55.543953+00:00"
        updated_at:
            description:
                - The exact time the message was updated.
            returned: always
            type: str
            sample: "2019-01-25 02:46:55.543953+00:00"
        accessed_at:
            description:
                - Last time the message was sent, or a request was received for this topic.
            returned: always
            type: str
            sample: "2019-01-25 02:46:55.543953+00:00"
        subscription_count:
            description:
                - Number of subscriptions under a topic.
            returned: always
            type: int
            sample: 1
        count_details:
            description:
                - Message count details.
            returned: always
            type: complex
            contains:
                active_message_count:
                    description:
                        - Number of active messages in the C(queue), C(topic), or C(subscription).
                    returned: always
                    type: int
                    sample: 0
                dead_letter_message_count:
                    description:
                        - Number of messages that are dead lettered.
                    returned: always
                    type: int
                    sample: 0
                scheduled_message_count:
                    description:
                        - Number of scheduled messages.
                    returned: always
                    type: int
                    sample: 0
                transfer_message_count:
                    description:
                        - Number of messages transferred to another C(queue), C(topic), or C(subscription).
                    returned: always
                    type: int
                    sample: 0
                transfer_dead_letter_message_count:
                    description:
                        - Number of messages transferred into dead letters.
                    returned: always
                    type: int
                    sample: 0
        support_ordering:
            description:
                - Value that indicates whether the C(topic) supports ordering.
            returned: always
            type: bool
            sample: true
        status:
            description:
              - The status of a messaging entity.
            returned: always
            type: str
            sample: active
        requires_session:
            description:
                - A value that indicates whether the C(queue) or C(topic) supports the concept of sessions.
            returned: always
            type: bool
            sample: true
        requires_duplicate_detection:
            description:
               - A value indicating if this C(queue) or C(topic) requires duplicate detection.
            returned: always
            type: bool
            sample: true
        max_size_in_mb:
            description:
                - Maximum size of the C(queue) or C(topic) in megabytes, which is the size of the memory allocated for the C(topic).
            returned: always
            type: int
            sample: 5120
        max_delivery_count:
            description:
                - The maximum delivery count.
                - A message is automatically deadlettered after this number of deliveries.
            returned: always
            type: int
            sample: 10
        lock_duration_in_seconds:
            description:
                - ISO 8601 timespan duration of a peek-lock.
                - The amount of time that the message is locked for other receivers.
                - The maximum value for LockDuration is 5 minutes.
            returned: always
            type: int
            sample: 60
        forward_to:
            description:
                - C(queue) or C(topic) name to forward the messages.
            returned: always
            type: str
            sample: quux
        forward_dead_lettered_messages_to:
            description:
                - C(queue) or C(topic) name to forward the Dead Letter message.
            returned: always
            type: str
            sample: corge
        enable_partitioning:
            description:
                - Value that indicates whether the C(queue) or C(topic) to be partitioned across multiple message brokers is enabled.
            returned: always
            type: bool
            sample: true
        enable_express:
            description:
                - Value that indicates whether Express Entities are enabled.
                - An express topic holds a message in memory temporarily before writing it to persistent storage.
            returned: always
            type: bool
            sample: true
        enable_batched_operations:
            description:
                - Value that indicates whether server-side batched operations are enabled.
            returned: always
            type: bool
            sample: true
        duplicate_detection_time_in_seconds:
            description:
                - ISO 8601 timeSpan structure that defines the duration of the duplicate detection history.
            returned: always
            type: int
            sample: 600
        default_message_time_to_live_seconds:
            description:
                - ISO 8061 Default message timespan to live value.
                - This is the duration after which the message expires, starting from when the message is sent to Service Bus.
                - This is the default value used when TimeToLive is not set on a message itself.
            returned: always
            type: int
            sample: 0
        dead_lettering_on_message_expiration:
            description:
                - A value that indicates whether this C(queue) or C(topic) has dead letter support when a message expires.
            returned: always
            type: int
            sample: 0
        dead_lettering_on_filter_evaluation_exceptions:
            description:
                - Value that indicates whether a subscription has dead letter support on filter evaluation exceptions.
            returned: always
            type: int
            sample: 0
        auto_delete_on_idle_in_seconds:
            description:
                - ISO 8061 timeSpan idle interval after which the  queue or topic is automatically deleted.
                - The minimum duration is 5 minutes.
            returned: always
            type: int
            sample: true
        size_in_bytes:
            description:
                - The size of the C(queue) or C(topic) in bytes.
            returned: always
            type: int
            sample: 0
        message_count:
            description:
                - Number of messages.
            returned: always
            type: int
            sample: 10
        sas_policies:
            description:
                - Dict of SAS policies.
                - Will not be returned until I(show_sas_policy) set.
            returned: always
            type: dict
            sample:  {
                        "testpolicy1": {
                            "id": "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/
                                   foo/providers/Microsoft.ServiceBus/namespaces/bar/queues/qux/authorizationRules/testpolicy1",
                            "keys": {
                                "key_name": "testpolicy1",
                                "primary_connection_string": "Endpoint=sb://bar.servicebus.windows.net/;
                                                              SharedAccessKeyName=testpolicy1;SharedAccessKey=XXXXXXXXXXXXXXXXX;EntityPath=qux",
                                "primary_key": "XXXXXXXXXXXXXXXXX",
                                "secondary_connection_string": "Endpoint=sb://bar.servicebus.windows.net/;
                                                                SharedAccessKeyName=testpolicy1;SharedAccessKey=XXXXXXXXXXXXXXX;EntityPath=qux",
                                "secondary_key": "XXXXXXXXXXXXXXX"
                            },
                            "name": "testpolicy1",
                            "rights": "listen_send",
                            "type": "Microsoft.ServiceBus/Namespaces/Queues/AuthorizationRules"
                        }
                     }
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict
from ansible.module_utils.common.dict_transformations import _camel_to_snake
from ansible.module_utils._text import to_native
from datetime import datetime, timedelta

duration_spec_map = dict(
    default_message_time_to_live='default_message_time_to_live_seconds',
    duplicate_detection_history_time_window='duplicate_detection_time_in_seconds',
    auto_delete_on_idle='auto_delete_on_idle_in_seconds',
    lock_duration='lock_duration_in_seconds'
)


def is_valid_timedelta(value):
    if value == timedelta(10675199, 10085, 477581):
        return None
    return value


class AzureRMServiceBusInfo(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            type=dict(type='str', required=True, choices=['namespace', 'topic', 'queue', 'subscription']),
            namespace=dict(type='str'),
            topic=dict(type='str'),
            show_sas_policies=dict(type='bool')
        )

        required_if = [
            ('type', 'subscription', ['topic', 'resource_group', 'namespace']),
            ('type', 'topic', ['resource_group', 'namespace']),
            ('type', 'queue', ['resource_group', 'namespace'])
        ]

        self.results = dict(
            changed=False,
            servicebuses=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.type = None
        self.namespace = None
        self.topic = None
        self.show_sas_policies = None

        super(AzureRMServiceBusInfo, self).__init__(self.module_arg_spec,
                                                    supports_tags=False,
                                                    required_if=required_if,
                                                    facts_module=True)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_servicebus_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_servicebus_facts' module has been renamed to 'azure_rm_servicebus_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_items()
        else:
            response = self.list_all_items()

        self.results['servicebuses'] = [self.instance_to_dict(x) for x in response]
        return self.results

    def instance_to_dict(self, instance):
        result = dict()
        instance_type = getattr(self.servicebus_models, 'SB{0}'.format(str.capitalize(self.type)))
        attribute_map = instance_type._attribute_map
        for attribute in attribute_map.keys():
            value = getattr(instance, attribute)
            if attribute_map[attribute]['type'] == 'duration':
                if is_valid_timedelta(value):
                    key = duration_spec_map.get(attribute) or attribute
                    result[key] = int(value.total_seconds())
            elif attribute == 'status':
                result['status'] = _camel_to_snake(value)
            elif isinstance(value, self.servicebus_models.MessageCountDetails):
                result[attribute] = value.as_dict()
            elif isinstance(value, self.servicebus_models.SBSku):
                result[attribute] = value.name.lower()
            elif isinstance(value, datetime):
                result[attribute] = str(value)
            elif isinstance(value, str):
                result[attribute] = to_native(value)
            elif attribute == 'max_size_in_megabytes':
                result['max_size_in_mb'] = value
            else:
                result[attribute] = value
        if self.show_sas_policies and self.type != 'subscription':
            policies = self.get_auth_rules()
            for name in policies.keys():
                policies[name]['keys'] = self.get_sas_key(name)
            result['sas_policies'] = policies
        if self.namespace:
            result['namespace'] = self.namespace
        if self.topic:
            result['topic'] = self.topic
        return result

    def _get_client(self):
        return getattr(self.servicebus_client, '{0}s'.format(self.type))

    def get_item(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                item = client.get(self.resource_group, self.name)
                return [item] if self.has_tags(item.tags, self.tags) else []
            elif self.type == 'subscription':
                return [client.get(self.resource_group, self.namespace, self.topic, self.name)]
            else:
                return [client.get(self.resource_group, self.namespace, self.name)]
        except Exception:
            pass
        return []

    def list_items(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                response = client.list_by_resource_group(self.resource_group)
                return [x for x in response if self.has_tags(x.tags, self.tags)]
            elif self.type == 'subscription':
                return client.list_by_topic(self.resource_group, self.namespace, self.topic)
            else:
                return client.list_by_namespace(self.resource_group, self.namespace)
        except CloudError as exc:
            self.fail("Failed to list items - {0}".format(str(exc)))
        return []

    def list_all_items(self):
        self.log("List all items in subscription")
        try:
            if self.type != 'namespace':
                return []
            response = self.servicebus_client.namespaces.list()
            return [x for x in response if self.has_tags(x.tags, self.tags)]
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))
        return []

    def get_auth_rules(self):
        result = dict()
        try:
            client = self._get_client()
            if self.type == 'namespace':
                rules = client.list_authorization_rules(self.resource_group, self.name)
            else:
                rules = client.list_authorization_rules(self.resource_group, self.namespace, self.name)
            while True:
                rule = rules.next()
                result[rule.name] = self.policy_to_dict(rule)
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Error when getting SAS policies for {0} {1}: {2}'.format(self.type, self.name, exc.message or str(exc)))
        return result

    def get_sas_key(self, name):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                return client.list_keys(self.resource_group, self.name, name).as_dict()
            else:
                return client.list_keys(self.resource_group, self.namespace, self.name, name).as_dict()
        except Exception as exc:
            self.fail('Error when getting SAS policy {0}\'s key - {1}'.format(name, exc.message or str(exc)))
        return None

    def policy_to_dict(self, rule):
        result = rule.as_dict()
        rights = result['rights']
        if 'Manage' in rights:
            result['rights'] = 'manage'
        elif 'Listen' in rights and 'Send' in rights:
            result['rights'] = 'listen_send'
        else:
            result['rights'] = rights[0].lower()
        return result


def main():
    AzureRMServiceBusInfo()


if __name__ == '__main__':
    main()
