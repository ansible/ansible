#!/usr/bin/python
#
# Copyright (c) 2019 Fan Qiu, (fanqiu@microsoft.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_policydefinition_info
version_added: "2.9"
short_description: Gather Information of Azure Policy Definition
description:
    - Gather information of a specific Azure policy definition or all Azure policy definitions

options:
    name:
        description:
            - Name of the policy definition
    management_group:
        description:
            - The ID of the management group.
            - This parameter is mutually exclusive with C(built_in).
    built_in:
        description:
            - To gather all built-in policy definitions when I(built_in=true).
            - This parameter is mutually exclusive with C(management_group).
        type: bool

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
- name: List all policy definitions in subscription
  azure_rm_policydefinition_info:

- name: List all built-in policy definitions in subscription
  azure_rm_policydefinition_info:
    built_in: true

- name: List a built-in policy definition by name
  azure_rm_policydefinition_info:
    name: testpolicydefinition
'''

RETURN = '''
policydefinitions:
    description: List of policy definitions.
    returned: always
    type: list
    contains:
        description:
            description:
                - The policy definition description.
            type: str
            sample: "This policy audits Linux virtual machines that do not have the specified applications installed."
        display_name:
            description:
                - The display name of the policy definition.
            type: str
            sample: "Audit Linux VMs that do not have the specified applications installed"
        id:
            description:
                - The ID of the policy definition.
            type: str
            sample: "/providers/Microsoft.Authorization/policyDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        metadata:
            description:
                - The policy definition metadata.
            type: dict
            sample: '{
                "category": "Guest Configuration"
            }'
        mode:
            description:
                - The policy definition mode. Possible values are NotSpecified, Indexed, and All.
            type: str
            sample: "Indexed"
        name:
            description:
                - The name of the policy definition.
            type: str
            sample: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        parameters:
            description:
                - Required if a parameter is used in policy rule.
            type: dict
            sample: '{
                "effect": {
                    "allowedValues": [
                        "AuditIfNotExists",
                        "Disabled"
                    ],
                    "defaultValue": "AuditIfNotExists",
                    "metadata": {
                        "description": "Enable or disable the execution of the pol
                        "displayName": "Effect"
                    },
                    "type": "String"
                }
            }'
        policy_rule:
            description:
                - The policy rule.
            type: dict
            sample: '{
                    "if": {
                            "field": "type",
                            "in": [
                                "Microsoft.Sql/servers/databases",
                                "Microsoft.Sql/managedinstances/databases"
                            ]
                        },
                        "then": {
                            "details": {
                                "existenceCondition": {
                                    "field": "Microsoft.Security/complianceResults/resourc
                                    "in": [
                                        "NotApplicable",
                                        "OffByPolicy",
                                        "Healthy"
                                    ]
                                },
                                "name": "sqlVulnerabilityAssessment",
                                "type": "Microsoft.Security/complianceResults"
                            }
                        }
                    }'
        policy_type:
            description:
                - The type of policy definition.
                - Possible values are NotSpecified, BuiltIn, and Custom.
            type: str
            sample: "BuiltIn"
        type:
            description:
                - Resource type
            sample: "Microsoft.Authorization/policyDefinitions"
            type: str
'''

import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMPolicyDefinitionInfo(AzureRMModuleBase):
    """Configuration class for an Azure RM Policy definition resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str'
            ),
            management_group=dict(
                type='str'
            ),
            built_in=dict(
                type='bool'
            )
        )

        self.name = None
        self.management_group = None
        self.built_in = None

        mutually_exclusive = [('management_group', 'built_in')]

        self.results = dict(
            changed=False,
            policydefinitions=[]
        )

        super(AzureRMPolicyDefinitionInfo, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                          info_module=True,
                                                          supports_tags=False,
                                                          mutually_exclusive=mutually_exclusive)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        results = None

        if self.name:
            results = self.get_policy_definition()
        else:
            results = self.list_policy_definition()

        self.results['policydefinitions'] = [self.policydefinition_to_dict(x) for x in results] if results else None
        return self.results

    def get_policy_definition(self):
        result = None
        try:
            self.log("Getting the resource policy definition")
            if self.management_group:
                result = self.rm_policy_client.policy_definitions.get_at_management_group(policy_definition_name=self.name,
                                                                                          management_group_id=self.management_group)
            elif self.built_in:
                result = self.rm_policy_client.policy_definitions.get_built_in(policy_definition_name=self.name)
            else:
                result = self.rm_policy_client.policy_definitions.get(policy_definition_name=self.name)
            result = [result]
        except CloudError as exc:
            self.fail("Error getting the information for resource policy definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def list_policy_definition(self):
        result = None
        try:
            self.log("Getting the resource policy definition")
            if self.management_group:
                result = self.rm_policy_client.policy_definitions.list_by_management_group(management_group_id=self.management_group)
            elif self.built_in:
                result = self.rm_policy_client.policy_definitions.list_built_in()
            else:
                result = self.rm_policy_client.policy_definitions.list()
        except CloudError as exc:
            self.fail("Error getting the information for resource policy definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def policydefinition_to_dict(self, policy_definition):
        return policy_definition.as_dict()


def main():
    """Main execution"""
    AzureRMPolicyDefinitionInfo()


if __name__ == '__main__':
    main()
