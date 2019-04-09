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
module: azure_rm_roleassignment_facts
version_added: "2.8"
short_description: Gets Azure Role Assignment facts.
description:
    - Gets facts of Azure Role Assignment.

options:
    scope:
        description:
            - The scope that the role assignment applies to.
            - For example, use /subscriptions/{subscription-id}/ for a subscription,
            - /subscriptions/{subscription-id}/resourceGroups/{resourcegroup-name} for a resource group,
            - /subscriptions/{subscription-id}/resourceGroups/{resourcegroup-name}/providers/{resource-provider}/{resource-type}/{resource-name} for a resource
    name:
        description:
            - Name of role assignment.
            - Mutual exclusive with I(assignee).
    assignee:
        description:
            - Object id of a user, group or service principal.
            - Mutually exclusive with I(name).
    role_definition_id:
        description:
            - Resource id of role definition.

extends_documentation_fragment:
    - azure

author:
    - "Yunge Zhu(@yungezz)"

'''

EXAMPLES = '''
    - name: Get role assignments for specific service principal
      azure_rm_roleassignment_facts:
        assignee: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    - name: Get role assignments for specific scope
      azure_rm_roleassignment_facts:
        scope: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
'''

RETURN = '''
roleassignments:
    description: List of role assignments.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Id of role assignment.
            type: str
            returned: always
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/roleAssignments/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        name:
            description:
                - Name of role assignment.
            type: str
            returned: always
            sample: myRoleAssignment
        type:
            descripition:
                - Type of role assignment.
            type: str
            returned: always
            sample: custom
        principal_id:
            description:
                - Principal Id of the role assigned to.
            type: str
            returned: always
            sample: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        role_definition_id:
            description:
                - Role definition id that was assigned to principal_id.
            type: str
            returned: always
            sample: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        scope:
            description:
                - The role assignment scope
            type: str
            returned: always
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.serialization import Model
    from azure.mgmt.authorization import AuthorizationManagementClient

except ImportError:
    # This is handled in azure_rm_common
    pass


def roleassignment_to_dict(assignment):
    return dict(
        id=assignment.id,
        name=assignment.name,
        type=assignment.type,
        principal_id=assignment.principal_id,
        role_definition_id=assignment.role_definition_id,
        scope=assignment.scope
    )


class AzureRMRoleAssignmentFacts(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str'
            ),
            scope=dict(
                type='str'
            ),
            assignee=dict(
                type='str'
            ),
            role_definition_id=dict(
                type='str'
            )
        )

        self.name = None
        self.scope = None
        self.assignee = None
        self.role_definition_id = None

        self.results = dict(
            changed=False
        )

        self._client = None

        mutually_exclusive = [['name', 'assignee']]

        super(AzureRMRoleAssignmentFacts, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_tags=False,
                                                         mutually_exclusive=mutually_exclusive)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        # get management client
        self._client = self.get_mgmt_svc_client(AuthorizationManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version="2018-01-01-preview")

        if self.name:
            self.results['roleassignments'] = self.get_by_name()
        elif self.assignee:
            self.results['roleassignments'] = self.get_by_assignee()
        elif self.scope:
            self.results['roleassignments'] = self.list_by_scope()
        else:
            self.fail("Please specify name or assignee")

        return self.results

    def get_by_name(self):
        '''
        Gets the properties of the specified role assignment by name.

        :return: deserialized role assignment dictionary
        '''
        self.log("Gets role assignment {0} by name".format(self.name))

        results = []

        try:
            response = self._client.role_assignments.get(scope=self.scope, role_assignment_name=self.name)

            if response:
                response = roleassignment_to_dict(response)

                if self.role_definition_id:
                    if self.role_definition_id == response['role_definition_id']:
                        results = [response]
                else:
                    results = [response]

        except CloudError as ex:
            self.log("Didn't find role assignment {0} in scope {1}".format(self.name, self.scope))

        return results

    def get_by_assignee(self):
        '''
        Gets the role assignments by assignee.

        :return: deserialized role assignment dictionary
        '''
        self.log("Gets role assignment {0} by name".format(self.name))

        results = []
        filter = "principalId eq '{0}'".format(self.assignee)
        try:
            response = list(self._client.role_assignments.list(filter=filter))

            if response and len(response) > 0:
                response = [roleassignment_to_dict(a) for a in response]

                if self.role_definition_id:
                    for r in response:
                        if r['role_definition_id'] == self.role_definition_id:
                            results.append(r)
                else:
                    results = response

        except CloudError as ex:
            self.log("Didn't find role assignments to assignee {0}".format(self.assignee))

        return results

    def list_by_scope(self):
        '''
        Lists the role assignments by specific scope.

        :return: deserialized role assignment dictionary
        '''
        self.log("Lists role assignment by scope {0}".format(self.scope))

        results = []
        try:
            response = list(self._client.role_assignments.list_for_scope(scope=self.scope, filter='atScope()'))

            if response and len(response) > 0:
                response = [roleassignment_to_dict(a) for a in response]

                if self.role_definition_id:
                    for r in response:
                        if r['role_definition_id'] == self.role_definition_id:
                            results.append(r)
                else:
                    results = response

        except CloudError as ex:
            self.log("Didn't find role assignments to scope {0}".format(self.scope))

        return results


def main():
    """Main execution"""
    AzureRMRoleAssignmentFacts()


if __name__ == '__main__':
    main()
