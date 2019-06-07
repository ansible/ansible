#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Thomas Stringer <tomstr@microsoft.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_functionapp
version_added: "2.4"
short_description: Manage Azure Function Apps
description:
    - Create, update or delete an Azure Function App.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
        aliases:
            - resource_group_name
    name:
        description:
            - Name of the Azure Function App.
        required: true
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    plan:
        description:
            - App service plan.
            - It can be name of existing app service plan in same resource group as function app.
            - It can be resource id of existing app service plan.
            - Resource id. For example /subscriptions/<subs_id>/resourceGroups/<resource_group>/providers/Microsoft.Web/serverFarms/<plan_name>.
            - It can be a dict which contains C(name), C(resource_group).
            - C(name). Name of app service plan.
            - C(resource_group). Resource group name of app service plan.
        version_added: "2.8"
    container_settings:
        description: Web app container settings.
        suboptions:
            name:
                description:
                    - Name of container. For example "imagename:tag".
            registry_server_url:
                description:
                    - Container registry server url. For example C(mydockerregistry.io).
            registry_server_user:
                description:
                    - The container registry server user name.
            registry_server_password:
                description:
                    - The container registry server password.
        version_added: "2.8"
    storage_account:
        description:
            - Name of the storage account to use.
        required: true
        aliases:
            - storage
            - storage_account_name
    app_settings:
        description:
            - Dictionary containing application settings.
    state:
        description:
            - Assert the state of the Function App. Use C(present) to create or update a Function App and C(absent) to delete.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Thomas Stringer (@trstringer)
'''

EXAMPLES = '''
- name: Create a function app
  azure_rm_functionapp:
    resource_group: myResourceGroup
    name: myFunctionApp
    storage_account: myStorageAccount

- name: Create a function app with app settings
  azure_rm_functionapp:
    resource_group: myResourceGroup
    name: myFunctionApp
    storage_account: myStorageAccount
    app_settings:
      setting1: value1
      setting2: value2

- name: Create container based function app
  azure_rm_functionapp:
    resource_group: myResourceGroup
    name: myFunctionApp
    storage_account: myStorageAccount
    plan:
      resource_group: myResourceGroup
      name: myAppPlan
    container_settings:
      name: httpd
      registry_server_url: index.docker.io

- name: Delete a function app
  azure_rm_functionapp:
    resource_group: myResourceGroup
    name: myFunctionApp
    state: absent
'''

RETURN = '''
state:
    description:
        - Current state of the Azure Function App.
    returned: success
    type: dict
    example:
        id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Web/sites/myFunctionApp
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
        server_farm_id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Web/serverfarms/EastUSPlan
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
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.web.models import (
        site_config, app_service_plan, Site, SiteConfig, NameValuePair, SiteSourceControl,
        AppServicePlan, SkuDescription
    )
    from azure.mgmt.resource.resources import ResourceManagementClient
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass

container_settings_spec = dict(
    name=dict(type='str', required=True),
    registry_server_url=dict(type='str'),
    registry_server_user=dict(type='str'),
    registry_server_password=dict(type='str', no_log=True)
)


class AzureRMFunctionApp(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True, aliases=['resource_group_name']),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            storage_account=dict(
                type='str',
                aliases=['storage', 'storage_account_name']
            ),
            app_settings=dict(type='dict'),
            plan=dict(
                type='raw'
            ),
            container_settings=dict(
                type='dict',
                options=container_settings_spec
            )
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.storage_account = None
        self.app_settings = None
        self.plan = None
        self.container_settings = None

        required_if = [('state', 'present', ['storage_account'])]

        super(AzureRMFunctionApp, self).__init__(
            self.module_arg_spec,
            supports_check_mode=True,
            required_if=required_if
        )

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        if self.app_settings is None:
            self.app_settings = dict()

        try:
            resource_group = self.rm_client.resource_groups.get(self.resource_group)
        except CloudError:
            self.fail('Unable to retrieve resource group')

        self.location = self.location or resource_group.location

        try:
            function_app = self.web_client.web_apps.get(
                resource_group_name=self.resource_group,
                name=self.name
            )
            # Newer SDK versions (0.40.0+) seem to return None if it doesn't exist instead of raising CloudError
            exists = function_app is not None
        except CloudError as exc:
            exists = False

        if self.state == 'absent':
            if exists:
                if self.check_mode:
                    self.results['changed'] = True
                    return self.results
                try:
                    self.web_client.web_apps.delete(
                        resource_group_name=self.resource_group,
                        name=self.name
                    )
                    self.results['changed'] = True
                except CloudError as exc:
                    self.fail('Failure while deleting web app: {0}'.format(exc))
            else:
                self.results['changed'] = False
        else:
            kind = 'functionapp'
            linux_fx_version = None
            if self.container_settings and self.container_settings.get('name'):
                kind = 'functionapp,linux,container'
                linux_fx_version = 'DOCKER|'
                if self.container_settings.get('registry_server_url'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_URL'] = 'https://' + self.container_settings['registry_server_url']
                    linux_fx_version += self.container_settings['registry_server_url'] + '/'
                linux_fx_version += self.container_settings['name']
                if self.container_settings.get('registry_server_user'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_USERNAME'] = self.container_settings.get('registry_server_user')

                if self.container_settings.get('registry_server_password'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_PASSWORD'] = self.container_settings.get('registry_server_password')

            if not self.plan and function_app:
                self.plan = function_app.server_farm_id

            if not exists:
                function_app = Site(
                    location=self.location,
                    kind=kind,
                    site_config=SiteConfig(
                        app_settings=self.aggregated_app_settings(),
                        scm_type='LocalGit'
                    )
                )
                self.results['changed'] = True
            else:
                self.results['changed'], function_app = self.update(function_app)

            # get app service plan
            if self.plan:
                if isinstance(self.plan, dict):
                    self.plan = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Web/serverfarms/{2}".format(
                        self.subscription_id,
                        self.plan.get('resource_group', self.resource_group),
                        self.plan.get('name')
                    )
                function_app.server_farm_id = self.plan

            # set linux fx version
            if linux_fx_version:
                function_app.site_config.linux_fx_version = linux_fx_version

            if self.check_mode:
                self.results['state'] = function_app.as_dict()
            elif self.results['changed']:
                try:
                    new_function_app = self.web_client.web_apps.create_or_update(
                        resource_group_name=self.resource_group,
                        name=self.name,
                        site_envelope=function_app
                    ).result()
                    self.results['state'] = new_function_app.as_dict()
                except CloudError as exc:
                    self.fail('Error creating or updating web app: {0}'.format(exc))

        return self.results

    def update(self, source_function_app):
        """Update the Site object if there are any changes"""

        source_app_settings = self.web_client.web_apps.list_application_settings(
            resource_group_name=self.resource_group,
            name=self.name
        )

        changed, target_app_settings = self.update_app_settings(source_app_settings.properties)

        source_function_app.site_config = SiteConfig(
            app_settings=target_app_settings,
            scm_type='LocalGit'
        )

        return changed, source_function_app

    def update_app_settings(self, source_app_settings):
        """Update app settings"""

        target_app_settings = self.aggregated_app_settings()
        target_app_settings_dict = dict([(i.name, i.value) for i in target_app_settings])
        return target_app_settings_dict != source_app_settings, target_app_settings

    def necessary_functionapp_settings(self):
        """Construct the necessary app settings required for an Azure Function App"""

        function_app_settings = []

        if self.container_settings is None:
            for key in ['AzureWebJobsStorage', 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING', 'AzureWebJobsDashboard']:
                function_app_settings.append(NameValuePair(name=key, value=self.storage_connection_string))
            function_app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='~1'))
            function_app_settings.append(NameValuePair(name='WEBSITE_NODE_DEFAULT_VERSION', value='6.5.0'))
            function_app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=self.name))
        else:
            function_app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='~2'))
            function_app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE', value=False))
            function_app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=self.storage_connection_string))

        return function_app_settings

    def aggregated_app_settings(self):
        """Combine both system and user app settings"""

        function_app_settings = self.necessary_functionapp_settings()
        for app_setting_key in self.app_settings:
            found_setting = None
            for s in function_app_settings:
                if s.name == app_setting_key:
                    found_setting = s
                    break
            if found_setting:
                found_setting.value = self.app_settings[app_setting_key]
            else:
                function_app_settings.append(NameValuePair(
                    name=app_setting_key,
                    value=self.app_settings[app_setting_key]
                ))
        return function_app_settings

    @property
    def storage_connection_string(self):
        """Construct the storage account connection string"""

        return 'DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1}'.format(
            self.storage_account,
            self.storage_key
        )

    @property
    def storage_key(self):
        """Retrieve the storage account key"""

        return self.storage_client.storage_accounts.list_keys(
            resource_group_name=self.resource_group,
            account_name=self.storage_account
        ).keys[0].value


def main():
    """Main function execution"""

    AzureRMFunctionApp()


if __name__ == '__main__':
    main()
