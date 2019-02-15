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
module: azure_rm_servicebus
version_added: "2.8"
short_description: Manage Azure Service Bus.
description:
    - Create, update or delete an Azure Service Bus namespaces, queues, topics, subscriptions and rules.
options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the route.
        required: true
    state:
        description:
            - Assert the state of the route. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
    namespace:
        description:
            - Servicebus namespace name.
            - A namespace is a scoping container for all messaging components.
            - Multiple queues and topics can reside within a single namespace, and namespaces often serve as application containers.
            - Required when C(type) is not C(namespace).
    location:
        description:
            - Namespace location.
    type:
        description:
            - Type of the messaging application.
            - Queue enables you to store messages until the receiving application is available to receive and process them.
            - Topic and subscriptions enable 1:n relationships between publishers and subscribers.
        choices:
            - namespace
            - queue
            - topic
            - subscription
    subscription_topic_name:
        description:
            - Topic name which the subscription subscribe to.
            - Required when C(type) is set to C(subscription).
    auto_delete_on_idle_in_seconds:
        description:
            - Time idle interval after which a queue is automatically deleted.
            - The minimum duration is 5 minutes.
        type: int
    dead_lettering_on_message_expiration:
        description:
            - A value that indicates whether a queue has dead letter support when a message expires.
        type: bool
    dead_lettering_on_filter_evaluation_exceptions:
        description:
            - Value that indicates whether a subscription has dead letter support on filter evaluation exceptions.
        type: bool
    default_message_time_to_live_seconds:
        description:
            - Default message timespan to live value.
            - This is the duration after which the message expires, starting from when the message is sent to Service Bus.
            - This is the default value used when TimeToLive is not set on a message itself.
        type: int
    enable_batched_operations:
        description:
            - Value that indicates whether server-side batched operations are enabled.
        type: bool
    enable_express:
        description:
            - Value that indicates whether Express Entities are enabled.
            - An express topic or queue holds a message in memory temporarily before writing it to persistent storage.
        type: bool
    enable_partitioning:
        description:
            - A value that indicates whether the topic or queue is to be partitioned across multiple message brokers.
        type: bool
    forward_dead_lettered_messages_to:
        description:
            - Queue or topic name to forward the Dead Letter message for a queue.
    forward_to:
        description:
            - Queue or topic name to forward the messages for a queue.
    lock_duration_in_seconds:
        description:
            - Timespan duration of a peek-lock.
            - The amount of time that the message is locked for other receivers.
            - The maximum value for LockDuration is 5 minutes.
        type: int
    max_delivery_count:
        description:
            - he maximum delivery count.
            - A message is automatically deadlettered after this number of deliveries.
        type: int
    max_size_in_mb:
        description:
            - The maximum size of the queue in megabytes, which is the size of memory allocated for the queue.
        type: int
    requires_session:
        description:
            - A value that indicates whether the queue supports the concept of sessions.
        type: bool
    requires_duplicate_detection:
        description:
            -  A value indicating if this queue or topic  requires duplicate detection.
        type: bool
    duplicate_detection_time_in_seconds:
        description:
            - TimeSpan structure that defines the duration of the duplicate detection history.
        type: int
    status:
        description:
            - Status of the entity.
        choices:
            - active
            - disabled
            - restoring
            - send_disabled
            - receive_disabled
            - creating
            - deleting
            - renaming
            - unkown
    support_ordering:
        description:
            - Value that indicates whether the topic supports ordering.
        type: bool
    sas_policies:
        description:
            - List of shared access policy management.
        suboptions:
            state:
                description:
                    - Assert the state of the route. Use 'present' to create or update and
                      'absent' to delete.
                default: present
                choices:
                    - absent
                    - present
            name:
                description:
                    - Name of the SAS policy.
                required: True
            regenerate_key:
                description:
                    - Regenerate the SAS policy primary and secondary key.
                type: bool
            rights:
                description:
                    - Claim rights of the SAS policy.
                required: True
                choices:
                    - manage
                    - listen
                    - send
                    - listen_send

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
- name: Create a namespace
  azure_rm_servicebus:
      name: deadbeef
      location: eastus

- name: Create a topic
  azure_rm_servicebus:
      name: subtopic
      resource_group: foo
      namespace: bar
      duplicate_detection_time_in_seconds: 600
      type: topic
      sas_policies:
        - name: testpolicy
          rights: manage

- name: Create a subscription
  azure_rm_servicebus:
      name: sbsub
      resource_group: foo
      namespace: bar
      type: subscription
      subscription_topic_name: subtopic
'''
RETURN = '''
id:
    description: Current state of the route.
    returned: success
    type: str
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
from ansible.module_utils._text import to_native
from datetime import datetime, timedelta


duration_spec_map = dict(
    default_message_time_to_live='default_message_time_to_live_seconds',
    duplicate_detection_history_time_window='duplicate_detection_time_in_seconds',
    auto_delete_on_idle='auto_delete_on_idle_in_seconds',
    lock_duration='lock_duration_in_seconds'
)


sas_policy_spec = dict(
    state=dict(type='str', default='present', choices=['present', 'absent']),
    name=dict(type='str', required=True),
    regenerate_key=dict(type='bool'),
    rights=dict(type='str', choices=['manage', 'listen', 'send', 'listen_send'])
)


class AzureRMServiceBus(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            location=dict(type='str'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            namespace=dict(type='str'),
            type=dict(type='str', choices=['queue', 'topic', 'subscription', 'namespace'], required=True),
            subscription_topic_name=dict(type='str'),
            auto_delete_on_idle_in_seconds=dict(type='int'),
            dead_lettering_on_filter_evaluation_exceptions=dict(type='bool'),
            dead_lettering_on_message_expiration=dict(type='bool'),
            default_message_time_to_live_seconds=dict(type='int'),
            enable_batched_operations=dict(type='bool'),
            enable_express=dict(type='bool'),
            enable_partitioning=dict(type='bool'),
            forward_dead_lettered_messages_to=dict(type='str'),
            forward_to=dict(type='str'),
            lock_duration_in_seconds=dict(type='int'),
            max_delivery_count=dict(type='int'),
            max_size_in_mb=dict(type='int'),
            requires_session=dict(type='bool'),
            requires_duplicate_detection=dict(type='bool'),
            duplicate_detection_time_in_seconds=dict(type='int'),
            status=dict(type='str',
                        choices=['active', 'disabled', 'restoring', 'send_disabled', 'receive_disabled', 'creating', 'deleting', 'renaming', 'unkown']),
            support_ordering=dict(type='bool'),
            sas_policies=dict(type='list', elements='dict', options=sas_policy_spec, default=[])
        )

        required_if = [
            ('type', 'subscription', ['subscription_topic_name', 'namespace']),
            ('type', 'queue', ['namespace']),
            ('type', 'topic', ['namespace'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
        self.location = None
        self.type = None
        self.subscription_topic_name = None
        self.auto_delete_on_idle_in_seconds = None
        self.dead_lettering_on_message_expiration = None
        self.dead_lettering_on_filter_evaluation_exceptions = None
        self.default_message_time_to_live_seconds = None
        self.enable_batched_operations = None
        self.enable_express = None
        self.enable_partitioning = None
        self.forward_dead_lettered_messages_to = None
        self.forward_to = None
        self.lock_duration_in_seconds = None
        self.max_delivery_count = None
        self.max_size_in_mb = None
        self.requires_session = None
        self.requires_duplicate_detection = None
        self.duplicate_detection_time_in_seconds = None
        self.status = None
        self.support_ordering = None
        self.location = None
        self.sas_policies = None

        self.results = dict(
            changed=False,
            id=None
        )

        super(AzureRMServiceBus, self).__init__(self.module_arg_spec,
                                                required_if=required_if,
                                                supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False

        if not self.location:
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location

        if self.type == 'namespace':
            self.namespace = self.name

        original = self.get()
        if self.state == 'present':
            # Create the resource instance
            params = dict(
                dead_lettering_on_filter_evaluation_exceptions=self.dead_lettering_on_filter_evaluation_exceptions,
                dead_lettering_on_message_expiration=self.dead_lettering_on_message_expiration,
                enable_batched_operations=self.enable_batched_operations,
                enable_express=self.enable_express,
                enable_partitioning=self.enable_partitioning,
                forward_dead_lettered_messages_to=self.forward_dead_lettered_messages_to,
                forward_to=self.forward_to,
                max_delivery_count=self.max_delivery_count,
                max_size_in_megabytes=self.max_size_in_mb,
                requires_session=self.requires_session,
                support_ordering=self.support_ordering,
                location=self.location
            )
            if self.status:
                params['status'] = self.servicebus_models.EntityStatus(str.capitalize(_snake_to_camel(self.status)))
            for k, v in duration_spec_map.items():
                seconds = getattr(self, v)
                if seconds:
                    params[k] = timedelta(seconds=seconds)

            instance_type = getattr(self.servicebus_models, 'SB{0}'.format(str.capitalize(self.type)))
            instance = instance_type(**params)
            result = original
            if not original:
                changed = True
                result = instance
            elif self.type != 'namespace':  # namespace's location and sku cannot be updated
                result = original
                attribute_map = set(instance_type._attribute_map.keys()) - set(instance_type._validation.keys())
                for attribute in attribute_map:
                    value = getattr(instance, attribute)
                    if value and value != getattr(original, attribute):
                        changed = True
            if changed and not self.check_mode:
                result = self.create_or_update(instance)
            self.results = self.to_dict(result, instance_type)

            # handle SAS policies, subscription should use topic to do such management
            if self.type != 'subscription':
                rules = self.get_auth_rules()
                for policy in self.sas_policies:
                    original_policy = rules.get(policy['name'])
                    if policy['state'] == 'present':
                        # whether create or update the policy
                        policy_changed = False
                        if original_policy and policy.get('rights') and policy['rights'] != original_policy['rights']:
                            policy_changed = True
                        elif not original_policy:
                            policy_changed = True
                        if policy_changed and not self.check_mode:
                            rules[policy['name']] = self.create_sas_policy(policy)
                        # get the original key or regenerate one
                        if policy.get('regenerate_key'):
                            policy_changed = True
                            self.regenerate_sas_key(policy['name'])
                        changed = changed | policy_changed
                    elif original_policy:
                        changed = True
                        if not self.check_mode:
                            rules.pop(policy['name'])
                            self.delete_sas_policy(policy['name'])
                for name in rules.keys():
                    rules[name]['keys'] = self.get_sas_key(name)
                self.results['sas_policies'] = rules
        elif original:
            changed = True
            if not self.check_mode:
                self.delete()
                self.results['deleted'] = True

        self.results['changed'] = changed
        return self.results

    def create_ns_if_not_exist(self):
        self.log('Cannot find namespace, creating a one')
        ns = None
        try:
            ns = self.servicebus_client.namespaces.get(self.resource_group, self.namespace)
        except Exception:
            pass
        if not ns:
            try:
                check_name = self.servicebus_client.namespaces.check_name_availability_method(self.namespace)
                if check_name and check_name.name_available:
                    poller = self.servicebus_client.namespaces.create_or_update(self.resource_group,
                                                                                self.namespace,
                                                                                self.servicebus_models.SBNamespace(location=self.location))
                    ns = self.get_poller_result(poller)
                else:
                    self.fail("Error creating namespace {0} - {1}".format(self.namespace, check_name.message or str(check_name)))
            except Exception as exc:
                self.fail('Error creating namespace {0} - {1}'.format(self.namespace, exc.message or str(exc)))
        return ns

    def create_or_update(self, param):
        ns = self.create_ns_if_not_exist()
        if self.type == 'namespace':
            return ns
        try:
            client = self._get_client()
            if self.type == 'subscription':
                return client.create_or_update(self.resource_group, self.namespace, self.subscription_topic_name, self.name, param)
            else:
                return client.create_or_update(self.resource_group, self.namespace, self.name, param)
        except Exception as exc:
            self.fail("Error creating or updating route {0} - {1}".format(self.name, str(exc)))

    def delete(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                client.delete(self.resource_group, self.name)
            elif self.type == 'subscription':
                client.delete(self.resource_group, self.namespace, self.subscription_topic_name, self.name)
            else:
                client.delete(self.resource_group, self.namespace, self.name)
            return True
        except Exception as exc:
            self.fail("Error deleting route {0} - {1}".format(self.name, str(exc)))

    def _get_client(self):
        return getattr(self.servicebus_client, '{0}s'.format(self.type))

    def get(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                return client.get(self.resource_group, self.name)
            elif self.type == 'subscription':
                return client.get(self.resource_group, self.namespace, self.subscription_topic_name, self.name)
            else:
                return client.get(self.resource_group, self.namespace, self.name)
        except Exception:
            return None

    def to_dict(self, instance, instance_type):
        result = dict()
        attribute_map = instance_type._attribute_map
        for attribute in attribute_map.keys():
            value = getattr(instance, attribute)
            if not value:
                continue
            if attribute_map[attribute]['type'] == 'duration':
                if is_valid_timedelta(value):
                    key = duration_spec_map.get(attribute) or attribute
                    result[key] = int(value.total_seconds())
            elif attribute == 'status':
                result['status'] = _camel_to_snake(value)
            elif isinstance(value, self.servicebus_models.MessageCountDetails):
                result[attribute] = value.as_dict()
            elif isinstance(value, self.servicebus_models.SBSku):
                result[attribute] = value.name
            elif isinstance(value, datetime):
                result[attribute] = str(value)
            elif isinstance(value, str):
                result[attribute] = to_native(value)
            elif attribute == 'max_size_in_megabytes':
                result['max_size_in_mb'] = value
            else:
                result[attribute] = value
        return result

    # SAS policy
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
        except Exception:
            pass
        return result

    def create_sas_policy(self, policy):
        if policy['rights'] == 'listen_send':
            rights = ['Listen', 'Send']
        elif policy['rights'] == 'manage':
            rights = ['Listen', 'Send', 'Manage']
        else:
            rights = [str.capitalize(policy['rights'])]
        try:
            client = self._get_client()
            rule = client.create_or_update_authorization_rule(self.resource_group, self.namespace, self.name, policy['name'], rights)
            return self.policy_to_dict(rule)
        except Exception as exc:
            self.fail('Error when creating or updating SAS policy {0} - {1}'.format(policy['name'], exc.message or str(exc)))
        return None

    def delete_sas_policy(self, name):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                client.delete_authorization_rule(self.resource_group, self.name, name)
            else:
                client.delete_authorization_rule(self.resource_group, self.namespace, self.name, name)
            return True
        except Exception as exc:
            self.fail('Error when deleting SAS policy {0} - {1}'.format(name, exc.message or str(exc)))

    def regenerate_sas_key(self, name):
        try:
            client = self._get_client()
            for key in ['PrimaryKey', 'SecondaryKey']:
                if self.type == 'namespace':
                    client.regenerate_keys(self.resource_group, self.name, name, key)
                else:
                    client.regenerate_keys(self.resource_group, self.namespace, self.name, name, key)
        except Exception as exc:
            self.fail('Error when generating SAS policy {0}\'s key - {1}'.format(name, exc.message or str(exc)))
        return None

    def get_sas_key(self, name):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                return client.list_keys(self.resource_group, self.name, name).as_dict()
            else:
                return client.list_keys(self.resource_group, self.namespace, self.name, name).as_dict()
        except Exception:
            pass
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


def is_valid_timedelta(value):
    if value == timedelta(10675199, 10085, 477581):
        return None
    return value


def main():
    AzureRMServiceBus()


if __name__ == '__main__':
    main()
