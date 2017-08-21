#!/usr/bin/python
#
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


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
    name:
        description:
            - Name of the Azure Function App
        required: true
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

author:
    - "Thomas Stringer (@tstringer)"
'''

EXAMPLES = '''
'''

RETURN = '''
state:
    description: Current state of the Azure Function App
    returned: success
    type: complex
    contains:
        address_prefix:
          description: IP address CIDR.
          type: str
          example: "10.1.0.0/16"
        id:
          description: Subnet resource path.
          type: str
          example: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/My_Virtual_Network/subnets/foobar"
        name:
          description: Subnet name.
          type: str
          example: "foobar"
        network_security_group:
          type: complex
          contains:
            id:
              description: Security group resource identifier.
              type: str
              example: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/secgroupfoo"
            name:
              description: Name of the security group.
              type: str
              example: "secgroupfoo"
        provisioning_state:
          description: Success or failure of the provisioning event.
          type: str
          example: "Succeeded"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.web.models import Site, SiteConfig, NameValuePair, SiteSourceControl
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
                required=True,
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
        self.app_settings = dict()

        super(AzureRMFunctionApp, self).__init__(
            self.module_arg_spec,
            supports_check_mode=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

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
            else:
                self.fail('Updating a resource is currently unsupported')

            try:
                new_function_app = self.web_client.web_apps.create_or_update(
                    resource_group_name=self.resource_group,
                    name=self.name,
                    site_envelope=function_app
                ).result()
                self.results['changed'] = True
                self.results['state'] = new_function_app.as_dict()
            except CloudError as exc:
                self.fail('Error creating or updating web app: {}'.format(exc))

        return self.results

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
        for app_setting_key in self.app_settings.keys():
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
