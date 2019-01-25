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
version_added: "2.7"
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


extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Create a route
      azure_rm_route:
        name: foobar
        resource_group: Testing
        address_prefix: 10.1.0.0/16
        next_hop_type: virtual_network_gateway
        route_table_name: table

    - name: Delete a route
      azure_rm_route:
        name: foobar
        resource_group: Testing
        route_table_name: table
        state: absent
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
            state=dict(type='str', default='present', choices=['present', 'absent']),
            namespace=dict(type='str', required=True),
            type=dict(type='str', choices=['queue', 'topic', 'subscription'], required=True),
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
            sas_policies=dict(type='list', elements='dict',  options=sas_policy_spec, default=[])
        )

        required_if = [
            ('type', 'subscription', ['subscription_topic_name'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
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

        resource_group = self.get_resource_group(self.resource_group)
        self.location = resource_group.location

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
                support_ordering=self.support_ordering
            )
            if self.status:
                params['status'] = self.servicebus_models.EntityStatus(str.capitalize(_snake_to_camel(self.status)))
            for k, v in duration_spec_map.items():
                seconds = getattr(self, v)
                if seconds:
                    params[k] = timedelta(seconds=seconds)

            instance_type = getattr(self.servicebus_models, 'SB{0}'.format(str.capitalize(self.type)))
            instance = instance_type(**params)
            if not original:
                changed = True
                result = instance
            else:
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
                            rules[policy['name']] =  self.create_sas_policy(policy)
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
        ns = None
        try:
            ns = self.servicebus_client.namespaces.get(self.resource_group, self.namespace)
        except Exception:
            pass
        if not ns:
            try:
                poller = self.servicebus_client.namespaces.create_or_update(self.resource_group,
                                                                            self.namespace,
                                                                            self.servicebus_models.SBNamespace(location=self.location))
                ns = self.get_poller_result(poller)
            except Exception as exc:
                self.fail('Error creating namespace {0}'.format(exc.message) or str(exc))
        return ns

    def create_or_update(self, param):
        try:
            self.create_ns_if_not_exist()
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
            if self.type == 'subscription':
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
            if self.type == 'subscription':
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
            client.delete_authorization_rule(self.resource_group, self.namespace, self.name, name)
            return True
        except Exception as exc:
            self.fail('Error when deleting SAS policy {0} - {1}'.format(name, exc.message or str(exc)))

    def regenerate_sas_key(self, name):
        try:
            client = self._get_client()
            client.regenerate_keys(self.resource_group, self.namespace, self.name, name, 'PrimaryKey')
            client.regenerate_keys(self.resource_group, self.namespace, self.name, name, 'SecondaryKey')
        except Exception as exc:
            self.fail('Error when generating SAS policy {0}\'s key - {1}'.format(name, exc.message or str(exc)))
        return None

    def get_sas_key(self, name):
        try:
            client = self._get_client()
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
