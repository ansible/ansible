#!/usr/bin/python
# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Element SW Software Snapshot Schedule"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_snapshot_schedule

short_description: NetApp Element Software Snapshot Schedules
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, destroy, or update accounts on ElementSW

options:

    state:
        description:
        - Whether the specified schedule should exist or not.
        required: true
        choices: ['present', 'absent']

    paused:
        description:
        - Pause / Resume a schedule.
        type: bool

    recurring:
        description:
        - Should the schedule recur?
        type: bool

    schedule_type:
        description:
        - Schedule type for creating schedule.
        choices: ['DaysOfWeekFrequency','DaysOfMonthFrequency','TimeIntervalFrequency']

    time_interval_days:
        description: Time interval in days.
        default: 1

    time_interval_hours:
        description: Time interval in hours.
        default: 0

    time_interval_minutes:
        description: Time interval in minutes.
        default: 0

    days_of_week_weekdays:
        description: List of days of the week (Sunday to Saturday)

    days_of_week_hours:
        description: Time specified in hours
        default: 0

    days_of_week_minutes:
        description:  Time specified in minutes.
        default: 0

    days_of_month_monthdays:
        description: List of days of the month (1-31)

    days_of_month_hours:
        description: Time specified in hours
        default: 0

    days_of_month_minutes:
        description:  Time specified in minutes.
        default: 0

    name:
        description:
        - Name for the snapshot schedule.
        - It accepts either schedule_id or schedule_name
        - if name is digit, it will consider as schedule_id
        - If name is string, it will consider as schedule_name

    snapshot_name:
        description:
        - Name for the created snapshots.

    volumes:
        description:
        - Volume IDs that you want to set the snapshot schedule for.
        - It accepts both volume_name and volume_id

    account_id:
        description:
        - Account ID for the owner of this volume.
        - It accepts either account_name or account_id
        - if account_id is digit, it will consider as account_id
        - If account_id is string, it will consider as account_name

    retention:
        description:
        - Retention period for the snapshot.
        - Format is 'HH:mm:ss'.

    starting_date:
        description:
        - Starting date for the schedule.
        - Required when C(state=present).
        - "Format: C(2016-12-01T00:00:00Z)"


    password:
        description:
        - Element SW access account password
        aliases:
        - pass

    username:
        description:
        - Element SW access account user-name
        aliases:
        - user
'''

EXAMPLES = """
   - name: Create Snapshot schedule
     na_elementsw_snapshot_schedule:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: Schedule_A
       schedule_type: TimeIntervalFrequency
       time_interval_days: 1
       starting_date: '2016-12-01T00:00:00Z'
       volumes:
       - 7
       - test
       account_id: 1

   - name: Update Snapshot schedule
     na_elementsw_snapshot_schedule:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: Schedule_A
       schedule_type: TimeIntervalFrequency
       time_interval_days: 1
       starting_date: '2016-12-01T00:00:00Z'
       volumes:
       - 8
       - test1
       account_id: 1

   - name: Delete Snapshot schedule
     na_elementsw_snapshot_schedule:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       name: 6
"""

RETURN = """

schedule_id:
    description: Schedule ID of the newly created schedule
    returned: success
    type: str
"""
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    from solidfire.custom.models import DaysOfWeekFrequency, Weekday, DaysOfMonthFrequency
    from solidfire.common import ApiServerError
except Exception:
    HAS_SF_SDK = False


class ElementSWSnapShotSchedule(object):
    """
    Contains methods to parse arguments,
    derive details of ElementSW objects
    and send requests to ElementSW via
    the ElementSW SDK
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure SDK is installed
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            schedule_type=dict(required=False, choices=['DaysOfWeekFrequency', 'DaysOfMonthFrequency', 'TimeIntervalFrequency']),

            time_interval_days=dict(required=False, type='int', default=1),
            time_interval_hours=dict(required=False, type='int', default=0),
            time_interval_minutes=dict(required=False, type='int', default=0),

            days_of_week_weekdays=dict(required=False, type='list'),
            days_of_week_hours=dict(required=False, type='int', default=0),
            days_of_week_minutes=dict(required=False, type='int', default=0),

            days_of_month_monthdays=dict(required=False, type='list'),
            days_of_month_hours=dict(required=False, type='int', default=0),
            days_of_month_minutes=dict(required=False, type='int', default=0),

            paused=dict(required=False, type='bool'),
            recurring=dict(required=False, type='bool'),

            starting_date=dict(required=False, type='str'),

            snapshot_name=dict(required=False, type='str'),
            volumes=dict(required=False, type='list'),
            account_id=dict(required=False, type='str'),
            retention=dict(required=False, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['account_id', 'volumes', 'schedule_type']),
                ('schedule_type', 'DaysOfMonthFrequency', ['days_of_month_monthdays']),
                ('schedule_type', 'DaysOfWeekFrequency', ['days_of_week_weekdays'])

            ],
            supports_check_mode=True
        )

        param = self.module.params

        # set up state variables
        self.state = param['state']
        self.name = param['name']
        self.schedule_type = param['schedule_type']
        self.days_of_week_weekdays = param['days_of_week_weekdays']
        self.days_of_week_hours = param['days_of_week_hours']
        self.days_of_week_minutes = param['days_of_week_minutes']
        self.days_of_month_monthdays = param['days_of_month_monthdays']
        self.days_of_month_hours = param['days_of_month_hours']
        self.days_of_month_minutes = param['days_of_month_minutes']
        self.time_interval_days = param['time_interval_days']
        self.time_interval_hours = param['time_interval_hours']
        self.time_interval_minutes = param['time_interval_minutes']
        self.paused = param['paused']
        self.recurring = param['recurring']
        if self.schedule_type == 'DaysOfWeekFrequency':
            # Create self.weekday list if self.schedule_type is days_of_week
            if self.days_of_week_weekdays is not None:
                # Create self.weekday list if self.schedule_type is days_of_week
                self.weekdays = []
                for day in self.days_of_week_weekdays:
                    if str(day).isdigit():
                        # If id specified, return appropriate day
                        self.weekdays.append(Weekday.from_id(int(day)))
                    else:
                        # If name specified, return appropriate day
                        self.weekdays.append(Weekday.from_name(day.capitalize()))

        if self.state == 'present' and self.schedule_type is None:
            # Mandate schedule_type for create operation
            self.module.fail_json(
                msg="Please provide required parameter: schedule_type")

        # Mandate schedule name for delete operation
        if self.state == 'absent' and self.name is None:
            self.module.fail_json(
                msg="Please provide required parameter: name")

        self.starting_date = param['starting_date']
        self.snapshot_name = param['snapshot_name']
        self.volumes = param['volumes']
        self.account_id = param['account_id']
        self.retention = param['retention']
        self.create_schedule_result = None

        if HAS_SF_SDK is False:
            # Create ElementSW connection
            self.module.fail_json(msg="Unable to import the ElementSW Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)
            self.elementsw_helper = NaElementSWModule(self.sfe)

    def get_schedule(self):
        # Checking whether schedule id is exist or not
        # Return schedule details if found, None otherwise
        # If exist set variable self.name
        try:
            schedule_list = self.sfe.list_schedules()
        except ApiServerError:
            return None

        for schedule in schedule_list.schedules:
            if str(schedule.schedule_id) == self.name:
                self.name = schedule.name
                return schedule
            elif schedule.name == self.name:
                return schedule
        return None

    def get_account_id(self):
        # Validate account id
        # Return account_id if found, None otherwise
        try:
            account_id = self.elementsw_helper.account_exists(self.account_id)
            return account_id
        except ApiServerError:
            return None

    def get_volume_id(self):
        # Validate volume_ids
        # Return volume ids if found, fail if not found
        volume_ids = []
        for volume in self.volumes:
            volume_id = self.elementsw_helper.volume_exists(volume.strip(), self.account_id)
            if volume_id:
                volume_ids.append(volume_id)
            else:
                self.module.fail_json(msg='Specified volume %s does not exist' % volume)
        return volume_ids

    def get_frequency(self):
        # Configuring frequency depends on self.schedule_type
        frequency = None
        if self.schedule_type is not None and self.schedule_type == 'DaysOfWeekFrequency':
            if self.weekdays is not None:
                frequency = DaysOfWeekFrequency(weekdays=self.weekdays,
                                                hours=self.days_of_week_hours,
                                                minutes=self.days_of_week_minutes)
        elif self.schedule_type is not None and self.schedule_type == 'DaysOfMonthFrequency':
            if self.days_of_month_monthdays is not None:
                frequency = DaysOfMonthFrequency(monthdays=self.days_of_month_monthdays,
                                                 hours=self.days_of_month_hours,
                                                 minutes=self.days_of_month_minutes)
        elif self.schedule_type is not None and self.schedule_type == 'TimeIntervalFrequency':
            frequency = netapp_utils.TimeIntervalFrequency(days=self.time_interval_days,
                                                           hours=self.time_interval_hours,
                                                           minutes=self.time_interval_minutes)
        return frequency

    def is_same_schedule_type(self, schedule_detail):
        # To check schedule type is same or not
        if str(schedule_detail.frequency).split('(')[0] == self.schedule_type:
            return True
        else:
            return False

    def create_schedule(self):
        # Create schedule
        try:
            frequency = self.get_frequency()
            if frequency is None:
                self.module.fail_json(msg='Failed to create schedule frequency object - type %s parameters' % self.schedule_type)

            # Create schedule
            name = self.name
            schedule_info = netapp_utils.ScheduleInfo(
                volume_ids=self.volumes,
                snapshot_name=self.snapshot_name,
                retention=self.retention
            )

            sched = netapp_utils.Schedule(schedule_info, name, frequency)
            sched.paused = self.paused
            sched.recurring = self.recurring
            sched.starting_date = self.starting_date

            self.create_schedule_result = self.sfe.create_schedule(sched)

        except Exception as e:
            self.module.fail_json(msg='Error creating schedule %s: %s' % (self.name, to_native(e.message)),
                                  exception=traceback.format_exc())

    def delete_schedule(self, schedule_id):
        # delete schedule
        try:
            get_schedule_result = self.sfe.get_schedule(schedule_id=schedule_id)
            sched = get_schedule_result.schedule
            sched.to_be_deleted = True
            self.sfe.modify_schedule(schedule=sched)

        except Exception as e:
            self.module.fail_json(msg='Error deleting schedule %s: %s' % (self.name, to_native(e.message)),
                                  exception=traceback.format_exc())

    def update_schedule(self, schedule_id):
        # Update schedule
        try:
            get_schedule_result = self.sfe.get_schedule(schedule_id=schedule_id)
            sched = get_schedule_result.schedule
            # Update schedule properties
            sched.frequency = self.get_frequency()
            if sched.frequency is None:
                self.module.fail_json(msg='Failed to create schedule frequency object - type %s parameters' % self.schedule_type)

            if self.volumes is not None and len(self.volumes) > 0:
                sched.schedule_info.volume_ids = self.volumes
            if self.retention is not None:
                sched.schedule_info.retention = self.retention
            if self.snapshot_name is not None:
                sched.schedule_info.snapshot_name = self.snapshot_name
            if self.paused is not None:
                sched.paused = self.paused
            if self.recurring is not None:
                sched.recurring = self.recurring
            if self.starting_date is not None:
                sched.starting_date = self.starting_date

            # Make API call
            self.sfe.modify_schedule(schedule=sched)

        except Exception as e:
            self.module.fail_json(msg='Error updating schedule %s: %s' % (self.name, to_native(e.message)),
                                  exception=traceback.format_exc())

    def apply(self):
        # Perform pre-checks, call functions and exit

        changed = False
        update_schedule = False

        if self.account_id is not None:
            self.account_id = self.get_account_id()

        if self.state == 'present' and self.volumes is not None:
            if self.account_id:
                self.volumes = self.get_volume_id()
            else:
                self.module.fail_json(msg='Specified account id does not exist')

        # Getting the schedule details
        schedule_detail = self.get_schedule()

        if schedule_detail is None and self.state == 'present':
            if len(self.volumes) > 0:
                changed = True
            else:
                self.module.fail_json(msg='Specified volumes not on cluster')
        elif schedule_detail is not None:
            # Getting the schedule id
            if self.state == 'absent':
                changed = True
            else:
                # Check if we need to update the account
                if self.retention is not None and schedule_detail.schedule_info.retention != self.retention:
                    update_schedule = True
                    changed = True
                elif self.snapshot_name is not None and schedule_detail.schedule_info.snapshot_name != self.snapshot_name:
                    update_schedule = True
                    changed = True
                elif self.paused is not None and schedule_detail.paused != self.paused:
                    update_schedule = True
                    changed = True
                elif self.recurring is not None and schedule_detail.recurring != self.recurring:
                    update_schedule = True
                    changed = True
                elif self.starting_date is not None and schedule_detail.starting_date != self.starting_date:
                    update_schedule = True
                    changed = True
                elif self.volumes is not None and len(self.volumes) > 0:
                    for volumeID in schedule_detail.schedule_info.volume_ids:
                        if volumeID not in self.volumes:
                            update_schedule = True
                            changed = True

                temp_frequency = self.get_frequency()
                if temp_frequency is not None:
                    # Checking schedule_type changes
                    if self.is_same_schedule_type(schedule_detail):
                        # If same schedule type
                        if self.schedule_type == "TimeIntervalFrequency":
                            # Check if there is any change in schedule.frequency, If schedule_type is time_interval
                            if schedule_detail.frequency.days != temp_frequency.days or \
                               schedule_detail.frequency.hours != temp_frequency.hours or \
                               schedule_detail.frequency.minutes != temp_frequency.minutes:
                                update_schedule = True
                                changed = True
                        elif self.schedule_type == "DaysOfMonthFrequency":
                            # Check if there is any change in schedule.frequency, If schedule_type is days_of_month
                            if len(schedule_detail.frequency.monthdays) != len(temp_frequency.monthdays) or \
                               schedule_detail.frequency.hours != temp_frequency.hours or \
                               schedule_detail.frequency.minutes != temp_frequency.minutes:
                                update_schedule = True
                                changed = True
                            elif len(schedule_detail.frequency.monthdays) == len(temp_frequency.monthdays):
                                actual_frequency_monthday = schedule_detail.frequency.monthdays
                                temp_frequency_monthday = temp_frequency.monthdays
                                for monthday in actual_frequency_monthday:
                                    if monthday not in temp_frequency_monthday:
                                        update_schedule = True
                                        changed = True
                        elif self.schedule_type == "DaysOfWeekFrequency":
                            # Check if there is any change in schedule.frequency, If schedule_type is days_of_week
                            if len(schedule_detail.frequency.weekdays) != len(temp_frequency.weekdays) or \
                               schedule_detail.frequency.hours != temp_frequency.hours or \
                               schedule_detail.frequency.minutes != temp_frequency.minutes:
                                update_schedule = True
                                changed = True
                            elif len(schedule_detail.frequency.weekdays) == len(temp_frequency.weekdays):
                                actual_frequency_weekdays = schedule_detail.frequency.weekdays
                                temp_frequency_weekdays = temp_frequency.weekdays
                                if len([actual_weekday for actual_weekday, temp_weekday in
                                        zip(actual_frequency_weekdays, temp_frequency_weekdays) if actual_weekday != temp_weekday]) != 0:
                                    update_schedule = True
                                    changed = True
                    else:
                        update_schedule = True
                        changed = True
                else:
                    self.module.fail_json(msg='Failed to create schedule frequency object - type %s parameters' % self.schedule_type)

        result_message = " "
        if changed:
            if self.module.check_mode:
                # Skip changes
                result_message = "Check mode, skipping changes"
            else:
                if self.state == 'present':
                    if update_schedule:
                        self.update_schedule(schedule_detail.schedule_id)
                        result_message = "Snapshot Schedule modified"
                    else:
                        self.create_schedule()
                        result_message = "Snapshot Schedule created"
                elif self.state == 'absent':
                    self.delete_schedule(schedule_detail.schedule_id)
                    result_message = "Snapshot Schedule deleted"

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    v = ElementSWSnapShotSchedule()
    v.apply()


if __name__ == '__main__':
    main()
