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
module: azure_rm_autoscale
version_added: "2.7"
short_description: Manage Azure autoscale setting.
description:
    - Create, delete an autoscale setting.
options:
    target:
        description:
        - The identifier of the resource to apply autoscale setting.
        - It could be the resource id string.
        - It also could be a dict contains the C(name), C(subscription_id), C(namespace), C(types), C(resource_group) of the resource.
    resource_group:
        required: true
        description: resource group of the resource.
    enabled:
        type: bool
        description: Specifies whether automatic scaling is enabled for the resource.
        default: true
    profiles:
        description:
        - The collection of automatic scaling profiles that specify different scaling parameters for different time periods.
        - A maximum of 20 profiles can be specified.
        suboptions:
            name:
                required: true
                description: the name of the profile.
            count:
                required: true
                description:
                - The number of instances that will be set if metrics are not available for evaluation.
                - The default is only used if the current instance count is lower than the default.
            min_count:
                description: the minimum number of instances for the resource.
            max_count:
                description: the maximum number of instances for the resource.
            recurrence_frequency:
                default: None
                description:
                - How often the schedule profile should take effect.
                - If this value is Week, meaning each week will have the same set of profiles.
                - This element is not used if the FixedDate element is used.
                choices:
                - None
                - Second
                - Minute
                - Hour
                - Day
                - Week
                - Month
                - Year
            recurrence_timezone:
                description:
                - The timezone of repeating times at which this profile begins.
                - This element is not used if the FixedDate element is used.
            recurrence_days:
                description:
                - The days of repeating times at which this profile begins.
                - This element is not used if the FixedDate element is used.
            recurrence_hours:
                description:
                - The hours of repeating times at which this profile begins.
                - This element is not used if the FixedDate element is used.
            recurrence_mins:
                description:
                - The mins of repeating times at which this profile begins.
                - This element is not used if the FixedDate element is used.
            fixed_date_timezone:
                description:
                - The specific date-time timezone for the profile.
                - This element is not used if the Recurrence element is used.
            fixed_date_start:
                description:
                - The specific date-time start for the profile.
                - This element is not used if the Recurrence element is used.
            fixed_date_end:
                description:
                - The specific date-time end for the profile.
                - This element is not used if the Recurrence element is used.
            rules:
                description:
                - The collection of rules that provide the triggers and parameters for the scaling action.
                - A maximum of 10 rules can be specified.
                suboptions:
                    time_aggregation:
                        default: Average
                        description: How the data that is collected should be combined over time.
                        choices:
                        - Average
                        - Minimum
                        - Maximum
                        - Total
                        - Count
                    time_window:
                        required: true
                        description:
                        - The range of time(minutes) in which instance data is collected.
                        - This value must be greater than the delay in metric collection, which can vary from resource-to-resource.
                        - Must be between 5 ~ 720.
                    direction:
                        description: Whether the scaling action increases or decreases the number of instances.
                        choices:
                        - Increase
                        - Decrease
                    metric_name:
                        required: true
                        description: The name of the metric that defines what the rule monitors.
                    metric_resource_uri:
                        description: The resource identifier of the resource the rule monitors.
                    value:
                        description:
                        - The number of instances that are involved in the scaling action.
                        - This value must be 1 or greater.
                    operator:
                        default: GreaterThan
                        description: The operator that is used to compare the metric data and the threshold.
                        choices:
                        - Equals
                        - NotEquals
                        - GreaterThan
                        - GreaterThanOrEqual
                        - LessThan
                        - LessThanOrEqual
                    cooldown:
                        description:
                        - The amount of time (minutes) to wait since the last scaling action before this action occurs.
                        - It must be between 1 ~ 10080.
                    time_grain:
                        required: true
                        description:
                        - The granularity(minutes) of metrics the rule monitors.
                        - Must be one of the predefined values returned from metric definitions for the metric.
                        - Must be between 1 ~ 720.
                    statistic:
                        default: Average
                        description: How the metrics from multiple instances are combined.
                        choices:
                        - Average
                        - Min
                        - Max
                        - Sum
                    threshold:
                        default: 70
                        description: The threshold of the metric that triggers the scale action.
                    type:
                        description:  The type of action that should occur when the scale rule fires.
                        choices:
                        - PercentChangeCount
                        - ExactCount
                        - ChangeCount
    notifications:
        description: the collection of notifications.
        suboptions:
            custom_emails:
                description: the custom e-mails list. This value can be null or empty, in which case this attribute will be ignored.
            send_to_subscription_administrator:
                type: bool
                description: A value indicating whether to send email to subscription administrator.
            webhooks:
                description: The list of webhook notifications service uri.
            send_to_subscription_co_administrators:
                type: bool
                description: A value indicating whether to send email to subscription co-administrators.
    state:
        default: present
        description: Assert the state of the virtual network. Use C(present) to create or update and C(absent) to delete.
        choices:
        - present
        - absent
    location:
        description: location of the resource.
    name:
        required: true
        description: name of the resource.


extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
- name: Create an auto scale
  azure_rm_autoscale:
      target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachineScaleSets/myVmss"
      enabled: true
      profiles:
      - count: '1'
        recurrence_days:
        - Monday
        name: Auto created scale condition
        recurrence_timezone: China Standard Time
        recurrence_mins:
        - '0'
        min_count: '1'
        max_count: '1'
        recurrence_frequency: Week
        recurrence_hours:
        - '18'
      name: scale
      resource_group: myResourceGroup

- name: Create an auto scale with compicated profile
  azure_rm_autoscale:
      target: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachineScaleSets
               /myVmss"
      enabled: true
      profiles:
      - count: '1'
        recurrence_days:
        - Monday
        name: Auto created scale condition 0
        rules:
        - Time_aggregation: Average
          time_window: 10
          direction: Increase
          metric_name: Percentage CPU
          metric_resource_uri: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtua
                                lMachineScaleSets/vmss"
          value: '1'
          threshold: 70
          cooldown: 5
          time_grain: 1
          statistic: Average
          operator: GreaterThan
          type: ChangeCount
        max_count: '1'
        recurrence_mins:
        - '0'
        min_count: '1'
        recurrence_timezone: China Standard Time
        recurrence_frequency: Week
        recurrence_hours:
        - '6'
      notifications:
      - email_admin: True
        email_co_admin: False
        custom_emails:
        - yuwzho@microsoft.com
      name: scale
      resource_group: myResourceGroup

- name: Delete an Azure Auto Scale Setting
  azure_rm_autoscale:
    state: absent
    resource_group: myResourceGroup
    name: scale
'''

RETURN = '''
state:
    description: Current state of the resource.
    returned: always
    type: dict
    sample: {
        "changed": false,
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
                                                t.Compute/virtualMachineScaleSets/MyVmss",
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
    }
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils._text import to_native
from datetime import timedelta

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.monitor.models import WebhookNotification, EmailNotification, AutoscaleNotification, RecurrentSchedule, MetricTrigger, \
        ScaleAction, AutoscaleSettingResource, AutoscaleProfile, ScaleCapacity, TimeWindow, Recurrence, ScaleRule
except ImportError:
    # This is handled in azure_rm_common
    pass


# duplicated in azure_rm_autoscale_facts
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


rule_spec = dict(
    metric_name=dict(type='str', required=True),
    metric_resource_uri=dict(type='str'),
    time_grain=dict(type='float', required=True),
    statistic=dict(type='str', choices=['Average', 'Min', 'Max', 'Sum'], default='Average'),
    time_window=dict(type='float', required=True),
    time_aggregation=dict(type='str', choices=['Average', 'Minimum', 'Maximum', 'Total', 'Count'], default='Average'),
    operator=dict(type='str',
                  choices=['Equals', 'NotEquals', 'GreaterThan', 'GreaterThanOrEqual', 'LessThan', 'LessThanOrEqual'],
                  default='GreaterThan'),
    threshold=dict(type='float', default=70),
    direction=dict(type='str', choices=['Increase', 'Decrease']),
    type=dict(type='str', choices=['PercentChangeCount', 'ExactCount', 'ChangeCount']),
    value=dict(type='str'),
    cooldown=dict(type='float')
)


profile_spec = dict(
    name=dict(type='str', required=True),
    count=dict(type='str', required=True),
    max_count=dict(type='str'),
    min_count=dict(type='str'),
    rules=dict(type='list', elements='dict', options=rule_spec),
    fixed_date_timezone=dict(type='str'),
    fixed_date_start=dict(type='str'),
    fixed_date_end=dict(type='str'),
    recurrence_frequency=dict(type='str', choices=['None', 'Second', 'Minute', 'Hour', 'Day', 'Week', 'Month', 'Year'], default='None'),
    recurrence_timezone=dict(type='str'),
    recurrence_days=dict(type='list', elements='str'),
    recurrence_hours=dict(type='list', elements='str'),
    recurrence_mins=dict(type='list', elements='str')
)


notification_spec = dict(
    send_to_subscription_administrator=dict(type='bool', aliases=['email_admin'], default=False),
    send_to_subscription_co_administrators=dict(type='bool', aliases=['email_co_admin'], default=False),
    custom_emails=dict(type='list', elements='str'),
    webhooks=dict(type='list', elements='str')
)


class AzureRMAutoScale(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            target=dict(type='raw'),
            profiles=dict(type='list', elements='dict', options=profile_spec),
            enabled=dict(type='bool', default=True),
            notifications=dict(type='list', elements='dict', options=notification_spec)
        )

        self.results = dict(
            changed=False
        )

        required_if = [
            ('state', 'present', ['target', 'profiles'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.tags = None
        self.target = None
        self.profiles = None
        self.notifications = None
        self.enabled = None

        super(AzureRMAutoScale, self).__init__(self.module_arg_spec, supports_check_mode=True, required_if=required_if)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = None
        changed = False

        self.log('Fetching auto scale settings {0}'.format(self.name))
        results = self.get_auto_scale()
        if results and self.state == 'absent':
            # delete
            changed = True
            if not self.check_mode:
                self.delete_auto_scale()
        elif self.state == 'present':

            if not self.location:
                # Set default location
                resource_group = self.get_resource_group(self.resource_group)
                self.location = resource_group.location

            resource_id = self.target
            if isinstance(self.target, dict):
                resource_id = format_resource_id(val=self.target['name'],
                                                 subscription_id=self.target.get('subscription_id') or self.subscription_id,
                                                 namespace=self.target['namespace'],
                                                 types=self.target['types'],
                                                 resource_group=self.target.get('resource_group') or self.resource_group)
            self.target = resource_id
            resource_name = self.name

            def create_rule_instance(params):
                rule = params.copy()
                rule['metric_resource_uri'] = rule.get('metric_resource_uri', self.target)
                rule['time_grain'] = timedelta(minutes=rule.get('time_grain', 0))
                rule['time_window'] = timedelta(minutes=rule.get('time_window', 0))
                rule['cooldown'] = timedelta(minutes=rule.get('cooldown', 0))
                return ScaleRule(metric_trigger=MetricTrigger(**rule), scale_action=ScaleAction(**rule))

            profiles = [AutoscaleProfile(name=p.get('name'),
                                         capacity=ScaleCapacity(minimum=p.get('min_count'),
                                                                maximum=p.get('max_count'),
                                                                default=p.get('count')),
                                         rules=[create_rule_instance(r) for r in p.get('rules') or []],
                                         fixed_date=TimeWindow(time_zone=p.get('fixed_date_timezone'),
                                                               start=p.get('fixed_date_start'),
                                                               end=p.get('fixed_date_end')) if p.get('fixed_date_timezone') else None,
                                         recurrence=Recurrence(frequency=p.get('recurrence_frequency'),
                                                               schedule=(RecurrentSchedule(time_zone=p.get('recurrence_timezone'),
                                                                                           days=p.get('recurrence_days'),
                                                                                           hours=p.get('recurrence_hours'),
                                                                                           minutes=p.get('recurrence_mins'))))
                                         if p.get('recurrence_frequency') and p['recurrence_frequency'] != 'None' else None)
                        for p in self.profiles or []]

            notifications = [AutoscaleNotification(email=EmailNotification(**n),
                                                   webhooks=[WebhookNotification(service_uri=w) for w in n.get('webhooks') or []])
                             for n in self.notifications or []]

            if not results:
                # create new
                changed = True
            else:
                # check changed
                resource_name = results.autoscale_setting_resource_name or self.name
                update_tags, tags = self.update_tags(results.tags)
                if update_tags:
                    changed = True
                    self.tags = tags
                if self.target != results.target_resource_uri:
                    changed = True
                if self.enabled != results.enabled:
                    changed = True
                profile_result_set = set([str(profile_to_dict(p)) for p in results.profiles or []])
                if profile_result_set != set([str(profile_to_dict(p)) for p in profiles]):
                    changed = True
                notification_result_set = set([str(notification_to_dict(n)) for n in results.notifications or []])
                if notification_result_set != set([str(notification_to_dict(n)) for n in notifications]):
                    changed = True
            if changed:
                # construct the instance will be send to create_or_update api
                results = AutoscaleSettingResource(location=self.location,
                                                   tags=self.tags,
                                                   profiles=profiles,
                                                   notifications=notifications,
                                                   enabled=self.enabled,
                                                   autoscale_setting_resource_name=resource_name,
                                                   target_resource_uri=self.target)
                if not self.check_mode:
                    results = self.create_or_update_auto_scale(results)
                # results should be the dict of the instance
        self.results = auto_scale_to_dict(results)
        self.results['changed'] = changed
        return self.results

    def get_auto_scale(self):
        try:
            return self.monitor_client.autoscale_settings.get(self.resource_group, self.name)
        except Exception as exc:
            self.log('Error: failed to get auto scale settings {0} - {1}'.format(self.name, str(exc)))
            return None

    def create_or_update_auto_scale(self, param):
        try:
            return self.monitor_client.autoscale_settings.create_or_update(self.resource_group, self.name, param)
        except Exception as exc:
            self.fail("Error creating auto scale settings {0} - {1}".format(self.name, str(exc)))

    def delete_auto_scale(self):
        self.log('Deleting auto scale settings {0}'.format(self.name))
        try:
            return self.monitor_client.autoscale_settings.delete(self.resource_group, self.name)
        except Exception as exc:
            self.fail("Error deleting auto scale settings {0} - {1}".format(self.name, str(exc)))


def main():
    AzureRMAutoScale()


if __name__ == '__main__':
    main()
