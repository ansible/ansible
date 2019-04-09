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
            - Limit results to a specific resource group
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
    - name: list all azure_rm_eventhubnamespace_facts
      azure_rm_eventhubnamespace_facts:

    - name: list all azure_rm_eventhubnamespace_facts in RG
      azure_rm_eventhubnamespace_facts:
        resource_group: fanqiu-org

    - name: list all azure_rm_eventhubnamespace_facts by name
      azure_rm_eventhubnamespace_facts:
        name: fanqiutestnamespace040401
        resource_group: fanqiu-org

    - name: Get facts by tags
      azure_rm_eventhubnamespace_facts:
        tags:
          - testing
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
            tags=dict(
                type='list'
            )
        )

        self.results = dict(
            changed=False,
            eventhubnamespaces=[]
        )

        self.resource_group = None
        self.name = None
        self.tags = None

        super(AzureRMEventHubNamespaceFact, self).__init__(self.module_arg_spec, supports_tags=False, facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_by_resource_group()
        else:
            response = self.list_all()
        self.results['eventhubnamespaces'] = [self.to_dict(x) for x in response if self.has_tags(x.tags, self.tags)]
        return self.results

    def get_item(self):
        '''Get a single eventhub namespace'''

        self.log('Get properies for {0}'.format(self.name))

        item = None

        try:
            item = self.eventhub_client.namespaces.get(self.resource_group, self.name)
            return [item]
        except Exception as exc:
            self.fail('Error when getting eventhub namespace {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_by_resource_group(self):
        '''Get all eventhub namespaces in a resource group'''

        try:
            return self.eventhub_client.namespaces.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail('Filed to list eventhub namespace in resource group {0}: {1}'.format(self.resource_group, exc.message or str(exc)))

    def list_all(self):
        '''Get all eventhub namespaces'''

        try:
            return self.eventhub_client.namespaces.list()
        except Exception as exc:
            self.fail('Filed to list all eventhub namespaces - {0}'.format(exc.message or str(exc)))

    def to_dict(self, eventhubnamespace):
        result = dict(
            id = eventhubnamespace.id,
            name = eventhubnamespace.name,
            resource_group = parse_resource_id(eventhubnamespace.id).get('resourceGroups'),
            location = eventhubnamespace.location,
            tags = eventhubnamespace.tags,
            sku = eventhubnamespace.sku.name.lower(),
            is_auto_inflate_enabled = eventhubnamespace.is_auto_inflate_enabled,
            maximum_throughput_units = eventhubnamespace.maximum_throughput_units,
            kafka_enabled = eventhubnamespace.kafka_enabled
        )
        return result


def main():
    """Main module execution code path"""

    AzureRMEventHubNamespaceFact()


if __name__ == '__main__':
    main()
