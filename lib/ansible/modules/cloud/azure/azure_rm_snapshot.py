#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_snapshot
version_added: '2.9'
short_description: Manage Azure Snapshot instance.
description:
  - 'Create, update and delete instance of Azure Snapshot.'
options:
  resource_group:
    description:
      - The name of the resource group.
    required: true
    type: str
  name:
    description:
      - Resource name
    type: str
  location:
    description:
      - Resource location
    type: str
  sku:
    description:
      - SKU
    type: dict
    suboptions:
      name:
        description:
          - The sku name.
        type: str
        choices:
          - Standard_LRS
          - Premium_LRS
          - Standard_ZRS
      tier:
        description:
          - The sku tier.
        type: str
  os_type:
    description:
      - The Operating System type.
    type: str
    choices:
      - Linux
      - Windows
  creation_data:
    description:
      - >-
        Disk source information. CreationData information cannot be changed
        after the disk has been created.
    type: dict
    suboptions:
      create_option:
        description:
          - This enumerates the possible sources of a disk's creation.
        type: str
        default: Import
        choices:
          - Import
      source_uri:
        description:
          - >-
            If createOption is Import, this is the URI of a blob to be imported
            into a managed disk.
        type: str
  state:
    description:
      - Assert the state of the Snapshot.
      - >-
        Use C(present) to create or update an Snapshot and C(absent) to delete
        it.
    default: present
    type: str
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
  - azure_tags
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: Create a snapshot by importing an unmanaged blob from the same subscription.
  azure_rm_snapshot:
    resource_group: myResourceGroup
    name: mySnapshot
    location: eastus
    creation_data:
      create_option: Import
      source_uri: 'https://mystorageaccount.blob.core.windows.net/osimages/osimage.vhd'
'''

RETURN = '''
id:
  description:
    - Resource Id
  returned: always
  type: str
  sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/snapshots/mySnapshot
'''

import time
import json
import re
from ansible.module_utils.azure_rm_common_ext import AzureRMModuleBaseExt
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # this is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMSnapshots(AzureRMModuleBaseExt):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                updatable=False,
                disposition='resourceGroupName',
                required=True
            ),
            name=dict(
                type='str',
                updatable=False,
                disposition='snapshotName',
                required=True
            ),
            location=dict(
                type='str',
                updatable=False,
                disposition='/'
            ),
            sku=dict(
                type='dict',
                disposition='/',
                options=dict(
                    name=dict(
                        type='str',
                        choices=['Standard_LRS',
                                 'Premium_LRS',
                                 'Standard_ZRS']
                    ),
                    tier=dict(
                        type='str'
                    )
                )
            ),
            os_type=dict(
                type='str',
                disposition='/properties/osType',
                choices=['Windows',
                         'Linux']
            ),
            creation_data=dict(
                type='dict',
                disposition='/properties/creationData',
                options=dict(
                    create_option=dict(
                        type='str',
                        disposition='createOption',
                        choices=['Import'],
                        default='Import'
                    ),
                    source_uri=dict(
                        type='str',
                        disposition='sourceUri'
                    )
                )
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.id = None
        self.name = None
        self.type = None
        self.managed_by = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 201, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-09-30'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMSnapshots, self).__init__(derived_arg_spec=self.module_arg_spec,
                                               supports_check_mode=True,
                                               supports_tags=True)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.body[key] = kwargs[key]

        self.inflate_parameters(self.module_arg_spec, self.body, 0)

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if 'location' not in self.body:
            self.body['location'] = resource_group.location

        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Compute' +
                    '/snapshots' +
                    '/{{ snapshot_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ snapshot_name }}', self.name)

        old_response = self.get_resource()

        if not old_response:
            self.log("Snapshot instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('Snapshot instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            else:
                modifiers = {}
                self.create_compare_modifiers(self.module_arg_spec, '', modifiers)
                self.results['modifiers'] = modifiers
                self.results['compare'] = []
                self.create_compare_modifiers(self.module_arg_spec, '', modifiers)
                if not self.default_compare(modifiers, self.body, old_response, '', self.results):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the Snapshot instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results
            response = self.create_update_resource()
            self.results['changed'] = True
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('Snapshot instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_resource()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_resource():
                time.sleep(20)
        else:
            self.log('Snapshot instance unchanged')
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_resource(self):
        # self.log('Creating / Updating the Snapshot instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(url=self.url,
                                              method='PUT',
                                              query_parameters=self.query_parameters,
                                              header_parameters=self.header_parameters,
                                              body=self.body,
                                              expected_status_codes=self.status_code,
                                              polling_timeout=600,
                                              polling_interval=30)
        except CloudError as exc:
            self.log('Error attempting to create the Snapshot instance.')
            self.fail('Error creating the Snapshot instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_resource(self):
        # self.log('Deleting the Snapshot instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(url=self.url,
                                              method='DELETE',
                                              query_parameters=self.query_parameters,
                                              header_parameters=self.header_parameters,
                                              body=None,
                                              expected_status_codes=self.status_code,
                                              polling_timeout=600,
                                              polling_interval=30)
        except CloudError as e:
            self.log('Error attempting to delete the Snapshot instance.')
            self.fail('Error deleting the Snapshot instance: {0}'.format(str(e)))

        return True

    def get_resource(self):
        # self.log('Checking if the Snapshot instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(url=self.url,
                                              method='GET',
                                              query_parameters=self.query_parameters,
                                              header_parameters=self.header_parameters,
                                              body=None,
                                              expected_status_codes=self.status_code,
                                              polling_timeout=600,
                                              polling_interval=30)
            found = True
            self.log("Response : {0}".format(response))
            # self.log("Snapshot instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Snapshot instance.')
        if found is True:
            return response

        return False


def main():
    AzureRMSnapshots()


if __name__ == '__main__':
    main()
