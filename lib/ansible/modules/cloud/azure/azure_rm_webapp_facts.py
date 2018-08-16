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
module: azure_rm_webapp_facts

version_added: "2.7"

short_description: Get azure web app facts.

description:
    - Get facts for a specific web app or all web app in a resource group, or all web app in current subscription.

options:
    name:
        description:
            - Only show results for a specific web app.
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
    - name: Get facts for web app by name
      azure_rm_webapp_facts:
        resource_group: testrg
        name: winwebapp1

    - name: Get facts for web apps in resource group
      azure_rm_webapp_facts:
        resource_group: testrg

    - name: Get facts for web apps with tags
      azure_rm_webapp_facts:
        tags:
          - testtag
          - foo:bar
'''

RETURN = '''
webapps:
    description: List of web apps.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Id of the web app.
            returned: always
            type: str
            sample: /subscriptions/xxxx/resourceGroups/xxx/providers/Microsoft.Web/sites/xx
        name:
            description:
                - Name of the web app.
            returned: always
            type: str
        resource_group:
            description:
                - Resource group of the web app.
            returned: always
            type: str
        location:
            description:
                - Location of the web app.
            returned: always
            type: str
        plan:
            description:
                - Id of app service plan used by the web app.
            returned: always
            type: str
            sample: /subscriptions/xxxx/resourceGroups/xxx/providers/Microsoft.Web/serverfarms/xxx
        app_settings:
            description:
                - App settings of the application. Only returned when web app has app settings.
            type: complex
        frameworks:
            description:
                - Frameworks of the application. Only returned when web app has frameworks.
            type: complex
        properties:
            description:
                - Other useful properties of the web app, which is not curated to module input.
            return: always
            type: complex
            contains:
                availabilityState:
                    description: Availability of this web app.
                    type: str
                defaultHostName:
                    description: Host name of the web app.
                    type: str
                enabled:
                    description: Indicate the web app enabled or not.
                    type: bool
                enabledHostNames:
                    description: Enabled host names of the web app.
                    type: list
                hostNameSslStates:
                    description: SSL state per host names of the web app.
                    type: list
                hostNames:
                    description: host names of the web app.
                    type: list
                lastModifiedTimeUtc:
                    description: Last modified date  of the web app.
                    type: str
                outboundIpAddresses:
                    description: outbound ip address of the web app.
                    type: str
                state:
                    description: state of the web app.  eg. running.
                    type: str
'''
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

AZURE_OBJECT_CLASS = 'WebApp'


class AzureRMWebAppFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            webapps=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.info_level = None

        self.framework_names = ['net_framework', 'java', 'php', 'node', 'python', 'dotnetcore', 'ruby']

        super(AzureRMWebAppFacts, self).__init__(self.module_arg_spec,
                                                 supports_tags=False,
                                                 facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            self.results['webapps'] = self.list_by_name()
        elif self.resource_group:
            self.results['webapps'] = self.list_by_resource_group()
        else:
            self.results['webapps'] = self.list_all()

        return self.results

    def list_by_name(self):
        self.log('Get web app {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.web_client.web_apps.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            curated_result = self.get_curated_webapp(self.resource_group, self.name, item)
            result = [curated_result]

        return result

    def list_by_resource_group(self):
        self.log('List web apps in resource groups {0}'.format(self.resource_group))
        try:
            response = list(self.web_client.web_apps.list_by_resource_group(self.resource_group))
        except CloudError as exc:
            self.fail("Error listing web apps in resource groups {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                curated_output = self.get_curated_webapp(self.resource_group, item.name, item)
                results.append(curated_output)
        return results

    def list_all(self):
        self.log('List web apps in current subscription')
        try:
            response = list(self.web_client.web_apps.list())
        except CloudError as exc:
            self.fail("Error listing web apps: {1}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                curated_output = self.get_curated_webapp(item.resource_group, item.name, item)
                results.append(curated_output)
        return results

    def list_webapp_configuration(self, resource_group, name):
        self.log('Get web app {0} configuration'.format(name))

        response = []

        try:
            response = self.web_client.web_apps.get_configuration(resource_group_name=resource_group, name=name)
        except CloudError as ex:
            self.fail('Error getting web app {0} configuration'.format(name))

        return response.as_dict()

    def list_webapp_appsettings(self, resource_group, name):
        self.log('Get web app {0} app settings'.format(name))

        response = []

        try:
            response = self.web_client.web_apps.list_application_settings(resource_group_name=resource_group, name=name)
        except CloudError as ex:
            self.fail('Error getting web app {0} app settings'.format(name))

        return response.as_dict()

    def get_curated_webapp(self, resource_group, name, webapp):
        pip = self.serialize_obj(webapp, AZURE_OBJECT_CLASS)

        try:
            site_config = self.list_webapp_configuration(resource_group, name)
            app_settings = self.list_webapp_appsettings(resource_group, name)
        except CloudError as ex:
            pass
        return self.construct_curated_webapp(pip, site_config, app_settings)

    def construct_curated_webapp(self, webapp, configuration=None, app_settings=None, deployment_slot=None):
        curated_output = dict()
        curated_output['id'] = webapp['id']
        curated_output['name'] = webapp['name']
        curated_output['resource_group'] = webapp['properties']['resourceGroup']
        curated_output['location'] = webapp['location']
        curated_output['plan'] = webapp['properties']['serverFarmId']
        curated_output['tags'] = webapp.get('tags', None)

        # add properties
        curated_output['properties'] = webapp['properties']

        # curated site_config
        if configuration:
            curated_output['frameworks'] = []
            for fx_name in self.framework_names:
                fx_version = configuration.get(fx_name + '_version', None)
                if fx_version:
                    fx = {
                        'name': fx_name,
                        'version': fx_version
                    }
                    # java container setting
                    if fx_name == 'java':
                        if configuration['java_container'] and configuration['java_container_version']:
                            settings = {
                                'java_container': configuration['java_container'].lower(),
                                'java_container_version': configuration['java_container_version']
                            }
                            fx['settings'] = settings

                    curated_output['frameworks'].append(fx)

            # linux_fx_version
            if configuration.get('linux_fx_version', None):
                tmp = configuration.get('linux_fx_version').split("|")
                if len(tmp) == 2:
                    curated_output['frameworks'].append({'name': tmp[0].lower(), 'version': tmp[1]})

        # curated app_settings
        if app_settings and app_settings.get('properties', None):
            curated_output['app_settings'] = dict()
            for item in app_settings['properties']:
                curated_output['app_settings'][item] = app_settings['properties'][item]

        # curated deploymenet_slot
        if deployment_slot:
            curated_output['deployment_slot'] = deployment_slot
        return curated_output


def main():
    AzureRMWebAppFacts()


if __name__ == '__main__':
    main()
