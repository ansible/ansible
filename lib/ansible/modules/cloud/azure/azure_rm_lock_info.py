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
module: azure_rm_lock_info
version_added: "2.9"
short_description: Manage Azure locks
description:
    - Create, delete an Azure lock.
options:
    name:
        description:
            - Name of the lock.
        type: str
        required: true
    managed_resource_id:
        description:
            - ID of the resource where need to manage the lock.
            - Get this via facts module.
            - Cannot be set mutual with I(resource_group).
            - Manage subscription if both I(managed_resource_id) and I(resource_group) not defined.
            - "'/subscriptions/{subscriptionId}' for subscriptions."
            - "'/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups."
            - "'/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{namespace}/{resourceType}/{resourceName}' for resources."
            - Can get all locks with 'child scope' for this resource, use I(managed_resource_id) in response for further management.
        type: str
    resource_group:
        description:
            - Resource group name where need to manage the lock.
            - The lock is in the resource group level.
            - Cannot be set mutual with I(managed_resource_id).
            - Query subscription if both I(managed_resource_id) and I(resource_group) not defined.
            - Can get all locks with 'child scope' in this resource group, use the I(managed_resource_id) in response for further management.
        type: str

extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Get myLock details of myVM
  azure_rm_lock_info:
    name: myLock
    managed_resource_id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/Microsoft.Compute/virtualMachines/myVM

- name: List locks of myVM
  azure_rm_lock_info:
    managed_resource_id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/Microsoft.Compute/virtualMachines/myVM

- name: List locks of myResourceGroup
  azure_rm_lock_info:
    resource_group: myResourceGroup

- name: List locks of myResourceGroup
  azure_rm_lock_info:
    managed_resource_id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup

- name: List locks of mySubscription
  azure_rm_lock_info:

- name: List locks of mySubscription
  azure_rm_lock_info:
    managed_resource_id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
'''

RETURN = '''
locks:
    description:
        - List of locks dicts.
    returned: always
    type: complex
    contains:
        id:
            description:
                - ID of the Lock.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Authorization/locks/myLock"
        name:
            description:
                - Name of the lock.
            returned: always
            type: str
            sample: myLock
        level:
            description:
                - Type level of the lock.
            returned: always
            type: str
            sample: can_not_delete
        notes:
            description:
                - Notes of the lock added by creator.
            returned: always
            type: str
            sample: "This is a lock"
'''  # NOQA

import json
import re
from ansible.module_utils.common.dict_transformations import _camel_to_snake
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMLockInfo(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            managed_resource_id=dict(type='str')
        )

        self.results = dict(
            changed=False,
            locks=[]
        )

        mutually_exclusive = [['resource_group', 'managed_resource_id']]

        self.name = None
        self.resource_group = None
        self.managed_resource_id = None
        self._mgmt_client = None
        self._query_parameters = {'api-version': '2016-09-01'}
        self._header_parameters = {'Content-Type': 'application/json; charset=utf-8'}

        super(AzureRMLockInfo, self).__init__(self.module_arg_spec, facts_module=True, mutually_exclusive=mutually_exclusive, supports_tags=False)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_lock_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_lock_facts' module has been renamed to 'azure_rm_lock_info'", version='2.13')

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        self._mgmt_client = self.get_mgmt_svc_client(GenericRestClient, base_url=self._cloud_environment.endpoints.resource_manager)
        changed = False
        # construct scope id
        scope = self.get_scope()
        url = '/{0}/providers/Microsoft.Authorization/locks'.format(scope)
        if self.name:
            url = '{0}/{1}'.format(url, self.name)
        locks = self.list_locks(url)
        resp = locks.get('value') if 'value' in locks else [locks]
        self.results['locks'] = [self.to_dict(x) for x in resp]
        return self.results

    def to_dict(self, lock):
        resp = dict(
            id=lock['id'],
            name=lock['name'],
            level=_camel_to_snake(lock['properties']['level']),
            managed_resource_id=re.sub('/providers/Microsoft.Authorization/locks/.+', '', lock['id'])
        )
        if lock['properties'].get('notes'):
            resp['notes'] = lock['properties']['notes']
        if lock['properties'].get('owners'):
            resp['owners'] = [x['application_id'] for x in lock['properties']['owners']]
        return resp

    def list_locks(self, url):
        try:
            resp = self._mgmt_client.query(url=url,
                                           method='GET',
                                           query_parameters=self._query_parameters,
                                           header_parameters=self._header_parameters,
                                           body=None,
                                           expected_status_codes=[200],
                                           polling_timeout=None,
                                           polling_interval=None)
            return json.loads(resp.text)
        except CloudError as exc:
            self.fail('Error when finding locks {0}: {1}'.format(url, exc.message))

    def get_scope(self):
        '''
        Get the resource scope of the lock management.
        '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{namespace}/{resourceType}/{resourceName}' for resources.
        '''
        if self.managed_resource_id:
            return self.managed_resource_id
        elif self.resource_group:
            return '/subscriptions/{0}/resourcegroups/{1}'.format(self.subscription_id, self.resource_group)
        else:
            return '/subscriptions/{0}'.format(self.subscription_id)


def main():
    AzureRMLockInfo()


if __name__ == '__main__':
    main()
