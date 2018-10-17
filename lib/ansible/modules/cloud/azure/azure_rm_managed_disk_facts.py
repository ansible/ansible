#!/usr/bin/python
#
# Copyright (c) 2016 Bruno Medina Bolanos Cacho, <bruno.medina@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_managed_disk_facts

version_added: "2.4"

short_description: Get managed disk facts.

description:
    - Get facts for a specific managed disk or all managed disks.

options:
    name:
        description:
            - Limit results to a specific managed disk
    resource_group:
        description:
            - Limit results to a specific resource group
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Bruno Medina (@brusMX)"
'''

EXAMPLES = '''
    - name: Get facts for one managed disk
      azure_rm_managed_disk_facts:
        name: Testing
        resource_group: TestRG

    - name: Get facts for all managed disks
      azure_rm_managed_disk_facts:

    - name: Get facts by tags
      azure_rm_managed_disk_facts:
        tags:
          - testing
'''

RETURN = '''
azure_managed_disk:
    description: List of managed disk dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from ansible.modules.cloud.azure.azure_rm_managed_disk import managed_disk_to_dict
except:
    # handled in azure_rm_common
    pass


class AzureRMManagedDiskFacts(AzureRMModuleBase):
    """Utility class to get managed disk facts"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=False
            ),
            name=dict(
                type='str',
                required=False
            ),
            tags=dict(
                type='str',
                required=False
            ),
        )
        self.results = dict(
            ansible_facts=dict(
                azure_managed_disk=[]
            )
        )
        self.resource_group = None
        self.name = None
        self.create_option = None
        self.source_uri = None
        self.source_resource_uri = None
        self.tags = None
        super(AzureRMManagedDiskFacts, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_check_mode=True,
            supports_tags=True)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.results['ansible_facts']['azure_managed_disk'] = (
            self.get_item() if self.name
            else self.list_items()
        )

        return self.results

    def get_item(self):
        """Get a single managed disk"""
        item = None
        result = []

        try:
            item = self.compute_client.disks.get(
                self.resource_group,
                self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [managed_disk_to_dict(item)]

        return result

    def list_items(self):
        """Get all managed disks"""
        try:
            response = self.compute_client.disks.list()
        except CloudError as exc:
            self.fail('Failed to list all items - {}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(managed_disk_to_dict(item))
        return results


def main():
    """Main module execution code path"""

    AzureRMManagedDiskFacts()

if __name__ == '__main__':
    main()
