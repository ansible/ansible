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
module: azure_rm_devtestlabpolicy_facts
version_added: "2.8"
short_description: Get Azure DTL Policy facts.
description:
    - Get facts of Azure DTL Policy.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    lab_name:
        description:
            - The name of the lab.
        required: True
    policy_set_name:
        description:
            - The name of the policy set.
        required: True
    name:
        description:
            - The name of the policy.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Policy
    azure_rm_devtestlabpolicy_facts:
      resource_group: myResourceGroup
      lab_name: myLab
      policy_set_name: myPolicySet
      name: myPolicy
'''

RETURN = '''
policies:
    description: A list of dictionaries containing facts for Policy.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the artifact source.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DevTestLab/labs/myLab/po
                     licysets/myPolicySet/policies/myPolicy"
        resource_group:
            description:
                - Name of the resource group.
            returned: always
            type: str
            sample: myResourceGroup
        lab_name:
            description:
                - Name of the lab.
            returned: always
            type: str
            sample: myLab
        name:
            description:
                - The name of the artifact source.
            returned: always
            type: str
            sample: myArtifactSource
        fact_name:
            description:
                - The name of the policy fact.
            returned: always
            type: str
            sample: UserOwnedLabVmCount
        evaluator_type:
            description:
                - Evaluator type for policy fact.
            returned: always
            type: str
            sample: MaxValuePolicy
        threshold:
            description:
                - Fact's threshold.
            returned: always
            type: str
            sample: 5
        tags:
            description:
                - The tags of the resource.
            returned: always
            type: complex
            sample: "{ 'MyTag': 'MyValue' }"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDtlPolicyFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            lab_name=dict(
                type='str',
                required=True
            ),
            policy_set_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.mgmt_client = None
        self.resource_group = None
        self.lab_name = None
        self.policy_set_name = None
        self.name = None
        self.tags = None
        super(AzureRMDtlPolicyFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name:
            self.results['policies'] = self.get()
        else:
            self.results['policies'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.policies.get(resource_group_name=self.resource_group,
                                                     lab_name=self.lab_name,
                                                     policy_set_name=self.policy_set_name,
                                                     name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Policy.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.policies.list(resource_group_name=self.resource_group,
                                                      lab_name=self.lab_name,
                                                      policy_set_name=self.policy_set_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Policy.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'policy_set_name': self.policy_set_name,
            'name': d.get('name'),
            'id': d.get('id'),
            'tags': d.get('tags'),
            'status': d.get('status'),
            'threshold': d.get('threshold'),
            'fact_name': d.get('fact_name'),
            'evaluator_type': d.get('evaluator_type')
        }
        return d


def main():
    AzureRMDtlPolicyFacts()


if __name__ == '__main__':
    main()
