#!/usr/bin/python
#
# Copyright (c) 2016 Amanvir Mundra, <@amanvirmundra>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: azure_rm_storageaccount_keys

version_added: "2.6"

short_description: Retrieve Azure Storage Account Keys.

description:
    - Retrive keys for a Storage Account.

options:
    resource_group:
        description:
            - This is the name of the resource group for which you want to retrieve Keys
        required: true
        default: null
    name:
        description:
            - Name of the Storage Account instance.
        required: true
        default: null
        aliases:
            - resource_group_name

extends_documentation_fragment:
    - azure

author:
    - Amanvir Mundra (@amanvirmundra)

'''

EXAMPLES = '''
- name: Get Storage account keys
  azure_rm_storageaccount_keys:
    resource_group: resource_group
    name: name
'''

RETURN = '''
keys:
    description: Dictionary of Keys associated with the Storage Account
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMStorageAccountKeys(AzureRMModuleBase):
    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', aliases=['resource_group_name'], required=True),
            name=dict(type='str', required=True)
        )
        self.results = dict(
            changed=False,
            keys = dict()
            )
        self.resource_group = None
        self.name = None

        super(AzureRMStorageAccountKeys, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        try:
            account_keys = self.storage_client.storage_accounts.list_keys(self.resource_group, self.name)
        except CloudError:
            pass

        keys = dict()
        for key in account_keys.keys:
            keys[key.key_name] = key.value

        self.results['keys'] = keys

        return self.results


def main():
    AzureRMStorageAccountKeys()


if __name__ == '__main__':
    main()
