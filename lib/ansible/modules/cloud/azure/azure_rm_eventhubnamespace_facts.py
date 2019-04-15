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
module: azure_rm_eventhubnamespace_facts
version_added: "2.9"
short_description: Get Azure eventhub namespace facts.
description:
    - Get facts for an a specific eventhub namespace or all eventhub namespaces.

options:
    resource_group:
        description:
            - The resource group to search for the desired eventhub namespace.
    name:
        description:
            - Name of the eventhub namespace
    show_sas_policies:
        description:
            - Whether to show the SAS policies.
            - Note if enable this option, the facts module will raise two more HTTP call for each resources, need more network overhead.
        type: bool

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
    - name: list all azure_rm_eventhubnamespace_facts
      azure_rm_eventhubnamespace_facts:

    - name: list all azure_rm_eventhubnamespace_facts in RG
      azure_rm_eventhubnamespace_facts:
        resource_group: myResourceGroup

    - name: list all azure_rm_eventhubnamespace_facts by name
      azure_rm_eventhubnamespace_facts:
        name: myEventhubNamespace
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_eventhubnamespace_facts:
        tags:
          testing
'''

RETURN = '''
eventhubnamespaces:
    description: List of eventhub namespace dicts.
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


class AzureRMEventHubNamespaceFact(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            ),
            show_sas_policies=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            eventhubnamespaces=[]
        )

        self.resource_group = None
        self.name = None
        self.tags = None
        self.show_sas_policies = None

        super(AzureRMEventHubNamespaceFact, self).__init__(self.module_arg_spec, supports_tags=True, facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_by_resource_group()
        else:
            response = self.list_all()
        self.results['eventhubnamespaces'] = [self.to_dict(x) for x in response if self.has_tags(x.tags, self.tags)]

        if self.show_sas_policies:
            self.results['eventhubnamespaces'] = [self.get_sas_policies(x) for x in self.results['eventhubnamespaces']]
        return self.results

    def get_item(self):
        '''Get a single eventhub namespace'''

        self.log('Get properies for {0}'.format(self.name))

        item = None

        try:
            item = self.eventhub_client.namespaces.get(resource_group_name=self.resource_group, namespace_name=self.name)
            return [item]
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error when getting eventhub namespace {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def list_by_resource_group(self):
        '''Get all eventhub namespaces in a resource group'''

        try:
            return self.eventhub_client.namespaces.list_by_resource_group(resource_group_name=self.resource_group)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list eventhub namespace in resource group {0}: {1}'.format(self.resource_group,
                                                                                            str(exc.inner_exception) or exc.message or str(exc)))

    def list_all(self):
        '''Get all eventhub namespaces'''

        try:
            return self.eventhub_client.namespaces.list()
        except Exception as exc:
            self.fail('Filed to list all eventhub namespaces - {0}'.format(exc.message or str(exc)))

    def get_sas_policies(self, eventhubnamespace):
        results = eventhubnamespace
        namespace_name = eventhubnamespace['name']
        resource_group_name = eventhubnamespace['resource_group']
        rules = self.list_authorization_rules(resource_group_name=resource_group_name, namespace_name=namespace_name)
        results['sas_keys'] = [self.list_keys(resource_group_name=resource_group_name, namespace_name=namespace_name, rule_name=x.name) for x in rules]
        return results

    def list_authorization_rules(self, resource_group_name, namespace_name):
        try:
            self.log("Getting authorization rules of an eventhub namespace")
            return self.eventhub_client.namespaces.list_authorization_rules(resource_group_name=resource_group_name, namespace_name=namespace_name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list authorization rules of namespace {0}: {1}'.format(namespace_name, str(exc.inner_exception) or exc.message or str(exc)))

    def list_keys(self, resource_group_name, namespace_name, rule_name):
        try:
            self.log("Getting sas keys of an authorization rule of an eventhub namespace")
            sas_keys = self.eventhub_client.namespaces.list_keys(resource_group_name=resource_group_name,
                                                                 namespace_name=namespace_name,
                                                                 authorization_rule_name=rule_name)
            return sas_keys.as_dict()
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list keys of authorization rules {0}: {1}'.format(rule_name,
                                                                                   str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, eventhubnamespace):
        result = dict(
            id=eventhubnamespace.id,
            name=eventhubnamespace.name,
            resource_group=parse_resource_id(eventhubnamespace.id).get('resource_group'),
            location=eventhubnamespace.location,
            tags=eventhubnamespace.tags,
            sku=eventhubnamespace.sku.name.lower(),
            is_auto_inflate_enabled=eventhubnamespace.is_auto_inflate_enabled,
            maximum_throughput_units=eventhubnamespace.maximum_throughput_units,
            kafka_enabled=eventhubnamespace.kafka_enabled
        )
        return result


def main():
    """Main module execution code path"""

    AzureRMEventHubNamespaceFact()


if __name__ == '__main__':
    main()
