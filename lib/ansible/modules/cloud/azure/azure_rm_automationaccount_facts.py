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
module: azure_rm_automationaccount_facts
version_added: "2.9"
short_description: Get Azure automation account facts.
description:
    - Get facts of automation account.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the automation account.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
'''

RETURN = '''
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.tools import parse_resource_id
except ImportError:
    pass


class AzureRMAutomationAccountFacts(AzureRMModuleBase):
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
            show_statistics=dict(
                type='bool'
            ),
            show_usages=dict(
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
        self.show_statistics = None
        self.show_usages= None
        self.list_keys = None
        super(AzureRMAutomationAccountFacts, self).__init__(self.module_arg_spec, supports_tags=False, facts_module=True)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec):
            setattr(self, key, kwargs[key])

        if self.resource_group and self.name:
            accounts = self.get()
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
        result = dict(
            id=account.id,
            name=account.name,
            resource_group=id_dict['resource_group'],
            tags=account.tags,
            location=account.location,
            sku=account.sku.name,
            last_modified_by=account.last_modified_by,
            state=account.state,
            description=account.description
        )
        if self.show_statistics:
            account['statistics'] = self.get_statics(id_dict['resource_group'], account.name)
        if self.show_usages:
            account['usage'] = self.get_usages(id_dict['resource_group'], account.name)
        if self.list_keys:
            account['list_keys'] = self.list_account_keys(id_dict['resource_group'], account.name)
        return result

    def get(self):
        try:
            return self.automation_client.automation_account.get(self.resource_group, self.name)
        except self.automation_models.ErrorResponseException as exc:
            self.fail("Error when getting automation account {0}: {1}-{2}".format(self.name, exc.code, exc.message))

    def list_by_resource_group(self):
        try:
            return self.automation_client.automation_account.list_by_resource_group(self.resource_group)
        except self.automation_models.ErrorResponseException as exc:
            self.fail("Error when listing automation account in resource group {0}: {1}-{2}".format(self.resource_group, exc.code, exc.message))

    def list_all(self):
        try:
            return self.automation_client.automation_account.list()
        except self.automation_models.ErrorResponseException as exc:
            self.fail("Error when listing automation account: {1}-{2}".format(exc.code, exc.message))

    def get_statics(self, resource_group, name):
        result = []
        try:
            resp = self.automation_client.statistics.list_by_automation_account(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except self.automation_models.ErrorResponseException as exc:
            self.fail("Error when getting statics for automation account {0}/{1}: {2}-{3}".format(resource_group, name, exc.code, exc.message))
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
            self.fail("Error when getting usage for automation account {0}/{1}: {2}-{3}".format(resource_group, name, exc.code, exc.message))
        return result

    def list_account_keys(self, resource_group, name):
        try:
            resp = self.automation_client.keys.list_by_automation_account(resource_group, name)
            return [x.as_dict() for x in resp.keys]
        except self.automation_models.ErrorResponseException as exc:
            self.fail("Error when listing keys for automation account {0}/{1}: {2}-{3}".format(resource_group, name, exc.code, exc.message))


def main():
    AzureRMAutomationAccountFacts()


if __name__ == '__main__':
    main()
