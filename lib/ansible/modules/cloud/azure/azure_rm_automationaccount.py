#!/usr/bin/python
#
# Copyright (c) 2017 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_automationaccount
version_added: "2.9"
short_description: Manage Azure Automation account
description:
    - Create, delete an Azure Automation account.
options:
    resource_group:
        description:
            - Name of resource group.
        type: str
        required: true
    name:
        description:
            - Name of the automation account.
        type: str
        required: true
    state:
        description:
            - State of the automation account. Use C(present) to create or update a automation account and C(absent) to delete an automation account.
        type: str
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Location of the resource.
            - If not specified, use resource group location.
        type: str

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Create an automation account
  azure_rm_automationaccount:
      name: Testing
      resource_group: myResourceGroup

- name: Create an automation account
  azure_rm_automationaccount:
      name: Testing
      resource_group: myResourceGroup
      location: eastus
'''

RETURN = '''
id:
    description:
        - Automation account resource ID.
    type: str
    returned: success
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Automation/automationAccounts/Testing"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


class AzureRMAutomationAccount(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str')
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None

        super(AzureRMAutomationAccount, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        account = self.get_account()
        changed = False
        if self.state == 'present':
            if not account:
                if not self.location:
                    resource_group = self.get_resource_group(self.resource_group)
                    self.location = resource_group.location
                param = self.automation_models.AutomationAccountCreateOrUpdateParameters(
                    location=self.location,
                    sku=self.automation_models.Sku(name='Basic'),
                    tags=self.tags
                )
                changed = True
                if not self.check_mode:
                    account = self.create_or_update(param)
            elif self.tags:
                update_tags, tags = self.update_tags(account.tags)
                if update_tags:
                    changed = True
                    param = self.automation_models.AutomationAccountUpdateParameters(
                        tags=tags
                    )
                    changed = True
                    if not self.check_mode:
                        self.update_account_tags(param)
            if account:
                self.results['id'] = account.id
        elif account:
            changed = True
            if not self.check_mode:
                self.delete_account()
        self.results['changed'] = changed
        return self.results

    def get_account(self):
        try:
            return self.automation_client.automation_account.get(self.resource_group, self.name)
        except self.automation_models.ErrorResponseException:
            pass

    def create_or_update(self, param):
        try:
            return self.automation_client.automation_account.create_or_update(self.resource_group, self.name, param)
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when creating automation account {0}: {1}'.format(self.name, exc.message))

    def update_account_tags(self, param):
        try:
            return self.automation_client.automation_account.update(self.resource_group, self.name, param)
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when updating automation account {0}: {1}'.format(self.name, exc.message))

    def delete_account(self):
        try:
            return self.automation_client.automation_account.delete(self.resource_group, self.name)
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when deleting automation account {0}: {1}'.format(self.name, exc.message))


def main():
    AzureRMAutomationAccount()


if __name__ == '__main__':
    main()
