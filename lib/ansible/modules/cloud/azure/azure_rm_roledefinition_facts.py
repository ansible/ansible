#!/usr/bin/python
#
# Copyright (c) 2019 Yunge Zhu, (@yungezz)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_roledefinition_facts
version_added: "2.8"
short_description: Get Azure Role Definition facts.
description:
    - Get facts of Azure Role Definition.

options:
    scope:
        description:
            - The scope of role defintion.
        required: True
    id:
        description:
            - Role definition id.
    role_name:
        description: Role name.
    type:
        description: Type of role.
        choices:
            - system
            - custom

extends_documentation_fragment:
    - azure

author:
    - "Yunge Zhu(@yungezz)"

'''

EXAMPLES = '''
    - name: List Role Definitions in scope
      azure_rm_roledefinition_facts:
        scope: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup

    - name: Get Role Definition by name
      azure_rm_roledefinition_facts:
        scope: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup
        name: myRoleDefinition
'''

RETURN = '''
roledefinitions:
    description: A list of Role Definition facts.
    returned: always
    type: complex
    contains:
      id:
        description: Role Definition id.
        returned: always
        type: str
        sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/roleDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      role_name:
        description: Role name.
        returned: always
        type: str
        sample: myCustomRoleDefinition
      name:
        description: System assigned role name.
        returned: always
        type: str
        sample: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
      assignable_scopes:
        description:
            - List of assignable scope of this definition.
        returned: always
        type: list
        sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup"
      permissions:
        description:
            - List of Role Definition peremissions.
        returned: always
        contains:
            actions:
                description:
                    - List of allowed actions.
                returned: always
                type: list
                sample: Microsoft.Compute/virtualMachines/read
            not_actions:
                description:
                    - List of denied actions.
                returned: always
                type: list
                sample: Microsoft.Compute/virtualMachines/write
            data_actions:
                description:
                    - List of allowed data actions.
                returned: always
                type: list
                sample: Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read
            not_data_actions:
                description:
                    - List of denied actions.
                returned: always
                type: list
                sample: Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.serialization import Model
    from azure.mgmt.authorization import AuthorizationManagementClient

except ImportError:
    # This is handled in azure_rm_common
    pass


def roledefinition_to_dict(role):
    result = dict(
        id=role.id,
        name=role.name,
        type=role.role_type,
        assignable_scopes=role.assignable_scopes,
        description=role.description,
        role_name=role.role_name
    )
    if role.permissions:
        result['permissions'] = [dict(
            actions=p.actions,
            not_actions=p.not_actions,
            data_actions=p.data_actions,
            not_data_actions=p.not_data_actions
        ) for p in role.permissions]
    return result


class AzureRMRoleDefinitionFacts(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            scope=dict(
                type='str',
                required='true'
            ),
            role_name=dict(type='str'),
            id=dict(type='str'),
            type=dict(
                type='str',
                choices=['custom', 'system'])
        )

        self.role_name = None
        self.scope = None
        self.id = None
        self.type = None

        self.results = dict(
            changed=False
        )

        self._client = None

        super(AzureRMRoleDefinitionFacts, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        if self.type:
            self.type = self.get_role_type(self.type)

        # get management client
        self._client = self.get_mgmt_svc_client(AuthorizationManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version="2018-01-01-preview")

        if self.id:
            self.results['roledefinitions'] = self.get_by_id()
        elif self.role_name:
            self.results['roledefinitions'] = self.get_by_role_name()
        else:
            self.results['roledefinitions'] = self.list()

        return self.results

    def get_role_type(self, role_type):
        if role_type:
            if role_type == 'custom':
                return 'CustomRole'
            else:
                return 'SystemRole'
        return role_type

    def list(self):
        '''
        List Role Definition in scope.

        :return: deserialized Role Definition state dictionary
        '''
        self.log("List Role Definition in scope {0}".format(self.scope))

        response = []

        try:
            response = list(self._client.role_definitions.list(scope=self.scope))

            if len(response) > 0:
                self.log("Response : {0}".format(response))
                roles = []

                if self.type:
                    roles = [r for r in response if r.role_type == self.type]
                else:
                    roles = response

                if len(roles) > 0:
                    return [roledefinition_to_dict(r) for r in roles]

        except CloudError as ex:
            self.log("Didn't find role definition in scope {0}".format(self.scope))

        return response

    def get_by_id(self):
        '''
        Get Role Definition in scope by id.

        :return: deserialized Role Definition state dictionary
        '''
        self.log("Get Role Definition by id {0}".format(self.id))

        response = None

        try:
            response = self._client.role_definitions.get(scope=self.scope, role_definition_id=self.id)
            if response:
                response = roledefinition_to_dict(response)
                if self.type:
                    if response.role_type == self.type:
                        return [response]
                else:
                    return [response]

        except CloudError as ex:
            self.log("Didn't find role definition by id {0}".format(self.id))

        return []

    def get_by_role_name(self):
        '''
        Get Role Definition in scope by role name.

        :return: deserialized role definition state dictionary
        '''
        self.log("Get Role Definition by name {0}".format(self.role_name))

        response = []

        try:
            response = self.list()

            if len(response) > 0:
                roles = []
                for r in response:
                    if r['role_name'] == self.role_name:
                        roles.append(r)

                if len(roles) == 1:
                    self.log("Role Definition : {0} found".format(self.role_name))
                    return roles
                if len(roles) > 1:
                    self.fail("Found multiple Role Definitions with name: {0}".format(self.role_name))

        except CloudError as ex:
            self.log("Didn't find Role Definition by name {0}".format(self.role_name))

        return []


def main():
    """Main execution"""
    AzureRMRoleDefinitionFacts()


if __name__ == '__main__':
    main()
