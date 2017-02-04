#!/usr/bin/python
# (c) 2017, NetApp, Inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

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
        required: true
        description:
        - Whether the specified schedule should exist or not.
        choices: ['present', 'absent']

    pause:
        required: false
        type: bool
        description:
        - Pause / Resume a schedule

    recurring:
        required: false
        type: bool
        description:
        - Define if the schedule should recur

    time_interval_days:
        description: time interval in days
        required: false
        type: int
        default: 1

    time_interval_hours:
        description: time interval in hours
        required: false
        type: int
        default: 0

    time_interval_minutes:
        description: time interval in minutes
        required: false
        type: int
        default: 0

    name:
        required: true
        description:
        - Name for the snapshot schedule

    new_name:
        required: false
        description:
        - New name for the snapshot schedule
        default: None

    snapshot_name:
        required: false
        description:
        - Name for the created snapshots

    volumes:
        required: false
        type: list
        description:
        - Volume IDs that you want to set the snapshot schedule for.
        - At least 1 volume ID is required for creating a new schedule.
        - required when C(state=present)

    retention:
        required: false
        description:
        - Retention period for the snapshot.
        - Format is HH:mm:ss

    schedule_id:
        required: false
        description:
        - The schedule ID for the schedule that you want to update or delete.

    starting_date:
        required: false
        format: 2016--12--01T00:00:00Z
        description:
        - starting date for the schedule
        - required when C(state=present)
        - Please use two '-' in the above format, or you may see an error- TypeError, is not JSON serializable description
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


"""

import logging
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SolidFireSnapShotSchedule(object):

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            new_name=dict(required=False, type='str', default=None),

            time_interval_days=dict(required=False, type='int', default=1),
            time_interval_hours=dict(required=False, type='int', default=0),
            time_interval_minutes=dict(required=False, type='int', default=0),

            pause=dict(required=False, type='bool'),
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
        self.new_name = p['new_name']

        # self.interval = p['interval']

        self.time_interval_days = p['time_interval_days']
        self.time_interval_hours = p['time_interval_hours']
        self.time_interval_minutes = p['time_interval_minutes']

        self.pause = p['pause']
        self.recurring = p['recurring']

        self.starting_date = p['starting_date']
        if self.starting_date is not None:
            self.starting_date = self.starting_date.replace("--", "-")

        self.snapshot_name = p['snapshot_name']
        self.volumes = p['volumes']
        self.retention = p['retention']

        self.schedule_id = p['schedule_id']

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
        logger.debug('Creating schedule %s', self.name)

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
            sched.paused = self.pause
            sched.recurring = self.recurring
            sched.starting_date = self.starting_date

            self.sfe.create_schedule(schedule=sched)

        except:
            err = get_exception()
            logger.exception('Error creating schedule %s : %s',
                             self.name, str(err))
            raise

    def delete_schedule(self):
        logger.debug('Deleting schedule %s', self.schedule_id)

        try:
            get_schedule_result = self.sfe.get_schedule(schedule_id=self.schedule_id)
            sched = get_schedule_result.schedule
            sched.to_be_deleted = True
            self.sfe.modify_schedule(schedule=sched)

        except:
            err = get_exception()
            logger.exception('Error deleting schedule %s : %s', self.schedule_id, str(err))
            raise

    def update_schedule(self):
        logger.debug('Updating schedule %s', self.schedule_id)

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

            if self.volumes is not None:
                sched.schedule_info.volume_ids = self.volumes
            if self.retention is not None:
                sched.schedule_info.retention = self.retention
            if self.snapshot_name is not None:
                sched.schedule_info.snapshot_name = self.snapshot_name
            if self.new_name is not None:
                sched.name = self.new_name
            if self.pause is not None:
                sched.paused = self.pause
            if self.recurring is not None:
                sched.recurring = self.recurring
            if self.starting_date is not None:
                sched.starting_date = self.starting_date

            # Make API call
            self.sfe.modify_schedule(schedule=sched)

        except:
            err = get_exception()
            logger.exception('Error updating account %s : %s', self.schedule_id, str(err))
            raise

    def apply(self):
        changed = False
        schedule_exists = False
        update_schedule = False
        schedule_detail = self.get_schedule()

        if schedule_detail:
            schedule_exists = True

            if self.state == 'absent':
                logger.debug(
                    "CHANGED: schedule exists, but requested state is 'absent'")
                changed = True

            elif self.state == 'present':
                # Check if we need to update the account

                if self.retention is not None and schedule_detail.schedule_info.retention !=self.retention:
                    logger.debug("CHANGED: retention needs to be updated")
                    update_schedule = True
                    changed = True

                elif self.new_name is not None and schedule_detail.name !=self.new_name:
                    logger.debug("CHANGED: schedule needs to be renamed")
                    update_schedule = True
                    changed = True

                elif self.snapshot_name is not None and schedule_detail.schedule_info.snapshot_name != self.snapshot_name:
                    logger.debug("CHANGED: snapshot name needs to be updated")
                    update_schedule = True
                    changed = True

                elif self.volumes is not None and schedule_detail.schedule_info.volume_ids != self.volumes:
                    logger.debug("CHANGED: snapshot name needs to be updated")
                    update_schedule = True
                    changed = True

                elif self.pause is not None and schedule_detail.paused != self.pause:
                    logger.debug("CHANGED: Schedule pause status needs to be updated")
                    update_schedule = True
                    changed = True

                elif self.recurring is not None and schedule_detail.recurring != self.recurring:
                    logger.debug("CHANGED: Recurring status needs to be updated")
                    update_schedule = True
                    changed = True

                elif self.starting_date is not None and schedule_detail.starting_date != self.starting_date:
                    logger.debug("CHANGED: Starting date needs to be updated")
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
                        logger.debug("CHANGED: schedule interval needs to be updated")
                        update_schedule = True
                        changed = True

        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: schedule does not exist, but requested state is "
                    "'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not schedule_exists:
                        self.create_schedule()
                    elif update_schedule:
                        self.update_schedule()

                elif self.state == 'absent':
                    self.delete_schedule()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireSnapShotSchedule()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

if __name__ == '__main__':
    main()
