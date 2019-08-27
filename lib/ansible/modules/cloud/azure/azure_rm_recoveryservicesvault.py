#!/usr/bin/python
#
# Copyright (c) 2019 Liu Qingyi, (@smile37773)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_recoveryservicesvault
version_added: '2.9'
short_description: Manage Azure Vault instance.
description:
  - 'Create, update and delete instance of Azure Vault.'
options:
  resource_group:
    description:
      - >-
        The name of the resource group where the recovery services vault is
        present.
    required: true
    type: str
  name:
    description:
      - Resource name associated with the resource.
    required: true
    type: str
  location:
    description:
      - Resource location.
    type: str
  upgrade_details:
    description:
      - Details for upgrading vault.
    type: dict
    suboptions:
      operation_id:
        description:
          - ID of the vault upgrade operation.
        type: str
      start_time_utc:
        description:
          - UTC time at which the upgrade operation has started.
        type: str
      last_updated_time_utc:
        description:
          - UTC time at which the upgrade operation status was last updated.
        type: str
      end_time_utc:
        description:
          - UTC time at which the upgrade operation has ended.
        type: str
      status:
        description:
          - Status of the vault upgrade operation.
        type: dict
        suboptions:
          failed:
            description:
              - This is failed.
            type: str
          in_progress:
            description:
              - This is in_progress.
            type: str
          unknown:
            description:
              - This is unknown.
            type: str
          upgraded:
            description:
              - This is upgraded.
            type: str
      message:
        description:
          - >-
            Message to the user containing information about the upgrade
            operation.
        type: str
      trigger_type:
        description:
          - The way the vault upgrade was triggered.
        type: dict
        suboptions:
          forced_upgrade:
            description:
              - This is forced_upgrade.
            type: str
          user_triggered:
            description:
              - This is user_triggered.
            type: str
      upgraded_resource_id:
        description:
          - Resource ID of the upgraded vault.
        type: str
      previous_resource_id:
        description:
          - Resource ID of the vault before the upgrade.
        type: str
  sku_name:
    description:
      - The Sku name.
    type: str
    choices:
      - Standard
      - RS0
  state:
    description:
      - Assert the state of the Vault.
      - Use C(present) to create or update an Vault and C(absent) to delete it.
    default: present
    type: str
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
  - azure_tags
author:
  - Liu Qingyi (@smile37773)

'''

EXAMPLES = '''
- name: Create Recovery Services vault
  azure_rm_recoveryservicesvault:
    resource_group: myResourceGroup
    name: myVault
    sku_name: Standard
    location: westus
- name: Delete Recovery Services Vault
  azure_rm_recoveryservicesvault:
    resource_group: myResourceGroup
    name: myVault
    state: absent

'''

RETURN = '''
id:
  description:
    - Resource Id represents the complete path to the resource.
  returned: always
  type: str
  sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup
  /providers/Microsoft.RecoveryServices/vaults/myVault"

'''

import time
import json
import re
from ansible.module_utils.azure_rm_common_ext import AzureRMModuleBaseExt
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMRecoveryServiceVault(AzureRMModuleBaseExt):
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
                disposition='vaultName',
                required=True
            ),
            location=dict(
                type='str',
                updatable=False,
                disposition='/'
            ),
            upgrade_details=dict(
                type='dict',
                disposition='/properties/upgradeDetails/*',
                options=dict(
                    operation_id=dict(
                        type='str',
                        disposition='operationId'
                    ),
                    start_time_utc=dict(
                        type='str',
                        disposition='startTimeUtc'
                    ),
                    last_updated_time_utc=dict(
                        type='str',
                        disposition='lastUpdatedTimeUtc'
                    ),
                    end_time_utc=dict(
                        type='str',
                        disposition='endTimeUtc'
                    ),
                    status=dict(
                        type='dict',
                        disposition='status/*',
                        options=dict(
                            failed=dict(type='str', disposition='Failed'),
                            in_progress=dict(type='str', disposition='InProgress'),
                            unknown=dict(type='str', disposition='Unknown'),
                            upgraded=dict(type='str', disposition='Upgraded')
                        )
                    ),
                    message=dict(
                        type='str',
                        disposition='message'
                    ),
                    trigger_type=dict(
                        type='dict',
                        disposition='triggerType/*',
                        options=dict(
                            forced_upgrade=dict(type='str', disposition='ForcedUpgrade'),
                            user_triggered=dict(type='str', disposition='UserTriggered')
                        )
                    ),
                    upgraded_resource_id=dict(
                        type='str',
                        disposition='upgradedResourceId'
                    ),
                    previous_resource_id=dict(
                        type='str',
                        disposition='previousResourceId'
                    ),
                )
            ),
            sku_name=dict(
                type='str',
                disposition='/sku/name',
                choices=['Standard',
                         'RS0']
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 201, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2016-06-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMRecoveryServiceVault, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                          supports_check_mode=True,
                                                          supports_tags=True)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.body[key] = kwargs[key]

        self.inflate_parameters(self.module_arg_spec, self.body, 0)

        if 'properties' not in self.body:
            self.body['properties'] = {}
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
                    '/Microsoft.RecoveryServices' +
                    '/vaults' +
                    '/{{ vault_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ vault_name }}', self.name)

        old_response = self.get_resource()

        if not old_response:
            self.log("Vault instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('Vault instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            else:
                modifiers = {}
                self.create_compare_modifiers(self.module_arg_spec, '', modifiers)
                self.results['modifiers'] = modifiers
                self.results['compare'] = []
                if not self.default_compare(modifiers, self.body, old_response, '', self.results):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the Vault instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_resource()

            # if not old_response:
            self.results['changed'] = True
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('Vault instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_resource()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_resource():
                time.sleep(20)
        else:
            self.log('Vault instance unchanged')
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_resource(self):
        # self.log('Creating / Updating the Vault instance {0}'.format(self.))

        try:
            response = self.mgmt_client.query(self.url,
                                              'PUT',
                                              self.query_parameters,
                                              self.header_parameters,
                                              self.body,
                                              self.status_code,
                                              600,
                                              30)
        except CloudError as exc:
            self.log('Error attempting to create the Vault instance.')
            self.fail('Error creating the Vault instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_resource(self):
        # self.log('Deleting the Vault instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
        except CloudError as e:
            self.log('Error attempting to delete the Vault instance.')
            self.fail('Error deleting the Vault instance: {0}'.format(str(e)))

        return True

    def get_resource(self):
        # self.log('Checking if the Vault instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            found = True
            self.log("Response : {0}".format(response))
            # self.log("Vault instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Vault instance.')
        if found is True:
            return response

        return False


def main():
    AzureRMRecoveryServiceVault()


if __name__ == '__main__':
    main()
