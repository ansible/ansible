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
module: azure_rm_autoscale_facts
version_added: "2.7"
short_description: Get Azure Auto Scale Setting facts.
description:
    - Get facts of Auto Scale Setting.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the Auto Scale Setting.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
  - name: Get instance of Auto Scale Setting
    azure_rm_autoscale_facts:
      resource_group: resource_group_name
      name: auto_scale_name

  - name: List instances of Auto Scale Setting
    azure_rm_autoscale_facts:
      resource_group: resource_group_name
'''

RETURN = '''
azure_autoscale:
    description: List of Azure Scale Settings dicts.
    returned: always
    type: list
    sample: [{
        "enabled": true,
        "id": "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/foo/providers/microsoft.insights/autoscalesettings/scale",
        "location": "eastus",
        "name": "scale",
        "notifications": [
            {
                "custom_emails": [
                    "yuwzho@microsoft.com"
                ],
                "send_to_subscription_administrator": true,
                "send_to_subscription_co_administrators": false,
                "webhooks": []
            }
        ],
        "profiles": [
            {
                "count": "1",
                "max_count": "1",
                "min_count": "1",
                "name": "Auto created scale condition 0",
                "recurrence_days": [
                    "Monday"
                ],
                "recurrence_frequency": "Week",
                "recurrence_hours": [
                    "6"
                ],
                "recurrence_mins": [
                    "0"
                ],
                "recurrence_timezone": "China Standard Time",
                "rules": [
                    {
                        "cooldown": 5.0,
                        "direction": "Increase",
                        "metric_name": "Percentage CPU",
                        "metric_resource_uri": "/subscriptions/XX/resourceGroups/foo/providers/Microsoft.Compute/virtualMachineScaleSets/vmss",
                        "operator": "GreaterThan",
                        "statistic": "Average",
                        "threshold": 70.0,
                        "time_aggregation": "Average",
                        "time_grain": 1.0,
                        "time_window": 10.0,
                        "type": "ChangeCount",
                        "value": "1"
                    }
                ]
            }
        ],
        "target": "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/foo/providers/Microsoft.Compute/virtualMachineScaleSets/vmss"
    }]

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.serialization import Model
    from ansible.modules.cloud.azure.azure_rm_autoscale import auto_scale_to_dict
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMAutoScaleFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict()
        self.resource_group = None
        self.name = None
        self.tags = None
        super(AzureRMAutoScaleFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec) + ['tags']:
            setattr(self, key, kwargs[key])

        if self.resource_group and self.name:
            self.results['autoscales'] = self.get()
        elif self.resource_group:
            self.results['autoscales'] = self.list_by_resource_group()
        return self.results

    def get(self):
        result = []
        try:
            instance = self.monitor_client.autoscale_settings.get(self.resource_group, self.name)
            result = [auto_scale_to_dict(instance)]
        except Exception as ex:
            self.log('Could not get facts for autoscale {0} - {1}.'.format(self.name, str(ex)))
        return result

    def list_by_resource_group(self):
        results = []
        try:
            response = self.monitor_client.autoscale_settings.list_by_resource_group(self.resource_group)
            results = [auto_scale_to_dict(item) for item in response if self.has_tags(item.tags, self.tags)]
        except Exception as ex:
            self.log('Could not get facts for autoscale {0} - {1}.'.format(self.name, str(ex)))
        return results


def main():
    AzureRMAutoScaleFacts()


if __name__ == '__main__':
    main()
