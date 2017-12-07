#!/usr/bin/python
# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: sf_snapshot_schedule_manager

short_description: Manage SolidFire snapshot schedules
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, destroy, or update accounts on SolidFire

options:

    state:
        description:
        - Whether the specified schedule should exist or not.
        required: true
        choices: ['present', 'absent']

    paused:
        description:
        - Pause / Resume a schedule.
        required: false

    recurring:
        description:
        - Should the schedule recur?
        required: false

    time_interval_days:
        description: Time interval in days.
        required: false
        default: 1

    time_interval_hours:
        description: Time interval in hours.
        required: false
        default: 0

    time_interval_minutes:
        description: Time interval in minutes.
        required: false
        default: 0

    name:
        description:
        - Name for the snapshot schedule.
        required: true

    snapshot_name:
        description:
        - Name for the created snapshots.
        required: false

    volumes:
        description:
        - Volume IDs that you want to set the snapshot schedule for.
        - At least 1 volume ID is required for creating a new schedule.
        - required when C(state=present)
        required: false

    retention:
        description:
        - Retention period for the snapshot.
        - Format is 'HH:mm:ss'.
        required: false

    schedule_id:
        description:
        - The schedule ID for the schedule that you want to update or delete.
        required: false

    starting_date:
        description:
        - Starting date for the schedule.
        - Required when C(state=present).
        - Please use two '-' in the above format, or you may see an error- TypeError, is not JSON serializable description.
        - "Format: C(2016--12--01T00:00:00Z)"
        required: false
'''

EXAMPLES = """
   - name: Create Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: Schedule_A
       time_interval_days: 1
       starting_date: 2016--12--01T00:00:00Z
       volumes: 7

   - name: Update Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       schedule_id: 6
       recurring: True
       snapshot_name: AnsibleSnapshots

   - name: Delete Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: absent
       schedule_id: 6
"""

RETURN = """

schedule_id:
    description: Schedule ID of the newly created schedule
    returned: success
    type: string
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireSnapShotSchedule(object):

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),

            time_interval_days=dict(required=False, type='int', default=1),
            time_interval_hours=dict(required=False, type='int', default=0),
            time_interval_minutes=dict(required=False, type='int', default=0),

            paused=dict(required=False, type='bool'),
            recurring=dict(required=False, type='bool'),

            starting_date=dict(type='str'),

            snapshot_name=dict(required=False, type='str'),
            volumes=dict(required=False, type='list'),
            retention=dict(required=False, type='str'),

            schedule_id=dict(type='int'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['starting_date', 'volumes'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']

        # self.interval = p['interval']

        self.time_interval_days = p['time_interval_days']
        self.time_interval_hours = p['time_interval_hours']
        self.time_interval_minutes = p['time_interval_minutes']

        self.paused = p['paused']
        self.recurring = p['recurring']

        self.starting_date = p['starting_date']
        if self.starting_date is not None:
            self.starting_date = self.starting_date.replace("--", "-")

        self.snapshot_name = p['snapshot_name']
        self.volumes = p['volumes']
        self.retention = p['retention']

        self.schedule_id = p['schedule_id']

        self.create_schedule_result = None

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_schedule(self):
        schedule_list = self.sfe.list_schedules()
        for schedule in schedule_list.schedules:
            if schedule.name == self.name:
                # Update self.schedule_id:
                if self.schedule_id is not None:
                    if schedule.schedule_id == self.schedule_id:
                        return schedule
                else:
                    self.schedule_id = schedule.schedule_id
                    return schedule

        return None

    def create_schedule(self):

        try:
            sched = netapp_utils.Schedule()
            # if self.interval == 'time_interval':
            sched.frequency = netapp_utils.TimeIntervalFrequency(days=self.time_interval_days,
                                                                 hours=self.time_interval_hours,
                                                                 minutes=self.time_interval_minutes)

            # Create schedule
            sched.name = self.name
            sched.schedule_info = netapp_utils.ScheduleInfo(
                volume_ids=self.volumes,
                snapshot_name=self.snapshot_name,
                retention=self.retention
            )
            sched.paused = self.paused
            sched.recurring = self.recurring
            sched.starting_date = self.starting_date

            self.create_schedule_result = self.sfe.create_schedule(schedule=sched)

        except Exception as e:
            self.module.fail_json(msg='Error creating schedule %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_schedule(self):

        try:
            get_schedule_result = self.sfe.get_schedule(schedule_id=self.schedule_id)
            sched = get_schedule_result.schedule
            sched.to_be_deleted = True
            self.sfe.modify_schedule(schedule=sched)

        except Exception as e:
            self.module.fail_json(msg='Error deleting schedule %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def update_schedule(self):

        try:
            get_schedule_result = self.sfe.get_schedule(schedule_id=self.schedule_id)
            sched = get_schedule_result.schedule

            # Update schedule properties

            # if self.interval == 'time_interval':
            temp_frequency = netapp_utils.TimeIntervalFrequency(days=self.time_interval_days,
                                                                hours=self.time_interval_hours,
                                                                minutes=self.time_interval_minutes)

            if sched.frequency.days != temp_frequency.days or \
                sched.frequency.hours != temp_frequency.hours \
                    or sched.frequency.minutes != temp_frequency.minutes:
                sched.frequency = temp_frequency

            sched.name = self.name
            if self.volumes is not None:
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
            self.module.fail_json(msg='Error updating schedule %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        schedule_exists = False
        update_schedule = False
        schedule_detail = self.get_schedule()

        if schedule_detail:
            schedule_exists = True

            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                # Check if we need to update the account

                if self.retention is not None and schedule_detail.schedule_info.retention != self.retention:
                    update_schedule = True
                    changed = True

                elif schedule_detail.name != self.name:
                    update_schedule = True
                    changed = True

                elif self.snapshot_name is not None and schedule_detail.schedule_info.snapshot_name != self.snapshot_name:
                    update_schedule = True
                    changed = True

                elif self.volumes is not None and schedule_detail.schedule_info.volume_ids != self.volumes:
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

                elif self.time_interval_minutes is not None or self.time_interval_hours is not None \
                        or self.time_interval_days is not None:

                    temp_frequency = netapp_utils.TimeIntervalFrequency(days=self.time_interval_days,
                                                                        hours=self.time_interval_hours,
                                                                        minutes=self.time_interval_minutes)

                    if schedule_detail.frequency.days != temp_frequency.days or \
                            schedule_detail.frequency.hours != temp_frequency.hours \
                            or schedule_detail.frequency.minutes != temp_frequency.minutes:
                        update_schedule = True
                        changed = True

        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                # Skip changes
                pass
            else:
                if self.state == 'present':
                    if not schedule_exists:
                        self.create_schedule()
                    elif update_schedule:
                        self.update_schedule()

                elif self.state == 'absent':
                    self.delete_schedule()

        if self.create_schedule_result is not None:
            self.module.exit_json(changed=changed, schedule_id=self.create_schedule_result.schedule_id)
        else:
            self.module.exit_json(changed=changed)


def main():
    v = SolidFireSnapShotSchedule()
    v.apply()

if __name__ == '__main__':
    main()
