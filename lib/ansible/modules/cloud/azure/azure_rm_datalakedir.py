#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Jose Angel Munoz, (@imjoseangel)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: azure_rm_datalakedir
version_added: 2.9
short_description: Setup Azure Datalake dirs
description:
    - Create or delete an dir within a given directory in a Datalake.
options:
    store_name:
        description:
            - Name of the Datalake.
        required: true
        type: str
    dir_name:
        description:
            - Name of the Datalake directory.
        required: true
        type: str
    recursive:
        description: Specifies whether to delete dirs recursively or not
        type: bool
        default: false
    state:
        description:
            - Assert the state of the dir. Use C(present) to create a directory and C(absent) to delete it.
        type: str
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - Jose Angel Munoz (@imjoseangel)

'''

EXAMPLES = '''
    - name: Create directory /raw
      azure_rm_datalakedir:
        dir_name: /raw
        store_name: mydatalake

    - name: Delete directory /raw
      azure_rm_datalakedir:
        dir_name: /raw
        store_name: mydatalake
        state: absent
'''

RETURN = '''
dir_exists: Returns if dir exists before the operation
  description:
  returned: dir exists
  type: str
  sample: true
directory:
  description: Directory created or deleted
  returned: created or deleted
  type: str
  sample: /raw
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.datalake.store import core, lib
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Delete = range(3)


class AzureRMDataLakes(AzureRMModuleBase):
    """Configuration class for an Azure RM Application Gateway resource"""
    def __init__(self):
        self.module_arg_spec = dict(store_name=dict(type='str', required=True),
                                    dir_name=dict(type='path', required=True),
                                    recursive=dict(type='bool'),
                                    state=dict(type='str',
                                               default='present',
                                               choices=['present', 'absent']))

        self.module_required_if = [['state', 'absent', ['recursive']]]

        self.dir_name = None
        self.store_name = None
        self.recursive = None
        self.resource = 'https://datalake.azure.net/'
        self.state = None
        self.results = dict(changed=False)

        super(AzureRMDataLakes,
              self).__init__(derived_arg_spec=self.module_arg_spec,
                             supports_check_mode=True,
                             supports_tags=False,
                             required_if=self.module_required_if)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        results = dict()
        changed = False

        # Access to the data lake
        adl_creds = self.get_adlcreds()

        try:

            results['dir_exists'] = self.get_dir(adl_creds)

            # Key exists and will be deleted
            if self.state == 'absent':
                changed = True

        except TypeError:
            # AC: doesn't exist
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if not self.check_mode:

            # Create Dir
            if self.state == 'present' and changed:
                results['directory'] = self.create_dir(adl_creds)
                self.results['state'] = results
                self.results['state']['status'] = 'Created'
            # Delete Dir
            elif self.state == 'absent' and changed:
                results['directory'] = self.delete_dir(adl_creds)
                self.results['state'] = results
                self.results['state']['status'] = 'Deleted'
        else:
            if self.state == 'present' and changed:
                self.results['state']['status'] = 'Created'
            elif self.state == 'absent' and changed:
                self.results['state']['status'] = 'Deleted'

        return self.results

    def get_adlcreds(self):

        if 'client_id' not in self.credentials or 'secret' not in self.credentials or self.credentials[  # noqa: E501
                'client_id'] is None or self.credentials['secret'] is None:
            self.fail(
                'Please specify client_id, secret and tenant to access azure Data Lake.'  # noqa: E501
            )

        tenant = self.credentials.get('tenant')
        if not self.credentials['tenant']:
            tenant = "common"

        adl_creds = lib.auth(tenant_id=tenant,
                             client_secret=self.credentials['secret'],
                             client_id=self.credentials['client_id'],
                             resource=self.resource)

        adls_accountname = self.store_name
        adls_filesystemclient = core.AzureDLFileSystem(
            adl_creds, store_name=adls_accountname)

        return adls_filesystemclient

    def get_dir(self, creds):

        dir_status = creds.exists(self.dir_name)

        if dir_status:
            return dir_status

        raise TypeError

    def create_dir(self, creds):

        try:
            creds.mkdir(self.dir_name)

        except CloudError as exc:
            self.log(
                'Error attempting to update dir on the Data lake instance.')
            self.fail("Error creating Data Lake dirs: {0}".format(str(exc)))

        return self.dir_name

    def delete_dir(self, creds):
        try:
            creds.rm(self.dir_name, recursive=self.recursive)

        except CloudError as exc:
            self.log(
                'Error attempting to remove dir on the Data lake instance.')
            self.fail("Error removing Data Lake dir: {0}".format(str(exc)))

        except PermissionError:
            self.log(
                'Error attempting to remove dir on the Data lake instance.')
            self.fail(
                "Check permissions and turn on recursive to force directory deletion"  # noqa: E501
            )

        return self.dir_name


def main():
    """Main execution"""
    AzureRMDataLakes()


if __name__ == '__main__':
    main()
