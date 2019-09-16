#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_vcenter_statistics
short_description: Configures statistics on a vCenter server
description:
- This module can be used to configure the vCenter server statistics.
- The remaining settings can be configured with the module C(vmware_vcenter_settings).
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested with vCenter Server Appliance (vCSA) 6.5 and 6.7
requirements:
- python >= 2.6
- PyVmomi
options:
    interval_past_day:
        description:
            - Settings for vCenter server past day statistic collection.
            - 'Valid attributes are:'
            - '- C(enabled) (bool): Past day statistics collection enabled. (default: True)'
            - '- C(interval_minutes) (int): Interval duration (minutes). (choices: [1, 2, 3, 4, 5]) (default: 5)'
            - '- C(save_for_days) (int): Save for (days). (choices: [1, 2, 3, 4, 5]) (default: 1)'
            - '- C(level) (int): Statistics level. (choices: [1, 2, 3, 4]) (default: 1)'
        type: dict
    interval_past_week:
        description:
            - Settings for vCenter server past week statistic collection.
            - 'Valid attributes are:'
            - '- C(enabled) (bool): Past week statistics collection enabled. (default: True)'
            - '- C(interval_minutes) (int): Interval duration (minutes). (choices: [30]) (default: 30)'
            - '- C(save_for_weeks) (int): Save for (weeks). (choices: [1]) (default: 1)'
            - '- C(level) (int): Statistics level. (choices: [1, 2, 3, 4]) (default: 1)'
        type: dict
    interval_past_month:
        description:
            - Settings for vCenter server past month statistic collection.
            - 'Valid attributes are:'
            - '- C(enabled) (bool): Past month statistics collection enabled. (default: True)'
            - '- C(interval_hours) (int): Interval duration (hours). (choices: [2]) (default: 2)'
            - '- C(save_for_months) (int): Save for (months). (choices: [1]) (default: 1)'
            - '- C(level) (int): Statistics level. (choices: [1, 2, 3, 4]) (default: 1)'
        type: dict
    interval_past_year:
        description:
            - Settings for vCenter server past month statistic collection.
            - 'Valid attributes are:'
            - '- C(enabled) (bool): Past month statistics collection enabled. (default: True)'
            - '- C(interval_days) (int): Interval duration (days). (choices: [1]) (default: 1)'
            - '- C(save_for_years) (int): Save for (years). (choices: [1, 2, 3, 4, 5]) (default: 1)'
            - '- C(level) (int): Statistics level. (choices: [1, 2, 3, 4]) (default: 1)'
        type: dict
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Configure vCenter statistics
  vmware_vcenter_statistics:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    interval_past_day:
      enabled: true
      interval_minutes: 5
      save_for_days: 1
      level: 1
    interval_past_week:
      enabled: true
      level: 1
    interval_past_month:
      enabled: true
      level: 1
    interval_past_year:
      enabled: true
      save_for_years: 1
      level: 1
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about vCenter statistics settings
    returned: always
    type: dict
    sample: {
        "changed": false,
        "msg": "vCenter statistics already configured properly",
        "past_day_enabled": true,
        "past_day_interval": 5,
        "past_day_level": 1,
        "past_day_save_for": 1,
        "past_month_enabled": true,
        "past_month_interval": 2,
        "past_month_level": 1,
        "past_month_save_for": 1,
        "past_week_enabled": true,
        "past_week_interval": 30,
        "past_week_level": 1,
        "past_week_save_for": 1,
        "past_year_enabled": true,
        "past_year_interval": 1,
        "past_year_level": 1,
        "past_year_save_for": 1
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


# This is a helper class to sort the changes in a valid order
# "Greater than" means a change has to happen after another one.
# As an example, let's say self is daily (key == 1) and other is weekly (key == 2)
class ChangeHelper:
    def __init__(self, old, new):
        self.key = new.key
        self.old = old
        self.new = new

    def __eq__(self, other):
        return ((self.key, self.new.enabled, self.new.level) ==
                (other.key, other.new.enabled, other.new.level))

    def __gt__(self, other):
        if self.key < other.key:
            # You cannot disable daily if weekly is enabled, so later
            if self.new.enabled < other.old.enabled:
                return True
            # Enabling daily is OK if weekly is disabled
            elif self.new.enabled > other.old.enabled:
                return False
            # Otherwise, decreasing the daily level below the current weekly level has to be done later
            else:
                return self.new.level < other.old.level
        else:
            return not (other > self)

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __lt__(self, other):
        return not (self >= other)

    def __le__(self, other):
        return not (self > other)


class VmwareVcenterStatistics(PyVmomi):
    """Manage statistics for a vCenter server"""

    def __init__(self, module):
        super(VmwareVcenterStatistics, self).__init__(module)

        if not self.is_vcenter():
            self.module.fail_json(msg="You have to connect to a vCenter server!")

    def ensure(self):
        """Manage statistics for a vCenter server"""

        DAILY_COUNTER = 1
        WEEKLY_COUNTER = 2
        MONTHLY_COUNTER = 3
        YEARLY_COUNTER = 4

        result = dict(changed=False, msg='')
        past_day_enabled = self.params['interval_past_day'].get('enabled', True)
        past_day_seconds = self.params['interval_past_day'].get('interval_minutes', 5) * 60
        past_day_save_for_seconds = self.params['interval_past_day'].get('save_for_days', 1) * 86400
        past_day_level = self.params['interval_past_day'].get('level', 1)
        past_week_enabled = self.params['interval_past_week'].get('enabled', True)
        past_week_seconds = self.params['interval_past_week'].get('interval_minutes', 30) * 60
        past_week_save_for_seconds = self.params['interval_past_week'].get('save_for_weeks', 1) * 604800
        past_week_level = self.params['interval_past_week'].get('level', 1)
        past_month_enabled = self.params['interval_past_month'].get('enabled', True)
        past_month_seconds = self.params['interval_past_month'].get('interval_hours', 2) * 3600
        past_month_save_for_seconds = self.params['interval_past_month'].get('save_for_months', 1) * 2592000
        past_month_level = self.params['interval_past_month'].get('level', 1)
        past_year_enabled = self.params['interval_past_year'].get('enabled', True)
        past_year_seconds = self.params['interval_past_year'].get('interval_days', 1) * 86400
        past_year_save_for_seconds = self.params['interval_past_year'].get('save_for_years', 1) * 31536000
        past_year_level = self.params['interval_past_year'].get('level', 1)

        # Check if level options are valid
        if past_year_level > past_month_level:
            self.module.fail_json(msg="The statistics level for past year can't be higher than past month!")
        if past_month_level > past_week_level:
            self.module.fail_json(msg="The statistics level for past month can't be higher than past week!")
        if past_week_level > past_day_level:
            self.module.fail_json(msg="The statistics level for past week can't be higher than past day!")

        # Check if state options are valid
        if not past_day_enabled and (past_week_enabled or past_month_enabled or past_year_enabled):
            self.module.fail_json(msg="The intervals past week, month, and year need to be disabled as well!")
        if not past_week_enabled and (past_month_enabled or past_year_enabled):
            self.module.fail_json(msg="The intervals past month, and year need to be disabled as well!")
        if not past_month_enabled and past_year_enabled:
            self.module.fail_json(msg="The interval past year need to be disabled as well!")
        if past_year_enabled and (not past_day_enabled or not past_week_enabled or not past_month_enabled):
            self.module.fail_json(msg="The intervals past day, week, and month need to be enabled as well!")
        if past_month_enabled and (not past_day_enabled or not past_week_enabled):
            self.module.fail_json(msg="The intervals past day, and week need to be enabled as well!")
        if past_week_enabled and (not past_day_enabled):
            self.module.fail_json(msg="The intervals past day need to be enabled as well!")

        changed = False
        changed_list = []

        # Check statistics
        result['past_day_enabled'] = past_day_enabled
        result['past_day_interval'] = int(past_day_seconds / 60)
        result['past_day_save_for'] = int(past_day_save_for_seconds / 86400)
        result['past_day_level'] = past_day_level
        result['past_week_enabled'] = past_week_enabled
        result['past_week_interval'] = int(past_week_seconds / 60)
        result['past_week_save_for'] = int(past_week_save_for_seconds / 604800)
        result['past_week_level'] = past_week_level
        result['past_month_enabled'] = past_month_enabled
        result['past_month_interval'] = int(past_month_seconds / 3600)
        result['past_month_save_for'] = int(past_month_save_for_seconds / 2592000)
        result['past_month_level'] = past_month_level
        result['past_year_enabled'] = past_year_enabled
        result['past_year_interval'] = int(past_year_seconds / 86400)
        result['past_year_save_for'] = int(past_year_save_for_seconds / 31536000)
        result['past_year_level'] = past_year_level
        change_statistics_list = []
        perf_manager = self.content.perfManager
        for historical_interval in perf_manager.historicalInterval:
            # Statistics for past day
            if historical_interval.name == 'Past day' and (
                    historical_interval.samplingPeriod != past_day_seconds
                    or historical_interval.length != past_day_save_for_seconds
                    or historical_interval.level != past_day_level
                    or historical_interval.enabled != past_day_enabled
            ):
                changed = True
                changed_list.append("Past day interval")
                if historical_interval.enabled != past_day_enabled:
                    result['past_day_enabled_previous'] = historical_interval.enabled
                if historical_interval.samplingPeriod != past_day_seconds:
                    result['past_day_interval_previous'] = int(historical_interval.samplingPeriod / 60)
                if historical_interval.length != past_day_save_for_seconds:
                    result['past_day_save_for_previous'] = int(historical_interval.length / 86400)
                if historical_interval.level != past_day_level:
                    result['past_day_level_previous'] = historical_interval.level

                change_statistics_list.append(
                    ChangeHelper(
                        historical_interval,
                        vim.HistoricalInterval(
                            key=DAILY_COUNTER,
                            samplingPeriod=past_day_seconds,
                            name='Past day',
                            length=past_day_save_for_seconds,
                            level=past_day_level,
                            enabled=past_day_enabled
                        )
                    )
                )

            # Statistics for past week
            if historical_interval.name == 'Past week' and (
                    historical_interval.samplingPeriod != past_week_seconds
                    or historical_interval.length != past_week_save_for_seconds
                    or historical_interval.level != past_week_level
                    or historical_interval.enabled != past_week_enabled
            ):
                changed = True
                changed_list.append("Past week interval")
                if historical_interval.enabled != past_week_enabled:
                    result['past_week_enabled_previous'] = historical_interval.enabled
                if historical_interval.samplingPeriod != past_week_seconds:
                    result['past_week_interval_previous'] = int(historical_interval.samplingPeriod / 60)
                if historical_interval.length != past_week_save_for_seconds:
                    result['past_week_save_for_previous'] = int(historical_interval.length / 604800)
                if historical_interval.level != past_week_level:
                    result['past_week_level_previous'] = historical_interval.level

                change_statistics_list.append(
                    ChangeHelper(
                        historical_interval,
                        vim.HistoricalInterval(
                            key=WEEKLY_COUNTER,
                            samplingPeriod=past_week_seconds,
                            name='Past week',
                            length=past_week_save_for_seconds,
                            level=past_week_level,
                            enabled=past_week_enabled
                        )
                    )
                )

            # Statistics for past month
            if historical_interval.name == 'Past month' and (
                    historical_interval.samplingPeriod != past_month_seconds
                    or historical_interval.length != past_month_save_for_seconds
                    or historical_interval.level != past_month_level
                    or historical_interval.enabled != past_month_enabled
            ):
                changed = True
                changed_list.append("Past month interval")
                if historical_interval.enabled != past_month_enabled:
                    result['past_month_enabled_previous'] = historical_interval.enabled
                if historical_interval.samplingPeriod != past_month_seconds:
                    result['past_month_interval_previous'] = int(historical_interval.samplingPeriod / 3600)
                if historical_interval.length != past_month_save_for_seconds:
                    result['past_month_save_for_previous'] = int(historical_interval.length / 2592000)
                if historical_interval.level != past_month_level:
                    result['past_month_level_previous'] = historical_interval.level

                change_statistics_list.append(
                    ChangeHelper(
                        historical_interval,
                        vim.HistoricalInterval(
                            key=MONTHLY_COUNTER,
                            samplingPeriod=past_month_seconds,
                            name='Past month',
                            length=past_month_save_for_seconds,
                            level=past_month_level,
                            enabled=past_month_enabled
                        )
                    )
                )

            # Statistics for past year
            if historical_interval.name == 'Past year' and (
                    historical_interval.samplingPeriod != past_year_seconds
                    or historical_interval.length != past_year_save_for_seconds
                    or historical_interval.level != past_year_level
                    or historical_interval.enabled != past_year_enabled
            ):
                changed = True
                changed_list.append("Past year interval")
                if historical_interval.enabled != past_year_enabled:
                    result['past_year_enabled_previous'] = historical_interval.enabled
                if historical_interval.samplingPeriod != past_year_seconds:
                    result['past_year_interval_previous'] = int(historical_interval.samplingPeriod / 86400)
                if historical_interval.length != past_year_save_for_seconds:
                    result['past_year_save_for_previous'] = int(historical_interval.length / 31536000)
                if historical_interval.level != past_year_level:
                    result['past_year_level_previous'] = historical_interval.level

                change_statistics_list.append(
                    ChangeHelper(
                        historical_interval,
                        vim.HistoricalInterval(
                            key=YEARLY_COUNTER,
                            samplingPeriod=past_year_seconds,
                            name='Past year',
                            length=past_year_save_for_seconds,
                            level=past_year_level,
                            enabled=past_year_enabled
                        )
                    )
                )

        if changed:
            if self.module.check_mode:
                changed_suffix = ' would be changed'
            else:
                changed_suffix = ' changed'
            if len(changed_list) > 2:
                message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
            elif len(changed_list) == 2:
                message = ' and '.join(changed_list)
            elif len(changed_list) == 1:
                message = changed_list[0]
            message += changed_suffix
            if not self.module.check_mode:
                change_statistics_list.sort()
                for statistic in change_statistics_list:
                    self.update_perf_interval(perf_manager, statistic.new)
        else:
            message = "vCenter statistics already configured properly"
        result['changed'] = changed
        result['msg'] = message

        self.module.exit_json(**result)

    def update_perf_interval(self, perf_manager, statistic):
        """Update statistics interval"""
        try:
            perf_manager.UpdatePerfInterval(statistic)
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(
                msg="The set of arguments passed to the function is not specified correctly or "
                "the update does not conform to the rules: %s" % to_native(invalid_argument.msg)
            )


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        interval_past_day=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool', default=True),
                interval_minutes=dict(type='int', choices=[1, 2, 3, 4, 5], default=5),
                save_for_days=dict(type='int', choices=[1, 2, 3, 4, 5], default=1),
                level=dict(type='int', choices=[1, 2, 3, 4], default=1),
            ),
        ),
        interval_past_week=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool', default=True),
                interval_minutes=dict(type='int', choices=[30], default=30),
                save_for_weeks=dict(type='int', choices=[1], default=1),
                level=dict(type='int', choices=[1, 2, 3, 4], default=1),
            ),
        ),
        interval_past_month=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool', default=True),
                interval_hours=dict(type='int', choices=[2], default=2),
                save_for_months=dict(type='int', choices=[1], default=1),
                level=dict(type='int', choices=[1, 2, 3, 4], default=1),
            ),
        ),
        interval_past_year=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool', default=True),
                interval_days=dict(type='int', choices=[1], default=1),
                save_for_years=dict(type='int', choices=[1, 2, 3, 4, 5], default=1),
                level=dict(type='int', choices=[1, 2, 3, 4], default=1),
            ),
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    host_snmp = VmwareVcenterStatistics(module)
    host_snmp.ensure()


if __name__ == '__main__':
    main()
