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
module: azure_rm_servicebus_facts

version_added: "2.8"

short_description: Get servicebus facts.

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

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Get facts for one servicebus
      azure_rm_servicebus_facts:
        name: Testing
        resource_group: foo

    - name: Get facts for all servicebuss
      azure_rm_servicebus_facts:
        resource_group: foo

    - name: Get facts by tags
      azure_rm_servicebus_facts:
        tags:
          - testing
          - foo:bar
'''
RETURN = '''
id:
    description: Resource id.
    returned: success
    type: str
name:
    description: Name of the resource.
    returned: success
    type: str
resource_group:
    description: Resource group of the servicebus.
    returned: success
    type: str
disable_bgp_route_propagation:
    description: Whether the routes learned by BGP on that servicebus disabled.
    returned: success
    type: bool
tags:
    description: Tags of the servicebus.
    returned: success
    type: list
routes:
    description: Current routes of the servicebus.
    returned: success
    type: list
    sample: [
        {
          "id": "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.ServiceBus/namespaces/foobar/queues/route",
          "name": "route",
          "resource_group": "Testing",
          "servicebuss": "foobar",
          "address_prefix": "192.0.0.1",
          "next_hop_type": "virtual_networkGateway"
        }
    ]
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


class AzureRMServiceBusFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            type=dict(type='str',required=True, choices=['namespace', 'topic', 'queue', 'subscription']),
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

        super(AzureRMServiceBusFacts, self).__init__(self.module_arg_spec,
                                                     supports_tags=False,
                                                     required_if=required_if,
                                                     facts_module=True)

    def exec_module(self, **kwargs):

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
                policies[name] = self.get_sas_key(name)
            result['sas_policies'] = policies
        return  result

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
        except CloudError:
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
    AzureRMServiceBusFacts()


if __name__ == '__main__':
    main()
