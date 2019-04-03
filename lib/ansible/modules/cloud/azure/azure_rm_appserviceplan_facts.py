#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_appserviceplan_facts

version_added: "2.7"

short_description: Get azure app service plan facts.

description:
    - Get facts for a specific app service plan or all app service plans in a resource group, or all app service plan in current subscription.

options:
    name:
        description:
            - Only show results for a specific app service plan.
    resource_group:
        description:
            - Limit results by resource group.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yunge Zhu (@yungezz)"
'''

EXAMPLES = '''
    - name: Get facts for app service plan by name
      azure_rm_appserviceplan_facts:
        resource_group: myResourceGroup
        name: winwebapp1

    - name: Get azure_rm_appserviceplan_facts for app service plan in resource group
      azure_rm_webapp_facts:
        resource_group: myResourceGroup

    - name: Get facts for app service plan with tags
      azure_rm_appserviceplan_facts:
        tags:
          - testtag
          - foo:bar
'''

RETURN = '''
appserviceplans:
    description: List of app service plans.
    returned: always
    type: complex
    contains:
        id:
            description: Id of the app service plan.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Web/serverfarms/myPlan
        name:
            description: Name of the app service plan.
            returned: always
            type: str
        resource_group:
            description: Resource group of the app service plan.
            returned: always
            type: str
            sample: myResourceGroup
        location:
            description: Location of the app service plan.
            returned: always
            type: str
        kind:
            description: Kind of the app service plan.
            returned: always
            type: str
            sample: app
        sku:
            description: Sku of the app service plan.
            returned: always
            type: complex
            contains:
                name:
                    description: Name of sku.
                    returned: always
                    type: str
                    sample: S1
                family:
                    description: Family of sku.
                    returned: always
                    type: str
                    sample: S
                size:
                    description: Size of sku.
                    returned: always
                    type: str
                    sample: S1
                tier:
                    description: Tier of sku.
                    returned: always
                    type: str
                    sample: Standard
                capacity:
                    description: Capacity of sku.
                    returned: always
                    type: int
                    sample: 1
'''
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

AZURE_OBJECT_CLASS = 'AppServicePlan'


class AzureRMAppServicePlanFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(changed=False)

        self.name = None
        self.resource_group = None
        self.tags = None
        self.info_level = None

        super(AzureRMAppServicePlanFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            self.results['appserviceplans'] = self.list_by_name()
        elif self.resource_group:
            self.results['appserviceplans'] = self.list_by_resource_group()
        else:
            self.results['appserviceplans'] = self.list_all()

        return self.results

    def list_by_name(self):
        self.log('Get app service plan {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.web_client.app_service_plans.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            curated_result = self.construct_curated_plan(item)
            result = [curated_result]

        return result

    def list_by_resource_group(self):
        self.log('List app service plans in resource groups {0}'.format(self.resource_group))
        try:
            response = list(self.web_client.app_service_plans.list_by_resource_group(self.resource_group))
        except CloudError as exc:
            self.fail("Error listing app service plan in resource groups {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                curated_output = self.construct_curated_plan(item)
                results.append(curated_output)
        return results

    def list_all(self):
        self.log('List app service plans in current subscription')
        try:
            response = list(self.web_client.app_service_plans.list())
        except CloudError as exc:
            self.fail("Error listing app service plans: {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                curated_output = self.construct_curated_plan(item)
                results.append(curated_output)
        return results

    def construct_curated_plan(self, plan):
        plan_facts = self.serialize_obj(plan, AZURE_OBJECT_CLASS)

        curated_output = dict()
        curated_output['id'] = plan_facts['id']
        curated_output['name'] = plan_facts['name']
        curated_output['resource_group'] = plan_facts['properties']['resourceGroup']
        curated_output['location'] = plan_facts['location']
        curated_output['tags'] = plan_facts.get('tags', None)
        curated_output['is_linux'] = False
        curated_output['kind'] = plan_facts['kind']
        curated_output['sku'] = plan_facts['sku']

        if plan_facts['properties'].get('reserved', None):
            curated_output['is_linux'] = True

        return curated_output


def main():
    AzureRMAppServicePlanFacts()


if __name__ == '__main__':
    main()
