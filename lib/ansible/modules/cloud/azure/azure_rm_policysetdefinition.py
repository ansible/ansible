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
module: azure_rm_policysetdefinition
version_added: "2.9"
short_description: Manage Azure Policy Set Definition
description:
    - Create, update and delet Azure policy set definition.

options:
    name:
        description:
            - Name of the policy set definition
        required: true
    management_group:
        description:
            - The ID of the management group.
    policy_type:
        description:
            - The type of policy set definition.
            - Possible values are C(NotSpecified), C(BuiltIn), and C(Custom).
            - Currently, user through Ansible module can only create policy set definition with custom type.
        choices:
            - custom
    display_name:
        description:
            - The display name of the policy set definition.
    description:
        description:
            - The policy set definition description.
    parameters:
        description:
            - Required if a parameter is used in policy rule.
            - JSON formatted string or a dict containing parameter definitions.
            - The parameters element of policy set definition is compatible with the policy definition
            - You can refer U(https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure) for more details.
    metadata:
        description:
            - The policy set definition metadata.
            - Defines subproperties primarily used by the Azure portal to display user-friendly information.
            - Refer U(https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure#parameter-properties) for more details.
            - Metadata in space-separated key=value pairs.
        type: dict
    policy_definitions:
        description:
            - An array of policy definition references.
            - Policy definitions in JSON format or a list containing policy rules.
            - The ID of the policy definition or policy set definition define the policy definition reference.
            - Required when creating the policy set definitions
            - You can refer U(https://docs.microsoft.com/en-us/azure/templates/Microsoft.Authorization/2018-05-01/policySetDefinitions) for more details.
    state:
        description:
            - Assert the state of the policy definition. Use C(present) to create or update a database and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
- name: Create policy set definition
  azure_rm_policysetdefinition:
    name: mytestpolicyset
    policy_definitions: '[
                            {
                                "policyDefinitionId": "/subscriptions/mySubId/providers/Microsoft.Authorization/policyDefinitions/storagePolicy"
                            }
                        ]'
    metadata:
        fortesting: yes
    policy_type: custom
    description: "This policy set is built for testing"
    display_name: "mytestpolicyset"

- name: Delete policy definition
  azure_rm_policysetdefinition:
    name: mytestpolicyset
    state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/policySetDefinitions/mytestpolicyset"
'''

import json
import os
import codecs
import base64
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
    from ansible.module_utils.urls import open_url
    from ansible.module_utils.six.moves.urllib.parse import urlparse
except ImportError:
    # This is handled in azure_rm_common
    pass

AUTO_ADDED_METADATA = ["createdBy", "createdOn", "updatedBy", "updatedOn"]


class AzureRMPolicySetDefinition(AzureRMModuleBase):
    """Configuration class for an Azure RM Policy definition resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str',
                required=True
            ),
            policy_type=dict(
                type='str',
                choices=['custom']
            ),
            display_name=dict(
                type='str'
            ),
            description=dict(
                type='str'
            ),
            policy_definitions=dict(
                type='raw'
            ),
            metadata=dict(
                type='dict'
            ),
            parameters=dict(
                type='raw'
            ),
            management_group=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.name = None
        self.policy_type = None
        self.display_name = None
        self.description = None
        self.policy_definitions = None
        self.metadata = None
        self.parameters = None
        self.management_group = None

        self.results = dict(
            changed=False,
            id=None,
        )
        self.state = None

        super(AzureRMPolicySetDefinition, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_check_mode=True,
                                                         supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        changed = False
        response = None
        results = None

        response = self.get_policy_set_definition()

        self.policy_definitions = self.load_file_string_or_dict(self.policy_definitions) if self.policy_definitions else None
        self.parameters = self.load_file_string_or_dict(self.parameters) if self.parameters else None
        self.policy_type = self.rm_policy_models.PolicyType[self.policy_type] if self.policy_type else None

        if self.state == 'present':
            if not response:
                changed = True

                policy_set_definition_instance = self.rm_policy_models.PolicySetDefinition(policy_type=self.policy_type,
                                                                                           display_name=self.display_name,
                                                                                           description=self.description,
                                                                                           metadata=self.metadata,
                                                                                           parameters=self.parameters,
                                                                                           policy_definitions=self.policy_definitions)

                if not self.check_mode:
                    response = self.create_or_update_policy_set_definition(policy_set_definition_instance)
            else:
                changed, response = self.check_update(changed=changed, policy_set_definition=response)

                if changed and not self.check_mode:
                    response = self.create_or_update_policy_set_definition(response)
            results = self.policy_set_definition_to_dict(response) if response else None
        elif response:
            if not self.check_mode:
                changed = True
                self.delete_policy_set_definition()

        self.results['changed'] = changed
        self.results['id'] = results['id'] if results else None
        return self.results

    def get_policy_set_definition(self):
        result = None
        try:
            self.log("Getting the resource policy set definition")
            if self.management_group:
                result = self.rm_policy_client.policy_set_definitions.get_at_management_group(policy_set_definition_name=self.name,
                                                                                              management_group_id=self.management_group)
            else:
                result = self.rm_policy_client.policy_set_definitions.get(policy_set_definition_name=self.name)
        except Exception as exc:
            pass
        return result

    def create_or_update_policy_set_definition(self, policy_set_definition):
        try:
            self.log("Creating or updating the resource policy set definition")
            if self.management_group:
                return self.rm_policy_client.policy_set_definitions.create_or_update_at_management_group(policy_set_definition_name=self.name,
                                                                                                         parameters=policy_set_definition,
                                                                                                         management_group_id=self.management_group)
            else:
                return self.rm_policy_client.policy_set_definitions.create_or_update(policy_set_definition_name=self.name,
                                                                                     parameters=policy_set_definition)

        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error creating or updating the resource policy set definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def check_update(self, changed, policy_set_definition):
        if self.policy_type and self.policy_type != policy_set_definition.policy_type:
            changed = True
            policy_set_definition.policy_type = self.policy_type

        if self.display_name and self.display_name != policy_set_definition.display_name:
            changed = True
            policy_set_definition.display_name = self.display_name

        if self.description and self.description != policy_set_definition.description:
            changed = True
            policy_set_definition.description = self.description

        if self.policy_definitions and self.policy_definitions != self.policy_definition_to_dict_list(policy_set_definition.policy_definitions):
            changed = True
            policy_set_definition.policy_definitions = self.policy_definitions

        if self.metadata is not None and self.update_metadata(policy_set_definition.metadata):
            changed = True
            policy_set_definition.metadata = self.metadata

        if self.parameters and self.parameters != policy_set_definition.parameters:
            changed = True
            policy_set_definition.parameters = self.parameters

        return changed, policy_set_definition

    def update_metadata(self, policy_set_definition_metadata):
        changed = False
        policy_set_definition_metadata = dict(policy_set_definition_metadata)
        for key, value in policy_set_definition_metadata.items():
            if key in AUTO_ADDED_METADATA:
                continue
            else:
                if key in self.metadata and self.metadata[key] == value:
                    continue
                else:
                    changed = True

        for key, value in self.metadata.items():
            if key in AUTO_ADDED_METADATA:
                continue
            else:
                if key in policy_set_definition_metadata and policy_set_definition_metadata[key] == value:
                    continue
                else:
                    changed = True
        return changed

    def delete_policy_set_definition(self):
        try:
            self.log("Deleting the resource policy set definition")
            if self.management_group:
                return self.rm_policy_client.policy_definitions.delete_at_management_group(policy_definition_name=self.name,
                                                                                           management_group_id=self.management_group)
            else:
                return self.rm_policy_client.policy_definitions.delete(policy_definition_name=self.name)

        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error deleting the resource policy set definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def policy_set_definition_to_dict(self, policy_set_definition):
        return policy_set_definition.as_dict()

    def policy_definition_to_dict_list(self, policy_definitions):
        policy_definitions_list = []
        for x in policy_definitions:
            policy_definition_dict = {'policyDefinitionId': x.policy_definition_id}
            if x.parameters is not None:
                policy_definition_dict['parameters'] = x.parameters
            policy_definitions_list.append(policy_definition_dict)
        return policy_definitions_list

    def load_file_string_or_dict(self, file_or_string_or_dict):
        if isinstance(file_or_string_or_dict, dict) or isinstance(file_or_string_or_dict, list):
            return file_or_string_or_dict
        return json.loads(file_or_string_or_dict)


def main():
    """Main execution"""
    AzureRMPolicySetDefinition()


if __name__ == '__main__':
    main()
