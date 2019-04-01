#!/usr/bin/python
#
# Copyright (c) 2019 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_iothub_facts

version_added: "2.8"

short_description: Get IoT Hub facts.

description:
    - Get facts for a specific IoT Hub or all IoT Hubs.

options:
    name:
        description:
            - Limit results to a specific resource group.
    resource_group:
        description:
            - The resource group to search for the desired IoT Hub
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"
'''

EXAMPLES = '''
    - name: Get facts for one IoT Hub
      azure_rm_iothub_facts:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all IoT Hubs
      azure_rm_iothub_facts:

    - name: Get facts for all IoT Hubs in a specific resource group
      azure_rm_iothub_facts:
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_iothub_facts:
        tags:
          - testing
'''

RETURN = '''
azure_iothubs:
    description: List of IoT Hub dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass



class AzureRMIoTHubFacts(AzureRMModuleBase):
    """Utility class to get IoT Hub facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                azure_iothubs=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMIoTHubFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_by_resource_group()
        else:
            response = self.list_all()
        self.results['iothubs'] = [self.to_dict(x) for x in response if self.has_tags(x.tags, self.tags)]
        return self.results

    def get_item(self):
        """Get a single IoT Hub"""

        self.log('Get properties for {0}'.format(self.name))

        item = None

        try:
            item = self.IoThub_client.iot_hub_resource.get(self.resource_group, self.name)
            return [item]
        except Exception as exc:
            self.fail('Error when getting IoT Hub {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_all(self):
        """Get all IoT Hubs"""

        self.log('List all IoT Hubs')

        try:
            return self.IoThub_client.iot_hub_resource.list_by_subscription()
        except Exception as exc:
            self.fail('Failed to list all IoT Hubs - {0}'.format(str(exc)))

    def list_by_resource_group(self):
        try:
            return self.IoThub_client.iot_hub_resource.list(self.resource_group)
        except Exception as exc:
            self.fail('Failed to list IoT Hub in resource group {0} - {1}'.format(self.resource_group, exc.message or str(exc)))

    def to_dict(self, hub):
        result = dict(
            id=hub.id,
            name=hub.name,
            resource_group=parse_resource_id(hub.id).get('resourceGroups'),
            location=hub.location,
            tags=hub.tags,
            unit=hub.sku.capacity,
            sku=hub.sku.name.lower()
        )
        return result


def main():
    """Main module execution code path"""

    AzureRMIoTHubFacts()


if __name__ == '__main__':
    main()
