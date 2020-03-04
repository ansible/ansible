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
module: azure_rm_autoscale_info
version_added: "2.9"
short_description: Get Azure Auto Scale Setting facts
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
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
  - name: Get instance of Auto Scale Setting
    azure_rm_autoscale_info:
      resource_group: myResourceGroup
      name: auto_scale_name

  - name: List instances of Auto Scale Setting
    azure_rm_autoscale_info:
      resource_group: myResourceGroup
'''

RETURN = '''
autoscales:
    description: List of Azure Scale Settings dicts.
    returned: always
    type: list
    sample: [{
        "enabled": true,
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/microsoft.insights/autoscalesettings/scale",
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
                        "metric_resource_uri": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsof
                                                t.Compute/virtualMachineScaleSets/myVmss",
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
        "target": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachineScale
                   Sets/myVmss"
    }]

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


# duplicated in azure_rm_autoscale
def timedelta_to_minutes(time):
    if not time:
        return 0
    return time.days * 1440 + time.seconds / 60.0 + time.microseconds / 60000000.0


def get_enum_value(item):
    if 'value' in dir(item):
        return to_native(item.value)
    return to_native(item)


def auto_scale_to_dict(instance):
    if not instance:
        return dict()
    return dict(
        id=to_native(instance.id or ''),
        name=to_native(instance.name),
        location=to_native(instance.location),
        profiles=[profile_to_dict(p) for p in instance.profiles or []],
        notifications=[notification_to_dict(n) for n in instance.notifications or []],
        enabled=instance.enabled,
        target=to_native(instance.target_resource_uri),
        tags=instance.tags
    )


def rule_to_dict(rule):
    if not rule:
        return dict()
    result = dict(metric_name=to_native(rule.metric_trigger.metric_name),
                  metric_resource_uri=to_native(rule.metric_trigger.metric_resource_uri),
                  time_grain=timedelta_to_minutes(rule.metric_trigger.time_grain),
                  statistic=get_enum_value(rule.metric_trigger.statistic),
                  time_window=timedelta_to_minutes(rule.metric_trigger.time_window),
                  time_aggregation=get_enum_value(rule.metric_trigger.time_aggregation),
                  operator=get_enum_value(rule.metric_trigger.operator),
                  threshold=float(rule.metric_trigger.threshold))
    if rule.scale_action and to_native(rule.scale_action.direction) != 'None':
        result['direction'] = get_enum_value(rule.scale_action.direction)
        result['type'] = get_enum_value(rule.scale_action.type)
        result['value'] = to_native(rule.scale_action.value)
        result['cooldown'] = timedelta_to_minutes(rule.scale_action.cooldown)
    return result


def profile_to_dict(profile):
    if not profile:
        return dict()
    result = dict(name=to_native(profile.name),
                  count=to_native(profile.capacity.default),
                  max_count=to_native(profile.capacity.maximum),
                  min_count=to_native(profile.capacity.minimum))

    if profile.rules:
        result['rules'] = [rule_to_dict(r) for r in profile.rules]
    if profile.fixed_date:
        result['fixed_date_timezone'] = profile.fixed_date.time_zone
        result['fixed_date_start'] = profile.fixed_date.start
        result['fixed_date_end'] = profile.fixed_date.end
    if profile.recurrence:
        if get_enum_value(profile.recurrence.frequency) != 'None':
            result['recurrence_frequency'] = get_enum_value(profile.recurrence.frequency)
        if profile.recurrence.schedule:
            result['recurrence_timezone'] = to_native(str(profile.recurrence.schedule.time_zone))
            result['recurrence_days'] = [to_native(r) for r in profile.recurrence.schedule.days]
            result['recurrence_hours'] = [to_native(r) for r in profile.recurrence.schedule.hours]
            result['recurrence_mins'] = [to_native(r) for r in profile.recurrence.schedule.minutes]
    return result


def notification_to_dict(notification):
    if not notification:
        return dict()
    return dict(send_to_subscription_administrator=notification.email.send_to_subscription_administrator if notification.email else False,
                send_to_subscription_co_administrators=notification.email.send_to_subscription_co_administrators if notification.email else False,
                custom_emails=[to_native(e) for e in notification.email.custom_emails or []],
                webhooks=[to_native(w.service_url) for w in notification.webhooks or []])


class AzureRMAutoScaleInfo(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict()
        self.resource_group = None
        self.name = None
        self.tags = None

        super(AzureRMAutoScaleInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_autoscale_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_autoscale_facts' module has been renamed to 'azure_rm_autoscale_info'", version='2.13')

        for key in list(self.module_arg_spec):
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
    AzureRMAutoScaleInfo()


if __name__ == '__main__':
    main()
