#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


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
    format:
        description:
            - Format of the data returned.
            - If C(raw) is selected information will be returned in raw format from Azure Python SDK.
            - If C(curated) is selected the structure will be identical to input parameters of azure_rm_webapp module. Not implemented yet.
        default: 'raw'
        choices:
            - 'curated'
            - 'raw'
    info_level:
        description:
            - A list to describe what information of the web app to return.
            - Only works with C(name) option.
        suboptions:
            level: 
                description:
                    - name of return information level.
                choices:
                    - basic
                    - app_settings
                    - configuration
                    - deployment_slot
                default: basic

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
      azure_rm_publicip_facts:
        resource_group: testrg

    - name: Get facts for web apps by name, with app_setting and configuration info
      azure_rm_publicip_facts:
        resource_group: testrg
        name: winwebapp1
        info_level:
            - level: "app_settings"
            - level: "configuration"
'''

RETURN = '''
azure_webapps:
    description: List of web apps.
    returned: always
    type: list
    example: [{
                "app_settings": {
                    "id": "/subscriptions/<subs_id>/resourceGroups/ansiblewebapp1/providers/Microsoft.Web/sites/ansiblewindows1/config/appsettings",
                    "location": "East US",
                    "name": "appsettings",
                    "properties": {},
                    "tags": {
                        "tag1": "test"
                    },
                    "type": "Microsoft.Web/sites/config"
                },
                "id": "/subscriptions/<subs_id>/resourceGroups/ansiblewebapp1/providers/Microsoft.Web/sites/ansiblewindows1",
                "kind": "app",
                "location": "East US",
                "name": "ansiblewindows1",
                "properties": {
                    "availabilityState": "Normal",
                    "clientAffinityEnabled": true,
                    "clientCertEnabled": false,
                    "containerSize": 0,
                    "dailyMemoryTimeQuota": 0,
                    "defaultHostName": "ansiblewindows1.azurewebsites.net",
                    "enabled": true,
                    "enabledHostNames": [
                        "ansiblewindows1.azurewebsites.net",
                        "ansiblewindows1.scm.azurewebsites.net"
                    ],
                    "hostNameSslStates": [
                        {
                            "hostType": "Standard",
                            "name": "ansiblewindows1.azurewebsites.net",
                            "sslState": "Disabled"
                        },
                        {
                            "hostType": "Repository",
                            "name": "ansiblewindows1.scm.azurewebsites.net",
                            "sslState": "Disabled"
                        }
                    ],
                    "hostNames": [
                        "ansiblewindows1.azurewebsites.net"
                    ],
                    "hostNamesDisabled": false,
                    "lastModifiedTimeUtc": "2018-05-29T06:55:50.6066659999999999Z",
                    "outboundIpAddresses": "13.82.93.245,40.121.151.32,40.121.151.100,52.179.11.174,40.121.148.162",
                    "repositorySiteName": "ansiblewindows1",
                    "reserved": false,
                    "resourceGroup": "ansiblewebapp1",
                    "scmSiteAlsoStopped": false,
                    "serverFarmId": "/subscriptions/<subs_id>/resourceGroups/ansiblewebapp1/providers/Microsoft.Web/serverfarms/win_appplan1",
                    "state": "Running",
                    "usageState": "Normal"
                },
                "site_config": {
                    "always_on": false,
                    "app_command_line": "",
                    "auto_heal_enabled": false,
                    "default_documents": [
                        "..."
                    ],
                    "detailed_error_logging_enabled": false,
                    "experiments": {
                        "ramp_up_rules": []
                    },
                    "http_logging_enabled": false,
                    "id": "/subscriptions/<subs_id>/resourceGroups/ansiblewebapp1/providers/Microsoft.Web/sites/ansiblewindows1/config/web",
                    "linux_fx_version": "",
                    "load_balancing": "LeastRequests",
                    "local_my_sql_enabled": false,
                    "location": "East US",
                    "logs_directory_size_limit": 35,
                    "managed_pipeline_mode": "Integrated",
                    "name": "ansiblewindows1",
                    "net_framework_version": "v4.0",
                    "node_version": "",
                    "number_of_workers": 1,
                    "php_version": "5.6",
                    "publishing_username": "$ansiblewindows1",
                    "python_version": "",
                    "remote_debugging_enabled": false,
                    "request_tracing_enabled": false,
                    "scm_type": "None",
                    "tags": {
                        "tag1": "test"
                    },
                    "type": "Microsoft.Web/sites/config",
                    "use32_bit_worker_process": true,
                    "virtual_applications": [
                        {
                            "physical_path": "site\\wwwroot",
                            "preload_enabled": false,
                            "virtual_path": "/"
                        }
                    ],
                    "vnet_name": "",
                    "web_sockets_enabled": false
                },
                "tags": {
                    "tag1": "test"
                },
                "type": "Microsoft.Web/sites"
            }]
'''
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

AZURE_OBJECT_CLASS = 'WebApp'

info_level_spec = dict(
    level=dict(
        type='str',
        choices=[
            'basic',
            'configuration',
            'app_settings'
        ],
        default='basic'
    )
)


class AzureRMWebAppFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            format=dict(
                type='str',
                choices=['curated',
                         'raw'],
                default='raw'
            ),
            info_level=dict(
                type='list',
                elements='dict',
                options=info_level_spec
            )
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_webapps=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.info_level = None

        super(AzureRMWebAppFacts, self).__init__(self.module_arg_spec,
                                                   supports_tags=False,
                                                   facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.format == "curated":
            self.fail('Not implemented.')

        if not self.name and self.info_level:
            self.fail('info_level must be specified with name parameter')

        if self.name:
            self.results['ansible_facts']['azure_webapps'] = self.list_by_name()

            if self.info_level:
                for level in self.info_level:
                    if level["level"] == "configuration":
                        self.results['ansible_facts']['azure_webapps'][0]['site_config'] = self.list_webapp_configuration()
                    if level["level"] == "app_settings":
                        self.results['ansible_facts']['azure_webapps'][0]['app_settings'] = self.list_webapp_appsettings()

        elif self.resource_group:
            self.results['ansible_facts']['azure_webapps'] = self.list_by_resource_group()
        else:
            self.results['ansible_facts']['azure_webapps'] = self.list_all()

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
            pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
            pip['name'] = item.name
            pip['type'] = item.type
            result = [pip]

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
                pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                pip['name'] = item.name
                pip['type'] = item.type
                results.append(pip)
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
                pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                pip['name'] = item.name
                pip['type'] = item.type
                results.append(pip)
        return results    

    def list_webapp_configuration(self):
        self.log('Get web app {0} configuration'.format(self.name))

        response = []

        try:
            response = self.web_client.web_apps.get_configuration(resource_group_name=self.resource_group, name=self.name)
        except CloudError as ex:
            self.fail('Error getting web app {0} configuration'.format(self.name))
        
        return response.as_dict()

    def list_webapp_appsettings(self):
        self.log('Get web app {0} app settings'.format(self.name))

        response = []

        try:
            response = self.web_client.web_apps.list_application_settings(resource_group_name=self.resource_group, name=self.name)
        except CloudError as ex:
            self.fail('Error getting web app {0} app settings'.format(self.name))
        
        return response.as_dict()



def main():
    AzureRMWebAppFacts()


if __name__ == '__main__':
    main()
