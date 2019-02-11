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
    contains:
        id:
            description:
                - Resource id.
        name:
            description:
                - Name of the managed disk.
        location:
            description:
                - Valid Azure location.
        storage_account_type:
            description:
                - Type of storage for the managed disk
            sample: Standard_LRS
            type: str
        create_option:
            description:
                - Create option of the disk
            sample: copy
            type: str
        source_uri:
            description:
                - URI to a valid VHD file to be used or the resource ID of the managed disk to copy.
        os_type:
            description:
                - "Type of Operating System: C(linux) or C(windows)."
        disk_size_gb:
            description:
                - Size in GB of the managed disk to be created.
        managed_by:
            description:
                - Name of an existing virtual machine with which the disk is or will be associated, this VM should be in the same resource group.
        tags:
            description:
                - Tags to assign to the managed disk.
            sample: { "tag": "value" }
            type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass


# duplicated in azure_rm_managed_disk
def managed_disk_to_dict(managed_disk):
    create_data = managed_disk.creation_data
    return dict(
        id=managed_disk.id,
        name=managed_disk.name,
        location=managed_disk.location,
        tags=managed_disk.tags,
        create_option=create_data.create_option.lower(),
        source_uri=create_data.source_uri or create_data.source_resource_id,
        disk_size_gb=managed_disk.disk_size_gb,
        os_type=managed_disk.os_type.lower() if managed_disk.os_type else None,
        storage_account_type=managed_disk.sku.name if managed_disk.sku else None,
        managed_by=managed_disk.managed_by
    )


class AzureRMManagedDiskFacts(AzureRMModuleBase):
    """Utility class to get managed disk facts"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='str'
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
