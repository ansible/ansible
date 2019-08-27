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
module: azure_rm_recoveryservicesvault_info
version_added: '2.9'
short_description: Get Vault info.
description:
  - Get info of Vault.
options:
  resource_group:
    description:
      - >-
        The name of the resource group where the recovery services vault is
        present.
    type: str
  name:
    description:
      - Resource name associated with the resource.
    type: str
extends_documentation_fragment:
  - azure
author:
  - Liu Qingyi (@smile37773)

'''

EXAMPLES = '''
- name: List of Recovery Services Resources in SubscriptionId
  azure_rm_recoveryservicesvault_info:
- name: List of Recovery Services Resources in ResourceGroup
  azure_rm_recoveryservicesvault_info:
    resource_group: myResourceGroup
- name: Get Recovery Services Resource
  azure_rm_recoveryservicesvault_info:
    resource_group: myResourceGroup
    name: myVault

'''

RETURN = '''
vaults:
  description: >-
    A list of dict results where the key is the name of the Vault and the values
    are the facts for that Vault.
  returned: always
  type: complex
  contains:
    id:
      description:
        - Resource Id represents the complete path to the resource.
      returned: always
      type: str
      sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup
      /providers/Microsoft.RecoveryServices/vaults/myVault"
    name:
      description:
        - Resource name associated with the resource.
      returned: always
      type: str
      sample: "myVault"
    e_tag:
      description:
        - Optional ETag.
      returned: always
      type: str
      sample: "W/datetime'xxxx-xx-xxT12%3A36%3A51.68Z'"
    location:
      description:
        - Resource location.
      returned: always
      type: str
      sample: "eastus"
    sku_name:
      description:
        - The Sku name.
      type: str
      sample: "Standard"
    tags:
      description:
        - Resource tags.
      type: dict
      sample: { "TestUpdatedKey": "TestUpdatedValue" }
    upgrade_details:
      description:
        - Details for upgrading vault.
      type: dict
      sample: { "status": None, "end_time_utc": None, "trigger_type": None, "start_time_utc": None, "last_updated_time_utc": None,
      "upgraded_resource_id": None, "previous_resource_id": None, "operation_id": None, "message": "myMessage" }
    provisioning_state:
        description:
          - The current state of the gallery.
        type: str
        sample: "Succeeded"

'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass


class AzureRMRecoveryServiceVaultInfo(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            )
        )

        self.resource_group = None
        self.name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200]

        self.query_parameters = {}
        self.query_parameters['api-version'] = '2016-06-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        self.mgmt_client = None
        super(AzureRMRecoveryServiceVaultInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and self.name is not None):
            self.results['vaults'] = self.get()
        elif (self.resource_group is not None):
            self.results['vaults'] = self.listbyresourcegroup()
        else:
            self.results['vaults'] = self.listbysubscriptionid()
        return self.results

    def get(self):
        response = None
        results = {}
        # prepare url
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

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return self.format_item(results) if results else None

    def listbyresourcegroup(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.RecoveryServices' +
                    '/vaults')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return [self.format_item(x) for x in results['value']] if results['value'] else []

    def listbysubscriptionid(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/providers' +
                    '/Microsoft.RecoveryServices' +
                    '/vaults')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return [self.format_item(x) for x in results['value']] if results['value'] else []

    def format_item(self, item):
        d = {
            'id': item['id'],
            'name': item['name'],
            'location': item['location'],
            'e_tag': item['etag'],
            'tags': item.get('tags'),
            'upgrade_details': item['properties'].get('upgradeDetails'),
            'sku_name': item['sku']['name'],
            'provisioning_state': item['properties']['provisioningState']
        }
        return d


def main():
    AzureRMRecoveryServiceVaultInfo()


if __name__ == '__main__':
    main()
