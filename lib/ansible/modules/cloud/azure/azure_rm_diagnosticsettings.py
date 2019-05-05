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
module: azure_rm_diagnosticsettings
version_added: "2.9"
short_description: Manage Azure diagnostic setting.
description:
    - Create, updata and delete an diagnostic setting.
options:
    name:
        description:
            - The name of the diagnostic setting.
    target:
        description:
            - The target which is the diagnostic settings used for.
            - The identifier of the resource.
    state:
        default: present
        description:
            -Assert the state of the diagnostic setting. Use C(present) to create or update and C(absent) to delete.
        choices:
            - present
            - absent
    storage_account_id:
        description:
            - The resource ID of the storage account to which you would like to send Diagnostic Logs.
    service_bus_rule_id:
        description:
            - The service bus rule Id of the diagnostic setting.
            - This is here to maintain backwards compatibility.
    event_hub_authorization_rule_id:
        description:
            - The resource Id for the event hub authorization rule.
    event_hub_name:
        description:
            - The name of the event hub.
    metrics:
        description:
            - The list of metric settings.
            - Each type of resourse has its own designed metric
        type: list
        suboptions:
            time_grain:
                description:
                    - The timegrain of the metric in ISO8601 format.
            category:
                description:
                    - Name of a Diagnostic Metric category for a resource type this setting is applied to.
            enabled:
                description:
                    - A value indicating whether this category is enabled.
                type: bool
            retention_policy:
                description:
                    - The retention policy for this category.
                type: dict
                suboptions:
                    enabled:
                        description:
                            - A value indicating whether the retention policy is enabled.
                        type: bool
                    days:
                        description:
                            - The number of days for the retention in days.
                            - A value of 0 will retain the events indefinitely.
                        type: int
    logs:
        description:
            - The list of logs settings.
            - Each type of resourse has its own designed logs
        type: list
        suboptions:
            category:
                description:
                    - Name of a Diagnostic Logs category for a resource type this setting is applied to.
            enabled:
                description:
                    - A value indicating whether this category is enabled.
                type: bool
            retention_policy:
                description:
                    - The retention policy for this category.
                type: dict
                suboptions:
                    enabled:
                        description:
                            - A value indicating whether the retention policy is enabled.
                        type: bool
                    days:
                        description:
                            - The number of days for the retention in days.
                            - A value of 0 will retain the events indefinitely.
                        type: int
    workspace_id:
        description:
            - The workspace ID (resource ID of a Log Analytics workspace) for a Log Analytics workspace to which you would like to send Diagnostic Logs.

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
- name: Create diagnostic settings for IP
  azure_rm_diagnosticsettings:
    name: myipdiagnostic
    target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/myip"
    storage_account_id: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/
                         resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
    logs:
    - category: DDoSMitigationReports
      enabled: yes
      retention_policy:
        enabled: yes
        days: 3
    metrics:
    - category: AllMetrics
      enabled: yes
      time_grain: PT1H
      retention_policy:
        enabled: yes
        days: 3

- name: Delete diagnostic settings
  azure_rm_diagnosticsettings:
    name: myipdiagnostic
    target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/myip"
    state: absent
'''

RETURN = '''
id:
    description: diagnostic setting resource path.
    type: str
    returned: success
    example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/
              microsoft.network/publicipaddresses/myip/providers/microsoft.insights/diagnosticSettings/myipdiagnostic"
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


retention_policy_spec = dict(
    enabled=dict(type='bool'),
    days=dict(type='int')
)

metrics_spec = dict(
    time_grain=dict(type='str'),
    category=dict(type='str'),
    enabled=dict(type='bool'),
    retention_policy=dict(type='dict', options=retention_policy_spec)
)

logs_spec = dict(
    category=dict(type='str'),
    enabled=dict(type='bool'),
    retention_policy=dict(type='dict', options=retention_policy_spec)
)


class AzureRMDiagnosticSettings(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            target=dict(
                type='raw',
                required=True
            ),
            storage_account_id=dict(
                type='str'
            ),
            service_bus_rule_id=dict(
                type='str'
            ),
            event_hub_authorization_rule_id=dict(
                type='str'
            ),
            event_hub_name=dict(
                type='str'
            ),
            metrics=dict(
                type='list',
                elements='dict',
                options=metrics_spec
            ),
            logs=dict(
                type='list',
                elements='dict',
                options=logs_spec
            ),
            workspace_id=dict(
                type='str'
            )
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.name = None
        self.state = None
        self.target = None
        self.storage_account_id = None
        self.service_bus_rule_id = None
        self.event_hub_authorization_rule_id = None
        self.event_hub_name = None
        self.metrics = None
        self.logs = None
        self.workspace_id = None

        super(AzureRMDiagnosticSettings, self).__init__(self.module_arg_spec,
                                                        supports_check_mode=True,
                                                        supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        results = None
        changed = False

        results = self.get_diagnostic_settings()

        resource_id = self.target
        if isinstance(self.target, dict):
            resource_id = format_resource_id(val=self.target['name'],
                                             subscription_id=self.target.get('subscription_id') or self.subscription_id,
                                             namespace=self.target['namespace'],
                                             types=self.target['types'],
                                             resource_group=self.target.get('resource_group'))
        self.target = resource_id
        if self.state == 'present':
            def create_metric_or_log_instance(params, metric_or_log):
                data = params.copy()
                data['category'] = data.get('category', None)
                data['enabled'] = data.get('enabled', None)
                if data.get('retention_policy', None):
                    data['retention_policy'] = RetentionPolicy(enabled=data.get('retention_policy').get('enabled', False),
                                                               days=data.get('retention_policy').get('days', 0))
                else:
                    data['retention_policy'] = None
                data['time_grain'] = data.get('time_grain', None)
                return metric_or_log(**data)

            parameters = DiagnosticSettingsResource(storage_account_id=self.storage_account_id,
                                                    service_bus_rule_id=self.service_bus_rule_id,
                                                    event_hub_authorization_rule_id=self.event_hub_authorization_rule_id,
                                                    event_hub_name=self.event_hub_name,
                                                    metrics=[create_metric_or_log_instance(p, MetricSettings) for p in self.metrics or []],
                                                    logs=[create_metric_or_log_instance(p, LogSettings) for p in self.logs or []],
                                                    workspace_id=self.workspace_id)

            if not results:
                changed = True
                if not self.check_mode:
                    results = self.create_or_update_diagnostic_settings(parameters)
            else:
                changed, results = self.check_status(changed=changed, results=results, params=parameters)

                if changed and not self.check_mode:
                    results = self.create_or_update_diagnostic_settings(results)
            results = self.diagnostic_setting_to_dict(results) if results else None
        elif results:
            changed = True
            if not self.check_mode:
                results = self.delete_diagnostic_settings()

        self.results['changed'] = changed
        self.results['id'] = results['id'] if results else None
        return self.results

    def check_status(self, changed, results, params):
        if params.storage_account_id and results.storage_account_id != params.storage_account_id:
            changed = True
            results.storage_account_id = params.storage_account_id

        if params.service_bus_rule_id and results.service_bus_rule_id != params.service_bus_rule_id:
            changed = True
            results.service_bus_rule_id = params.service_bus_rule_id

        if params.event_hub_authorization_rule_id and results.event_hub_authorization_rule_id != params.event_hub_authorization_rule_id:
            changed = True
            results.event_hub_authorization_rule_id = params.event_hub_authorization_rule_id

        if params.event_hub_name and results.event_hub_name != params.event_hub_name:
            changed = True
            results.event_hub_name = params.event_hub_name

        if params.metrics:
            changed, results.metrics = self.update_metrics_or_logs(params=params.metrics, results=results.metrics, changed=changed)

        if params.logs:
            changed, results.logs = self.update_metrics_or_logs(params=params.logs, results=results.logs, changed=changed)

        if params.workspace_id and results.workspace_id != params.workspace_id:
            changed = True
            results.workspace_id = params.workspace_id

        return changed, results

    def update_metrics_or_logs(self, params, results, changed):
        results_name_dict = dict()
        for idx, val in enumerate(results):
            results_name_dict[val.category] = idx
        for val in params:
            if results_name_dict.get(val.category, None) is not None:
                if val.enabled is not None and val.enabled != results[results_name_dict.get(val.category)].enabled:
                    changed = True
                    results[results_name_dict.get(val.category)].enabled = val.enabled
                if results[results_name_dict.get(val.category)].enabled:
                    if val.retention_policy is not None and val.retention_policy != results[results_name_dict.get(val.category)].retention_policy:
                        changed = True
                        results[results_name_dict.get(val.category)].retention_policy = val.retention_policy
            else:
                self.fail("Incrorrect metric or log category! Please check the exsitence of the category for this resource.")
        return changed, results

    def get_diagnostic_settings(self):
        self.log('Getting diagnostic settings {0}'.format(self.name))
        try:
            return self.monitor_client.diagnostic_settings.get(resource_uri=self.target, name=self.name)
        except Exception as exc:
            self.log('Error getting diagnostic settings {0} - {1}'.format(self.name, str(exc)))
            return None

    def create_or_update_diagnostic_settings(self, param):
        self.log('Creating or updating diagnostic settings {0}'.format(self.name))
        try:
            return self.monitor_client.diagnostic_settings.create_or_update(resource_uri=self.target, parameters=param, name=self.name)
        except ErrorResponseException as exc:
            self.fail("Error creating diagnostic settings {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def delete_diagnostic_settings(self):
        self.log('Deleting diagnostic settings {0}'.format(self.name))
        try:
            return self.monitor_client.diagnostic_settings.delete(resource_uri=self.target, name=self.name)
        except ErrorResponseException as exc:
            self.fail("Error deleting diagnostic settings {0} - {1}".format(self.name, str(exc.inner_exception) or str(exc)))

    def diagnostic_setting_to_dict(self, diagnostic_setting):
        return diagnostic_setting.as_dict()


def main():
    AzureRMDiagnosticSettings()


if __name__ == '__main__':
    main()
