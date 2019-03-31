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
module: azure_rm_apimanagementusersubscription_info
version_added: '2.8'
short_description: Get UserSubscription facts.
description:
    - Get facts of UserSubscription.

options:

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@@zikalino)"

'''

EXAMPLES = '''
'''

RETURN = '''
'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
from msrestazure.azure_exceptions import CloudError


class AzureRMUserSubscriptionFacts(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str',
                required=True
            ),
            service_name=dict(
                type='str',
                required=True
            ),
            uid=dict(
                type='str',
                required=True
            ),
            $filter=dict(
                type='str'
            ),
            $top=dict(
                type='dict'
            ),
            $skip=dict(
                type='dict'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group_name = None
        self.service_name = None
        self.uid = None
        self.$filter = None
        self.$top = None
        self.$skip = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200]

        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-01-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        self.mgmt_client = None
        super(AzureRMUserSubscriptionFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        # prepare url
        self.url = ('/undefined')
        self.url = self.url.replace('{{}}', self.)

        self.results['@(Model.ModuleOperationName)'] = self.Getusersubscription()
        return self.results

    def Getusersubscription(self):
        '''
        Gets facts of the specified @(Model.ObjectName).

        :return: deserialized @(Model.ObjectName)instance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
            results['temp_item'] = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get facts for @(Model.ModuleOperationNameUpper).')

        return results


def main():
    """Main execution"""
    AzureRMUserSubscriptionFacts()


if __name__ == '__main__':
    main()
