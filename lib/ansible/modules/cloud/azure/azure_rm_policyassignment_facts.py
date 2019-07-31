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
module: azure_rm_policyassignment_facts
version_added: "2.9"
short_description: Gather Info of Policy Assignment
description:
    - Gather information of a specific policy assignment or all policy assignments.

options:
    name:
        description:
            - Name of the policy assignment.
            - This parameter is mutually exclusive with I(policy_assignment_id).
        type: str
    scope:
        description:
            - The scope of the policy assignment.
            - This parameter is required when I(name) provided.
            - For example, use C(/subscriptions/{subscription-id}/) for a subscription.
            - C(/subscriptions/{subscription-id}/resourceGroups/{resourcegroup-name}) for a resource group.
            - C(/subscriptions/{subscription-id}/resourceGroups/{resourcegroup-name}/providers/{resource-provider}/{resource-type}/{resource-name})
              for a resource.
            - C(/providers/Microsoft.Management/managementGroups/{managementGroup}) for a management group.
        type: str
    resource_group_name:
        description:
            - The name of the resource group containing the resource.
            - This parameter is required when I(resource_name) provided.
        type: str
    resource_provider_namespace:
        description:
            - The namespace of the resource provider.
            - This parameter is required when I(resource_name) provided.
        type: str
    parent_resource_path:
        description:
            - The parent resource path. Use empty string if there is C(none).
        type: str
    resource_type:
        description:
            - The resource type name.
            - This parameter is required when I(resource_name) provided.
        type: str
    resource_name:
        description:
            - The name of the resource.
        type: str
    filter:
        description:
            - The filter to apply on the operation.
            - Valid values for I(filter) are atScope() or policyDefinitionId eq {value}.
        type: str
extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
- name: list policy assignment in a subscription
  azure_rm_policyassignment_facts:

- name: list policy assignment by resource group
  azure_rm_policyassignment_facts:
    resource_group_name: myResourceGroup

- name: list policy assignment by name
  azure_rm_policyassignment_facts:
    name: SecurityCenterBuiltIn
    scope: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
'''

RETURN = '''
policyassignments:
    description:
        - List of policy assignments.
    returned: always
    type: complex
    contains:
        description:
            description:
                - The policy assignment description.
            returned: always
            type: str
            sample: "This policy assignment was automatically created by Azure Security Center"
        display_name:
            description:
                - The display name of the policy assignment.
            returned: always
            type: str
            sample: "ASC Default (subscription: f64d4ee8-be94-457d-ba26-3fa6b6506cef)"
        id:
            description:
                - The ID of the policy assignment.
            returned: always
            type: str
            sample:  "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/policyAssignments/SecurityCenterBuiltIn"
        metadata:
            description:
                - The policy assignment metadata.
            returned: always
            type: dict
            sample: {
                "assignedBy": "Security Center"
            }
        name:
            description:
                - The name of the policy assignment.
            returned: always
            type: str
            sample: "SecurityCenterBuiltIn"
        parameters:
            description:
                - Required if a parameter is used in policy rule.
            returned: always
            type: dict
            sample: {
                "effect": {
                    "allowedValues": [
                        "AuditIfNotExists",
                        "Disabled"
                    ],
                    "defaultValue": "AuditIfNotExists",
                    "metadata": {
                        "description": "Enable or disable the execution of the pol",
                        "displayName": "Effect"
                    },
                    "type": "String"
                }
            }
        policy_definition_id:
            description:
                - The ID of the policy definition or policy set definition being assigned.
            returned: always
            type: str
            sample: "/providers/Microsoft.Authorization/policySetDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        scope:
            description:
                - The scope for the policy assignment.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        sku:
            description:
                - The policy SKU.
            returned: always
            type: dict
            sample: {
                "name": "A1",
                "tier": "Standard"
            }
        type:
            description:
                - Resource type.
            returned: always
            sample: "Microsoft.Authorization/policyAssignments"
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


class AzureRMPolicyAssignmentFacts(AzureRMModuleBase):
    """Configuration class for an Azure RM Policy assignment resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str'
            ),
            scope=dict(
                type='str'
            ),
            resource_group_name=dict(
                type='str'
            ),
            resource_provider_namespace=dict(
                type='str'
            ),
            parent_resource_path=dict(
                type='str'
            ),
            resource_type=dict(
                type='str'
            ),
            resource_name=dict(
                type='str'
            ),
            filter=dict(
                type='str'
            )
        )

        self.name = None
        self.scope = None
        self.resource_group_name = None
        self.resource_provider_namespace = None
        self.parent_resource_path = None
        self.resource_type = None
        self.resource_name = None
        self.filter = None

        self.results = dict(
            changed=False,
            policyassignments=[]
        )

        super(AzureRMPolicyAssignmentFacts, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                           facts_module=True,
                                                           supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        results = None

        if self.name:
            results = self.get_policy_assignment_by_name()
        elif self.resource_group_name and self.resource_name:
            results = self.list_policy_assignments_by_resource()
        elif self.resource_group_name:
            results = self.list_policy_assignments_by_resource_group()
        else:
            results = self.list_all_policy_assignments()

        self.results['policyassignments'] = [self.policyassignment_to_dict(x) for x in results] if results else None
        return self.results

    def get_policy_assignment_by_name(self):
        result = None
        try:
            self.log("Getting the resource policy assignment by name")
            result = self.rm_policy_client.policy_assignments.get(scope=self.scope,
                                                                  policy_assignment_name=self.name)
            result = [result]
        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error getting the info for resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def list_policy_assignments_by_resource(self):
        result = None
        try:
            self.log("Getting the resource policy assignment")
            result = self.rm_policy_client.policy_assignments.list_for_resource(resource_group_name=self.resource_group_name,
                                                                                resource_provider_namespace=self.resource_provider_namespace,
                                                                                parent_resource_path=self.parent_resource_path,
                                                                                resource_type=self.resource_type,
                                                                                resource_name=self.resource_name,
                                                                                filter=self.filter)
        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error getting the info for resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def list_policy_assignments_by_resource_group(self):
        result = None
        try:
            self.log("Getting the resource policy assignment")
            result = self.rm_policy_client.policy_assignments.list_for_resource_group(resource_group_name=self.resource_group_name,
                                                                                      filter=self.filter)
        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error getting the info for resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def list_all_policy_assignments(self):
        result = None
        try:
            self.log("Getting the resource policy assignment")
            result = self.rm_policy_client.policy_assignments.list(filter=self.filter)
        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error getting the info for resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))
        return result

    def policyassignment_to_dict(self, policy_assignment):
        return policy_assignment.as_dict()


def main():
    """Main execution"""
    AzureRMPolicyAssignmentFacts()


if __name__ == '__main__':
    main()
