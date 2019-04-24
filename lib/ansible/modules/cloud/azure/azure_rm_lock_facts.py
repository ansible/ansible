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
module: azure_rm_lock
version_added: "2.9"
short_description: Manage Azure locks.
description:
    - Create, delete an Azure lock.
options:
    name:
        description:
            - Name of the lock.
        required: true
    resource_id:
        description:
            - Id of the resource where need to manage the lock.
            - Get this via facts module.
            - Cannot be set mutal with C(resource_group).
            - Query subscription if both C(resource_id) and C(resource_group) not defined.
    resource_group:
        description:
            - Resource group name where need to manage the lock.
            - The lock is in the resource group level.
            - Cannot be set mutal with C(resource_id).
            - Query subscription if both C(resource_id) and C(resource_group) not defined.

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
'''

RETURN = '''
'''  # NOQA

from ansible.module_utils.common.dict_transformations import _camel_to_snake
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.azure_rm_common_rest import GenericRestClient

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMLockFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            resource_id=dict(type='str')
        )

        self.results = dict(
            changed=False,
            locks=[]
        )

        mutually_exclusive = [['resource_group', 'resource_id']]

        self.name = None
        self.resource_group = None
        self.resource_id = None
        self._mgmt_client = None
        self._query_parameters = {'api-version': '2016-09-01'}
        self._header_parameters = {'Content-Type': 'application/json; charset=utf-8'}

        super(AzureRMLockFacts, self).__init__(self.module_arg_spec, facts_module=True, mutually_exclusive=mutually_exclusive, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        self._mgmt_client = self.get_mgmt_svc_client(GenericRestClient, base_url=self._cloud_environment.endpoints.resource_manager)
        changed = False
        # construct scope id
        scope = self.get_scope()
        url = '/{0}/providers/Microsoft.Authorization/locks'.format(scope)
        if self.name:
            url = '{0}/{1}'.format(url, self.name)
        resp = self.list_locks(url)
        self.results = [self.to_dict(x) for x in resp]
        return self.results

    def to_dict(self, lock):
        resp = dict(
            id=lock['id'],
            name=lock['name'],
            level=_camel_to_snake(lock['level'])
        )
        if lock.get('notes'):
            resp['notes'] = lock['notes']
        if lock.get('owners'):
            resp['owners'] = [x['application_id'] for x in lock['owners']]
        return resp

    def list_locks(self, url):
        try:
            return self._mgmt_client.query(url=url,
                                           method='GET',
                                           query_parameters=self._query_parameters,
                                           header_parameters=self._header_parameters,
                                           body=None,
                                           expected_status_codes=[200],
                                           polling_timeout=None,
                                           polling_interval=None)
        except CloudError as exc:
            self.fail('Error when finding locks {0}: {1}'.format(url, exc.message))

    def get_scope(self):
        '''
        Get the resource scope of the lock management.
        '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{namespace}/{resourceType}/{resourceName}' for resources.
        '''
        if self.resource_id:
            return self.resource_id
        elif self.resource_group:
            return '/subscriptions/{0}/resourcegroups/{1}'.format(self.subscription_id, self.resource_group)
        else:
            return '/subscriptions/{0}'.format(self.subscription_id)


def main():
    AzureRMLockFacts()


if __name__ == '__main__':
    main()
