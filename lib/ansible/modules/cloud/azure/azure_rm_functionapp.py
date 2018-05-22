#!/usr/bin/python
#
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>
#
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
    - Create, update or delete an Azure Function App
options:
    resource_group:
        description:
            - Name of resource group
        required: true
        aliases:
            - resource_group_name
    name:
        description:
            - Name of the Azure Function App
        required: true
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    storage_account:
        description:
            - Name of the storage account to use.
        required: true
        aliases:
            - storage
            - storage_account_name
    app_settings:
        description:
            - Dictionary containing application settings
    state:
        description:
            - Assert the state of the Function App. Use 'present' to create or update a Function App and
              'absent' to delete.
        required: false
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Thomas Stringer (@tstringer)"
'''

EXAMPLES = '''
- name: create function app
  azure_rm_functionapp:
      resource_group: ansible-rg
      name: myfunctionapp

- name: create a function app with app settings
  azure_rm_functionapp:
      resource_group: ansible-rg
      name: myfunctionapp
      app_settings:
          setting1: value1
          setting2: value2

- name: delete a function app
  azure_rm_functionapp:
      name: myfunctionapp
      state: absent
'''

RETURN = '''
state:
    description: Current state of the Azure Function App
    returned: success
    type: dict
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
        resource_group: ansible-rg
        default_host_name: myfunctionapp.azurewebsites.net
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.web.models import Site, SiteConfig, NameValuePair, SiteSourceControl
    from azure.mgmt.resource.resources import ResourceManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMFunctionApp(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True, aliases=['resource_group_name']),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str', required=False),
            storage_account=dict(
                type='str',
                required=False,
                aliases=['storage', 'storage_account_name']
            ),
            app_settings=dict(type='dict')
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
            exists = True
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
                    self.fail('Failure while deleting web app: {}'.format(exc))
            else:
                self.results['changed'] = False
        else:
            if not exists:
                function_app = Site(
                    location=self.location,
                    kind='functionapp',
                    site_config=SiteConfig(
                        app_settings=self.aggregated_app_settings(),
                        scm_type='LocalGit'
                    )
                )
                self.results['changed'] = True
            else:
                self.results['changed'], function_app = self.update(function_app)

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
                    self.fail('Error creating or updating web app: {}'.format(exc))

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
        for key in ['AzureWebJobsStorage', 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING', 'AzureWebJobsDashboard']:
            function_app_settings.append(NameValuePair(name=key, value=self.storage_connection_string))
        function_app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='~1'))
        function_app_settings.append(NameValuePair(name='WEBSITE_NODE_DEFAULT_VERSION', value='6.5.0'))
        function_app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=self.storage_account))
        return function_app_settings

    def aggregated_app_settings(self):
        """Combine both system and user app settings"""

        function_app_settings = self.necessary_functionapp_settings()
        for app_setting_key in self.app_settings:
            function_app_settings.append(NameValuePair(
                name=app_setting_key,
                value=self.app_settings[app_setting_key]
            ))
        return function_app_settings

    @property
    def storage_connection_string(self):
        """Construct the storage account connection string"""

        return 'DefaultEndpointsProtocol=https;AccountName={};AccountKey={}'.format(
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
