#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Julien Stroheker <juliens@microsoft.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_availabilityset_facts

version_added: "2.4"

short_description: Get availability set facts.

description:
    - Get facts for a specific availability set or all availability sets.

options:
    name:
        description:
            - Limit results to a specific availability set
    resource_group:
        description:
            - The resource group to search for the desired availability set
    tags:
        description:
            - List of tags to be matched

extends_documentation_fragment:
    - azure

author:
    - "Julien Stroheker (@julienstroheker)"
'''

EXAMPLES = '''
    - name: Get facts for one availability set
      azure_rm_availabilityset_facts:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all availability sets in a specific resource group
      azure_rm_availabilityset_facts:
        resource_group: myResourceGroup

'''

RETURN = '''
azure_availabilityset:
    description: List of availability sets dicts.
    returned: always
    type: list
    example: [{
        "location": "eastus2",
        "name": "myavailabilityset",
        "properties": {
            "platformFaultDomainCount": 3,
            "platformUpdateDomainCount": 2,
            "virtualMachines": []
        },
        "sku": "Aligned",
        "type": "Microsoft.Compute/availabilitySets"
    }]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'AvailabilitySet'


class AzureRMAvailabilitySetFacts(AzureRMModuleBase):
    """Utility class to get availability set facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                azure_availabilitysets=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMAvailabilitySetFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")
        if self.name:
            self.results['ansible_facts']['azure_availabilitysets'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_availabilitysets'] = self.list_items()

        return self.results

    def get_item(self):
        """Get a single availability set"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.compute_client.availability_sets.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            avase = self.serialize_obj(item, AZURE_OBJECT_CLASS)
            avase['name'] = item.name
            avase['type'] = item.type
            avase['sku'] = item.sku.name
            result = [avase]

        return result

    def list_items(self):
        """Get all availability sets"""

        self.log('List all availability sets')

        try:
            response = self.compute_client.availability_sets.list(self.resource_group)
        except CloudError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                avase = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                avase['name'] = item.name
                avase['type'] = item.type
                avase['sku'] = item.sku.name
                results.append(avase)

        return results


def main():
    """Main module execution code path"""

    AzureRMAvailabilitySetFacts()


if __name__ == '__main__':
    main()
