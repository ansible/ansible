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
module: azure_rm_policyassignment
version_added: "2.9"
short_description: Manage Azure policy assignment instance
description:
    - Create, update and delete instance of Azure policy assignment.

options:
    name:
        description:
            - Name of the policy assignment.
        type: str
    scope:
        description:
            - The scope of the policy assignment to create.
            - For example, use C(/subscriptions/{subscription-id}/) for subscription.
            - C(/subscriptions/{subscription-id}/resourceGroups/{resource-group-name}) for resource group.
            - C(/subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/providers/{resource-provider}/{resource-type}/{resource-name}) for resource.
            - C(/providers/Microsoft.Management/managementGroups/{managementGroup}) for a management group.
        type: str
    state:
        description:
            - State of the policy assignment.
            - Use C(present) to create or update a policy assignment and C(absent) to delete it.
        type: str
        default: present
        choices:
            - absent
            - present
    policy_definition:
        description:
            - The ID or name of the policy definition or policy set definition being assigned.
            - It can also be a dict contains C(name), C(types) and optional C(subscription_id).
            - The types of the I(policy_definition) could be policyDefinitions or policySetDefinitions.
        type: raw
    display_name:
        description:
            - The display name of the policy assignment.
        type: str
    not_scopes:
        description:
            - The policy's excluded scopes.
        type: list
    parameters:
        description:
            - Required if a parameter is used in policy rule.
            - JSON formatted string or a path to a file or url with parameter definitions.
            - See U(https://docs.microsoft.com/en-us/azure/templates/Microsoft.Authorization/2018-05-01/policyAssignments) for more details.
        type: str
    description:
        description:
            - This message will be part of response in case of policy violation.
        type: str
    metadata:
        description:
            - The policy assignment metadata.
            - Metadata in space-separated key=value pairs.
        type: dict
    sku:
        description:
            - The policy SKU.
        type: str
        choices:
            - a0
            - a1
    location:
        description:
            - The location of the policy assignment.
        type: str

extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
- name: Create a policy assignment
  azure_rm_policyassignment:
    scope: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    policy_definition:
        "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/policyDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

- name: Delete a policy assignment
  azure_rm_policyassignment:
    name: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    scope: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    state: absent
'''

RETURN = '''
id:
    description:
        - ID of current policy assignment.
    returned: always
    type: str
    sample:
      "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/policyAssignments/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
'''

import json
import os
import codecs
import base64
import uuid
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
    from ansible.module_utils.urls import open_url
    from ansible.module_utils.six.moves.urllib.parse import urlparse
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMPolicyAssignment(AzureRMModuleBase):
    """Configuration class for an Azure RM policy assignment"""

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str'
            ),
            scope=dict(
                type='str'
            ),
            display_name=dict(
                type='str'
            ),
            policy_definition=dict(
                type='raw'
            ),
            not_scopes=dict(
                type='list'
            ),
            parameters=dict(
                type='str'
            ),
            description=dict(
                type='str'
            ),
            metadata=dict(
                type='dict'
            ),
            sku=dict(
                type='str',
                choices=['a0', 'a1']
            ),
            location=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.name = None
        self.scope = None
        self.display_name = None
        self.policy_definition = None
        self.not_scopes = None
        self.parameters = None
        self.description = None
        self.metadata = None
        self.sku = None
        self.location = None

        self.results = dict(
            changed=False,
            id=None,
        )
        self.state = None

        super(AzureRMPolicyAssignment, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True,
                                                      supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        changed = False
        response = None
        results = None

        policy_definition = self.policy_definition
        if isinstance(self.policy_definition, dict):
            policy_definition = format_resource_id(val=self.policy_definition['name'],
                                                   subscription_id=self.policy_definition.get('subscription_id') or self.subscription_id,
                                                   namespace="Microsoft.Authorization",
                                                   types=self.policy_definition['types'],
                                                   resource_group=None)
        self.policy_definition = policy_definition

        self.parameters = self.load_file_string_or_url(self.parameters) if self.parameters else None
        if self.sku == 'a0':
            self.sku = self.rm_policy_models.PolicySku(name="A0", tier="Free")
        elif self.sku == 'a1':
            self.sku = self.rm_policy_models.PolicySku(name="A1", tier="Standard")

        self.scope = self.build_scope()

        if self.name is None:
            self.name = str(uuid.uuid4())

        response = self.get_policy_assignment()

        if self.state == 'present':
            if not response:
                changed = True

                policy_assignment_instance = self.rm_policy_models.PolicyAssignment(display_name=self.display_name,
                                                                                    policy_definition_id=self.policy_definition,
                                                                                    scope=self.scope,
                                                                                    not_scopes=self.not_scopes,
                                                                                    parameters=self.parameters,
                                                                                    description=self.description,
                                                                                    metadata=self.metadata,
                                                                                    sku=self.sku,
                                                                                    location=self.location)

                if not self.check_mode:
                    results = self.create_policy_assignment(policy_assignment_instance)
            else:
                self.log("Policy assignment already exists, not updatable")
                self.log('Result: {0}'.format(response))
            results = self.policy_assignment_to_dict(results) if results else None
        elif response:
            if not self.check_mode:
                changed = True
                self.delete_policy_assignment()

        self.results['changed'] = changed
        self.results['id'] = results if results else None
        return self.results

    # build scope
    def build_scope(self):
        subscription_scope = '/subscriptions/' + self.subscription_id
        if self.scope is None:
            return subscription_scope
        return self.scope

    def get_policy_assignment(self):
        result = None
        try:
            self.log("Getting the resource policy assignment")
            result = self.rm_policy_client.policy_assignments.get(scope=self.scope, policy_assignment_name=self.name)
        except Exception as exc:
            pass
        return result

    def create_policy_assignment(self, policy_assignment):
        try:
            self.log("Creating or updating the resource policy assignment")
            return self.rm_policy_client.policy_assignments.create(scope=self.scope,
                                                                   policy_assignment_name=self.name,
                                                                   parameters=policy_assignment)

        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error creating or updating the resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def delete_policy_assignment(self):
        try:
            self.log("Deleting the resource policy assignment")
            return self.rm_policy_client.policy_assignments.delete(scope=self.scope,
                                                                   policy_assignment_name=self.name)
        except self.rm_policy_models.ErrorResponseException as exc:
            self.fail("Error deleting the resource policy assignment {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def policy_assignment_to_dict(self, policy_assignment):
        return policy_assignment.as_dict()

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
    AzureRMPolicyAssignment()


if __name__ == '__main__':
    main()
