#!/usr/bin/python
#
# Copyright (c) 2019 Fan Qiu, (fanqiu@microsoft.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_diagnosticsettings_facts
version_added: "2.9"
short_description: Get Azure diagnostic setting facts.
description:
    - Get facts of diagnostic setting.
options:
    name:
        description:
            - The name of the diagnostic setting.
    target:
        description:
            - The target which is the diagnostic settings used for.
            - The identifier of the resource.
    show_category:
        description:
            - List the diagnostic settings category when I(show_category) is set to true
            - Note this will cost one more network overhead.
        type: bool

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
- name: Get facts for a specific diagnostic setting
  azure_rm_diagnosticsettings_facts:
    name: fanqiuipdiagnostic
    target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/myip"
    show_category: true
- name: List facts for diagnostic setting of a specific resource
  azure_rm_diagnosticsettings_facts:
    target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/myip"
    show_category: true
'''

RETURN = '''
labs:
    description: A list of dictionaries containing facts for diagnostic setting.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/
                      microsoft.network/publicipaddresses/myip/providers/microsoft.insights/diagnosticSettings/myipdiagnostic"
        storage_account_id:
            description:
                - The resource ID of the storage account to which you would like to send Diagnostic Logs.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myorgdiag"
        name:
            description:
                - The name of the resource.
            returned: always
            type: str
            sample: myipdiagnostic
        logs:
            description:
                - The list of logs settings.
            returned: always
            type: list
            sample: '[
                        {
                            "category": "DDoSProtectionNotifications",
                            "enabled": false,
                            "retention_policy": {
                                "days": 0,
                                "enabled": false
                            }
                        },
                        {
                            "category": "DDoSMitigationFlowLogs",
                            "enabled": true,
                            "retention_policy": {
                                "days": 6,
                                "enabled": true
                            }
                        },
                        {
                            "category": "DDoSMitigationReports",
                            "enabled": true,
                            "retention_policy": {
                                "days": 3,
                                "enabled": true
                            }
                        }
                    ]'
        metrics:
            description:
                - The list of metric settings.
            returned: always
            type: list
            sample: '[
                        {
                            "category": "AllMetrics",
                            "enabled": false,
                            "retention_policy": {
                                "days": 0,
                                "enabled": false
                            }
                        }
                    ]'
category:
    description: A list of dictionaries containing facts for diagnostic setting category.
    returned: when I(show_category) is set to true
    type: complex
    contains:
        category_type:
            description:
                - The type of the diagnostic settings category. Possible values include 'Metrics' and 'Logs'
            returned: always
            type: str
            example: "Logs"
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/
                      microsoft.network/publicipaddresses/myip/providers/microsoft.insights/diagnosticSettingsCategories/DDoSProtectionNotifications"
        name:
            description:
                - The name of the resource.
            returned: always
            type: str
            sample: DDoSProtectionNotifications

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils._text import to_native
from datetime import timedelta

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.monitor.models import MetricSettings, DiagnosticSettingsResource, LogSettings, RetentionPolicy, ErrorResponseException
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDiagnosticSettingsFacts(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str'
            ),
            target=dict(
                type='raw',
                required=True
            ),
            show_category=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            diagnosticsettings=[]
        )

        self.name = None
        self.target = None
        self.show_category = None

        super(AzureRMDiagnosticSettingsFacts, self).__init__(self.module_arg_spec,
                                                             supports_check_mode=True,
                                                             supports_tags=False,
                                                             facts_module=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        diagnosticsettings = []

        if self.name:
            diagnosticsettings = self.get_diagnostic_settings()
        else:
            diagnosticsettings = self.list_diagnostic_settings()
        diagnosticsettings = [self.diagnostic_setting_to_dict(x) for x in diagnosticsettings]

        if self.show_category:
            category = self.get_category_info()
            self.results['category'] = category.as_dict()['value']
        self.results['diagnosticsettings'] = diagnosticsettings

        return self.results

    def get_category_info(self):
        self.log('Getting diagnostic settings {0}'.format(self.name))
        try:
            return self.monitor_client.diagnostic_settings_category.list(resource_uri=self.target)
        except ErrorResponseException as exc:
            self.fail('Error listing diagnostic settings category {0} - {1}'.format(self.target, str(exc)))
            return None

    def get_diagnostic_settings(self):
        self.log('Getting diagnostic settings {0}'.format(self.name))
        try:
            diagnostic_settings = self.monitor_client.diagnostic_settings.get(resource_uri=self.target, name=self.name)
            return [diagnostic_settings]
        except ErrorResponseException as exc:
            self.fail('Error getting diagnostic settings {0} - {1}'.format(self.name, str(exc)))

    def list_diagnostic_settings(self):
        self.log('Listing diagnostic settings {0}'.format(self.name))
        try:
            diagnostic_settings = self.monitor_client.diagnostic_settings.list(resource_uri=self.target)
            return diagnostic_settings.value
        except ErrorResponseException as exc:
            self.fail('Error listing diagnostic settings {0} - {1}'.format(self.target, str(exc)))

    def diagnostic_setting_to_dict(self, diagnostic_setting):
        return diagnostic_setting.as_dict()


def main():
    AzureRMDiagnosticSettingsFacts()


if __name__ == '__main__':
    main()
