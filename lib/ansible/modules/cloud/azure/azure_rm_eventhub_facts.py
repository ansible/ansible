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
module: azure_rm_eventhub_facts
version_added: "2.9"
short_description: Get Azure event hub facts
description:
    - Get facts for an a specific event hub or all event hubs.

options:
    resource_group:
        description:
            - The resource group to search for the desired eventhub namespace.
        type: str
        required: true
    namespace:
        description:
            - Name of the eventhub namespace.
        type: str
        required: true
    name:
        description:
            - Name of the event hub.
        type: str
    show_sas_policies:
        description:
            - Whether to show the SAS policies.
            - Note if enable this option, the facts module will raise more than two HTTP calls for each resources, need more network overhead.
        type: bool
    show_consumer_groups:
        description:
            - Whether to show the consumer groups.
            - Note if enable this option, the facts module will raise one more HTTP call for each resources, need more network overhead.
        type: bool

extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
    - name: List all azure eventhubs by namespace
      azure_rm_eventhub_facts:
        resource_group: myResourceGroup
        namespace: testingnamespace

    - name: Get the facts for a specific eventhub
      azure_rm_eventhub_facts:
        resource_group: myResourceGroup
        namespace: testingnamespace
        name: testing
'''

RETURN = '''
eventhubs:
    description:
        - List of eventhub dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHubFacts(AzureRMModuleBase):

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
            name=dict(
                type='str'
            ),
            show_sas_policies=dict(
                type='bool'
            ),
            show_consumer_groups=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            eventhubs=[]
        )

        self.resource_group = None
        self.namespace = None
        self.name = None
        self.show_sas_policies = None
        self.show_consumer_groups = None

        super(AzureRMEventHubFacts, self).__init__(self.module_arg_spec, supports_tags=False, facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        else:
            response = self.list_by_namespace()
        self.results['eventhubs'] = [self.to_dict(x) for x in response]
        if self.show_sas_policies:
            for x in self.results['eventhubs']:
                self.add_sas_policies(x)
        if self.show_consumer_groups:
            for x in self.results['eventhubs']:
                self.add_consumer_groups(x)
        return self.results

    def get_item(self):
        '''Get a single eventhub'''

        self.log('Get properies for {0}'.format(self.name))

        item = None

        try:
            item = self.eventhub_client.event_hubs.get(resource_group_name=self.resource_group,
                                                       namespace_name=self.namespace,
                                                       event_hub_name=self.name)
            return [item]
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error when getting eventhub {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def list_by_namespace(self):
        '''Get all eventhub in a resource group'''

        try:
            self.log('Getting facts for event hubs by a eventhub namespace')
            return self.eventhub_client.event_hubs.list_by_namespace(resource_group_name=self.resource_group, namespace_name=self.namespace)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Filed to list eventhub by namespace {0}: {1}'.format(self.namespace, str(exc.inner_exception) or exc.message or str(exc)))

    def add_sas_policies(self, eventhub):
        name = eventhub['name']
        rules = self.list_authorization_rules(name)
        eventhub['sas_keys'] = [self.list_keys(eventhub=name, rule_name=x.name).as_dict() for x in rules]

    def list_authorization_rules(self, eventhub):
        try:
            self.log('Getting authorization rules of an event hub')
            return self.eventhub_client.event_hubs.list_authorization_rules(resource_group_name=self.resource_group,
                                                                            namespace_name=self.namespace,
                                                                            event_hub_name=eventhub)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list authorization rules of eventhub {0}: {1}'.format(eventhub, str(exc.inner_exception) or exc.message or str(exc)))

    def list_keys(self, eventhub, rule_name):
        try:
            self.log('Getting sas keys of a authorization rule')
            return self.eventhub_client.event_hubs.list_keys(resource_group_name=self.resource_group,
                                                             namespace_name=self.namespace,
                                                             event_hub_name=eventhub,
                                                             authorization_rule_name=rule_name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list keys of authorization rules {0}: {1}'.format(rule_name,
                                                                                   str(exc.inner_exception) or exc.message or str(exc)))

    def add_consumer_groups(self, eventhub):
        consumer_groups = self.list_consumer_groups(eventhub['name'])
        eventhub['consumer_groups'] = [x.as_dict() for x in consumer_groups]

    def list_consumer_groups(self, eventhub):
        try:
            self.log('Getting consumer groups of an event hub')
            return self.eventhub_client.consumer_groups.list_by_event_hub(resource_group_name=self.resource_group,
                                                                          namespace_name=self.namespace,
                                                                          event_hub_name=eventhub)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list consumer groups of the eventhub {0}: {1}'.format(eventhub, str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, eventhub):
        result = dict(
            id=eventhub.id,
            name=eventhub.name,
            message_retention_in_days=eventhub.message_retention_in_days,
            partition_count=eventhub.partition_count,
            partition_ids=eventhub.partition_ids,
            status=eventhub.status,
            capture_description=eventhub.capture_description.as_dict() if eventhub.capture_description else None
        )
        return result


def main():
    """Main module execution code path"""

    AzureRMEventHubFacts()


if __name__ == '__main__':
    main()
