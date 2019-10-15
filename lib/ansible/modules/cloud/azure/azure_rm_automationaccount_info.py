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
module: azure_rm_automationaccount_info
version_added: '2.9'
short_description: Get Azure automation account facts
description:
    - Get facts of automation account.

options:
    resource_group:
        description:
            - The name of the resource group.
        type: str
        required: True
    name:
        description:
            - The name of the automation account.
        type: str
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        type: list
    list_statistics:
        description:
            - List statistics details for a automation account.
            - Note this will cost network overhead, suggest only used when I(name) set.
        type: bool
    list_usages:
        description:
            - List usage details for a automation account.
            - Note this will cost network overhead, suggest only used when I(name) set.
        type: bool
    list_keys:
        description:
            - List keys for a automation account.
            - Note this will cost network overhead, suggest only used when I(name) set.
        type: bool

extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Get details of an automation account
  azure_rm_automationaccount_info:
      name: Testing
      resource_group: myResourceGroup
      list_statistics: yes
      list_usages: yes
      list_keys: yes

- name: List automation account in a resource group
  azure_rm_automationaccount_info:
      resource_group: myResourceGroup

- name: List automation account in a resource group
  azure_rm_automationaccount_info:
'''

RETURN = '''
automation_accounts:
    description:
        - List of automation account dicts.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            type: str
            returned: always
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups
                     /myResourceGroup/providers/Microsoft.Automation/automationAccounts/Testing"
        resource_group:
            description:
                - Resource group name.
            type: str
            returned: always
            sample: myResourceGroup
        name:
            description:
                - Resource name.
            type: str
            returned: always
            sample: Testing
        location:
            description:
                - Resource location.
            type: str
            returned: always
            sample: eastus
        creation_time:
            description:
                - Resource creation date time.
            type: str
            returned: always
            sample: "2019-04-26T02:55:16.500Z"
        last_modified_time:
            description:
                - Resource last modified date time.
            type: str
            returned: always
            sample: "2019-04-26T02:55:16.500Z"
        state:
            description:
                - Resource state.
            type: str
            returned: always
            sample: ok
        keys:
            description:
                - Resource keys.
            type: complex
            returned: always
            contains:
                key_name:
                    description:
                        - Name of the key.
                    type: str
                    returned: always
                    sample: Primary
                permissions:
                    description:
                        - Permission of the key.
                    type: str
                    returned: always
                    sample: Full
                value:
                    description:
                        - Value of the key.
                    type: str
                    returned: always
                    sample: "MbepKTO6IyGwml0GaKBkKN"
        statistics:
            description:
                - Resource statistics.
            type: complex
            returned: always
            contains:
                counter_property:
                    description:
                        - Property value of the statistic.
                    type: str
                    returned: always
                    sample: New
                counter_value:
                    description:
                        - Value of the statistic.
                    type: int
                    returned: always
                    sample: 0
                end_time:
                    description:
                        - EndTime of the statistic.
                    type: str
                    returned: always
                    sample: "2019-04-26T06:29:43.587518Z"
                id:
                    description:
                        - ID of the statistic.
                    type: str
                    returned: always
                    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups
                             /myResourceGroup/providers/Microsoft.Automation/automationAccounts/Testing/statistics/New"
                start_time:
                    description:
                        - StartTime of the statistic.
                    type: str
                    returned: always
                    sample: "2019-04-26T06:29:43.587518Z"
        usages:
            description:
                - Resource usages.
            type: complex
            returned: always
            contains:
                current_value:
                    description:
                        - Current usage.
                    type: float
                    returned: always
                    sample: 0.0
                limit:
                    description:
                        - Max limit, C(-1) for unlimited.
                    type: int
                    returned: always
                    sample: -1
                name:
                    description:
                        - Usage counter name.
                    type: complex
                    returned: always
                    contains:
                        localized_value:
                            description:
                                - Localized name.
                            type: str
                            returned: always
                            sample: "SubscriptionUsage"
                        value:
                            description:
                                - Name value.
                            type: str
                            returned: always
                            sample: "SubscriptionUsage"
                unit:
                    description:
                        - Usage unit name.
                    type: str
                    returned: always
                    sample: "Minute"
                throttle_status:
                    description:
                        - Usage throttle status.
                    type: str
                    returned: always
                    sample: "NotThrottled"

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.tools import parse_resource_id
except ImportError:
    pass


class AzureRMAutomationAccountInfo(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            ),
            list_statistics=dict(
                type='bool'
            ),
            list_usages=dict(
                type='bool'
            ),
            list_keys=dict(
                type='bool'
            )
        )
        # store the results of the module operation
        self.results = dict()
        self.resource_group = None
        self.name = None
        self.tags = None
        self.list_statistics = None
        self.list_usages = None
        self.list_keys = None

        super(AzureRMAutomationAccountInfo, self).__init__(self.module_arg_spec, supports_tags=False, facts_module=True)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_automationaccount_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_automationaccount_facts' module has been renamed to 'azure_rm_automationaccount_info'", version='2.13')

        for key in list(self.module_arg_spec):
            setattr(self, key, kwargs[key])

        if self.resource_group and self.name:
            accounts = [self.get()]
        elif self.resource_group:
            accounts = self.list_by_resource_group()
        else:
            accounts = self.list_all()
        self.results['automation_accounts'] = [self.to_dict(x) for x in accounts if self.has_tags(x.tags, self.tags)]
        return self.results

    def to_dict(self, account):
        if not account:
            return None
        id_dict = parse_resource_id(account.id)
        result = account.as_dict()
        result['resource_group'] = id_dict['resource_group']
        if self.list_statistics:
            result['statistics'] = self.get_statics(id_dict['resource_group'], account.name)
        if self.list_usages:
            result['usages'] = self.get_usages(id_dict['resource_group'], account.name)
        if self.list_keys:
            result['keys'] = self.list_account_keys(id_dict['resource_group'], account.name)
        return result

    def get(self):
        try:
            return self.automation_client.automation_account.get(self.resource_group, self.name)
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when getting automation account {0}: {1}'.format(self.name, exc.message))

    def list_by_resource_group(self):
        result = []
        try:
            resp = self.automation_client.automation_account.list_by_resource_group(self.resource_group)
            while True:
                result.append(resp.next())
        except StopIteration:
            pass
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when listing automation account in resource group {0}: {1}'.format(self.resource_group, exc.message))
        return result

    def list_all(self):
        result = []
        try:
            resp = self.automation_client.automation_account.list()
            while True:
                result.append(resp.next())
        except StopIteration:
            pass
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when listing automation account: {0}'.format(exc.message))
        return result

    def get_statics(self, resource_group, name):
        result = []
        try:
            resp = self.automation_client.statistics.list_by_automation_account(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when getting statics for automation account {0}/{1}: {2}'.format(resource_group, name, exc.message))
        return result

    def get_usages(self, resource_group, name):
        result = []
        try:
            resp = self.automation_client.usages.list_by_automation_account(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when getting usage for automation account {0}/{1}: {2}'.format(resource_group, name, exc.message))
        return result

    def list_account_keys(self, resource_group, name):
        try:
            resp = self.automation_client.keys.list_by_automation_account(resource_group, name)
            return [x.as_dict() for x in resp.keys]
        except self.automation_models.ErrorResponseException as exc:
            self.fail('Error when listing keys for automation account {0}/{1}: {2}'.format(resource_group, name, exc.message))


def main():
    AzureRMAutomationAccountInfo()


if __name__ == '__main__':
    main()
