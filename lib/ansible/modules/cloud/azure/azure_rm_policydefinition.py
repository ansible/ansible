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
module: azure_rm_policydefinition
version_added: "2.9"
short_description: Manage Azure Policy Definition
description:
    - Create, update and delete instance of Azure policy definition.

options:
    name:
        description:
            - Name of the policy definition
        required: True
    management_group:
        description:
            - The ID of the management group.
    policy_type:
        description:
            - The type of policy definition.
            - Possible value is C(Custom).
        choices:
            - custom
    mode:
        description:
            - The policy definition mode.
            - Possible values are C(Indexed) and C(All).
            - "I(mode=all) determines all resource types will be evaluated for a policy 
              and I(mode=indexed) means the policy only evaluate resource types that support tags and location."
            - Refer U(https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure#mode) for more details.
        choices:
            - indexed
            - all
    display_name:
        description:
            - The display name of the policy definition.
    description:
        description:
            - The policy definition description.
    policy_rule:
        description:
            - The policy rule.
            - Policy rules in JSON format, or a path or url to a file containing JSON rules.
            - Refer U(https://docs.microsoft.com/en-us/azure/templates/microsoft.authorization/2018-05-01/policydefinitions) for more details.
            - This link U(https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure) can be helpful.
    parameters:
        description:
            - Required if a parameter is used in policy rule.
            - JSON formatted string or a path to a file or url with parameter definitions.
            - Refer U(https://docs.microsoft.com/en-us/azure/templates/microsoft.authorization/2018-05-01/policydefinitions) for more details.
    metadata:
        description:
            - The policy definition metadata.
            - Defines subproperties primarily used by the Azure portal to display user-friendly information.
            - Refer U(https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure#parameter-properties) for more details.
            - Metadata in space-separated key=value pairs.
        type: dict
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
- name: Create policy definition
  azure_rm_policydefinition:
    name: mytestpolicy
    policy_rule: "https://xxxxxxxx.blob.core.windows.net/templates/test_policy.json"
    metadata:
        fortesting: yes
    mode: all
    policy_type: custom
    description: "This policy is built for testing"
    display_name: "mytestpolicy"

- name: Create policy definition
  azure_rm_policydefinition:
    name: mytestpolicy
    policy_rule: '{
                    "if":
                    {
                        "field": "type",
                        "equals": "Microsoft.Storage/storageAccounts/write"
                    },
                    "then":
                    {
                        "effect": "deny"
                    }
                  }'
    metadata:
        fortesting: yes
    mode: all
    policy_type: custom
    description: "This policy is built for testing"
    display_name: "mytestpolicy"

- name: Delete policy definition
  azure_rm_policydefinition:
    name: test-policy
    state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/policyDefinitions/mytestpolicy"
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


class AzureRMPolicyDefinition(AzureRMModuleBase):
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
            mode=dict(
                type='str',
                choices=['all', 'indexed']
            ),
            display_name=dict(
                type='str'
            ),
            description=dict(
                type='str'
            ),
            policy_rule=dict(
                type='str'
            ),
            metadata=dict(
                type='dict'
            ),
            parameters=dict(
                type='str'
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
        self.mode = None
        self.display_name = None
        self.description = None
        self.policy_rule = None
        self.metadata = None
        self.parameters = None
        self.management_group = None

        self.results = dict(
            changed=False,
            id=None,
        )
        self.state = None

        super(AzureRMPolicyDefinition, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True,
                                                      supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        changed = False
        response = None
        results = None

        response = self.get_policy_definition()

        self.policy_rule = self.load_file_string_or_url(self.policy_rule) if self.policy_rule else None
        self.parameters = self.load_file_string_or_url(self.parameters) if self.parameters else None
        self.policy_type = self.rm_policy_models.PolicyType[self.policy_type] if self.policy_type else None
        self.mode = self.rm_policy_models.PolicyMode[self.mode] if self.mode else None

        if self.state == 'present':
            if not response:
                changed = True

                policy_definition_instance = self.rm_policy_models.PolicyDefinition(policy_type=self.policy_type,
                                                                                    mode=self.mode,
                                                                                    display_name=self.display_name,
                                                                                    description=self.description,
                                                                                    policy_rule=self.policy_rule,
                                                                                    metadata=self.metadata,
                                                                                    parameters=self.parameters)

                if not self.check_mode:
                    response = self.create_or_update_policy_definition(policy_definition_instance)
            else:
                changed, response = self.check_update(changed=changed, policy_definition=response)

                if changed and not self.check_mode:
                    response = self.create_or_update_policy_definition(response)
            results = self.policy_definition_to_dict(response) if response else None
        elif response:
            if not self.check_mode:
                changed = True
                self.delete_policy_definition()

        self.results['changed'] = changed
        self.results['id'] = results['id'] if results else None
        return self.results

    def get_policy_definition(self):
        result = None
        try:
            self.log("Getting the resource policy definition")
            if self.management_group:
                result = self.rm_policy_client.policy_definitions.get_at_management_group(policy_definition_name=self.name,
                                                                                          management_group_id=self.management_group)
            else:
                result = self.rm_policy_client.policy_definitions.get(policy_definition_name=self.name)
        except Exception as exc:
            pass
        return result

    def create_or_update_policy_definition(self, policy_definition):
        try:
            self.log("Creating or updating the resource policy definition")
            if self.management_group:
                return self.rm_policy_client.policy_definitions.create_or_update_at_management_group(policy_definition_name=self.name,
                                                                                                     parameters=policy_definition,
                                                                                                     management_group_id=self.management_group)
            else:
                return self.rm_policy_client.policy_definitions.create_or_update(policy_definition_name=self.name,
                                                                                 parameters=policy_definition)

        except CloudError as exc:
            self.fail("Error creating or updating the resource policy definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def check_update(self, changed, policy_definition):
        if self.policy_type and self.policy_type != policy_definition.policy_type:
            changed = True
            policy_definition.policy_type = self.policy_type

        if self.mode and self.mode != policy_definition.mode:
            changed = True
            policy_definition.mode = self.mode

        if self.display_name and self.display_name != policy_definition.display_name:
            changed = True
            policy_definition.display_name = self.display_name

        if self.description and self.description != policy_definition.description:
            changed = True
            policy_definition.description = self.description

        if self.policy_rule and self.policy_rule != policy_definition.policy_rule:
            changed = True
            policy_definition.policy_rule = self.policy_rule

        if self.metadata and self.update_metadata(policy_definition.metadata):
            changed = True
            policy_definition.metadata = self.metadata

        if self.parameters and self.parameters != policy_definition.parameters:
            changed = True
            policy_definition.parameters = self.parameters

        return changed, policy_definition

    def update_metadata(self, policy_definition_metadata):
        changed = False
        policy_definition_metadata = dict(policy_definition_metadata)
        for key, value in policy_definition_metadata.items():
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
                if key in policy_definition_metadata and policy_definition_metadata[key] == value:
                    continue
                else:
                    changed = True
        return changed

    def delete_policy_definition(self):
        try:
            self.log("Deleting the resource policy definition")
            if self.management_group:
                return self.rm_policy_client.policy_definitions.delete_at_management_group(policy_definition_name=self.name,
                                                                                           management_group_id=self.management_group)
            else:
                return self.rm_policy_client.policy_definitions.delete(policy_definition_name=self.name)

        except CloudError as exc:
            self.fail("Error deleting the resource policy definition {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def policy_definition_to_dict(self, policy_definition):
        return policy_definition.as_dict()

    def get_file_json(self, file_path):
        try:
            content = self.read_file_content(file_path)
            return json.loads(content)
        except Exception as exc:
            self.fail("Failed to parse {0} with exception:\n    {1}".format(file_path, str(exc)))

    def read_file_content(self, file_path, allow_binary=False):
        from codecs import open as codecs_open
        # Note, always put 'utf-8-sig' first, so that BOM in WinOS won't cause trouble.
        for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be']:
            try:
                with codecs_open(file_path, encoding=encoding) as f:
                    self.log("Attempting to read file {0} as {1}".format(file_path, encoding))
                    return f.read()
            except (UnicodeError, UnicodeDecodeError):
                pass

        if allow_binary:
            try:
                with open(file_path, 'rb') as input_file:
                    self.log("Attempting to read file {0} as binary".format(file_path))
                    return base64.b64encode(input_file.read()).decode("utf-8")
            except Exception:
                pass
        self.fail("Failed to decode file {0} - unknown decoding".format(file_path))

    def load_file_string_or_url(self, file_or_string_or_url):
        url = urlparse(file_or_string_or_url)
        if url.scheme == 'http' or url.scheme == 'https' or url.scheme == 'file':
            response = open_url(file_or_string_or_url)
            reader = codecs.getreader('utf-8')
            result = json.load(reader(response))
            response.close()
            return result
        if os.path.exists(file_or_string_or_url):
            return self.get_file_json(file_or_string_or_url)
        return json.loads(file_or_string_or_url)


def main():
    """Main execution"""
    AzureRMPolicyDefinition()


if __name__ == '__main__':
    main()
