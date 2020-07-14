#!/usr/bin/python
#
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_functionapp_info
version_added: "2.9"
short_description: Get Azure Function App facts
description:
    - Get facts for one Azure Function App or all Function Apps within a resource group.
options:
    name:
        description:
            - Only show results for a specific Function App.
    resource_group:
        description:
            - Limit results to a resource group. Required when filtering by name.
        aliases:
            - resource_group_name
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Thomas Stringer (@trstringer)
'''

EXAMPLES = '''
    - name: Get facts for one Function App
      azure_rm_functionapp_info:
        resource_group: myResourceGroup
        name: myfunctionapp

    - name: Get facts for all Function Apps in a resource group
      azure_rm_functionapp_info:
        resource_group: myResourceGroup

    - name: Get facts for all Function Apps by tags
      azure_rm_functionapp_info:
        tags:
          - testing
'''

RETURN = '''
azure_functionapps:
    description:
        - List of Azure Function Apps dicts.
    returned: always
    type: list
    example:
        id: /subscriptions/.../resourceGroups/ansible-rg/providers/Microsoft.Web/sites/myfunctionapp
        name: myfunctionapp
        kind: functionapp
        location: East US
        type: Microsoft.Web/sites
        state: Running
        host_names:
          - myfunctionapp.azurewebsites.net
        repository_site_name: myfunctionapp
        usage_state: Normal
        enabled: true
        enabled_host_names:
          - myfunctionapp.azurewebsites.net
          - myfunctionapp.scm.azurewebsites.net
        availability_state: Normal
        host_name_ssl_states:
          - name: myfunctionapp.azurewebsites.net
            ssl_state: Disabled
            host_type: Standard
          - name: myfunctionapp.scm.azurewebsites.net
            ssl_state: Disabled
            host_type: Repository
        server_farm_id: /subscriptions/.../resourceGroups/ansible-rg/providers/Microsoft.Web/serverfarms/EastUSPlan
        reserved: false
        last_modified_time_utc: 2017-08-22T18:54:01.190Z
        scm_site_also_stopped: false
        client_affinity_enabled: true
        client_cert_enabled: false
        host_names_disabled: false
        outbound_ip_addresses: ............
        container_size: 1536
        daily_memory_time_quota: 0
        resource_group: myResourceGroup
        default_host_name: myfunctionapp.azurewebsites.net
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


class AzureRMFunctionAppInfo(AzureRMModuleBase):
    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str', aliases=['resource_group_name']),
            tags=dict(type='list'),
        )

        self.results = dict(
            changed=False,
            ansible_info=dict(azure_functionapps=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMFunctionAppInfo, self).__init__(
            self.module_arg_spec,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_functionapp_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_functionapp_facts' module has been renamed to 'azure_rm_functionapp_info'",
                                  version='2.13', collection_name='ansible.builtin')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['ansible_info']['azure_functionapps'] = self.get_functionapp()
        elif self.resource_group:
            self.results['ansible_info']['azure_functionapps'] = self.list_resource_group()
        else:
            self.results['ansible_info']['azure_functionapps'] = self.list_all()

        return self.results

    def get_functionapp(self):
        self.log('Get properties for Function App {0}'.format(self.name))
        function_app = None
        result = []

        try:
            function_app = self.web_client.web_apps.get(
                self.resource_group,
                self.name
            )
        except CloudError:
            pass

        if function_app and self.has_tags(function_app.tags, self.tags):
            result = function_app.as_dict()

        return [result]

    def list_resource_group(self):
        self.log('List items')
        try:
            response = self.web_client.web_apps.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing for resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(item.as_dict())
        return results

    def list_all(self):
        self.log('List all items')
        try:
            response = self.web_client.web_apps.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(item.as_dict())
        return results


def main():
    AzureRMFunctionAppInfo()


if __name__ == '__main__':
    main()
