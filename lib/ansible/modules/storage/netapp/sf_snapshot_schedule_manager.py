#!/usr/bin/python
# (c) 2016, NetApp, Inc
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

#!/usr/bin/python

DOCUMENTATION = '''

module: sf_snapshot_schedule_manager

short_description: Manage SolidFire snapshot schedules
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, destroy, or update accounts on SolidFire
    - auth_basic

options:

    hostname:
        required: true
        description:
        - hostname

    username:
        required: true
        description:
        - username

    password:
        required: true
        description:
        - password

    action:
        required: true
        description:
        - Create, Delete, or Update an account with the passed parameters
        choices: ['create', 'delete', 'update']

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

    interval:
        required: false
        note: required when action == 'create'
        description:
        -   In order for automatic snapshots to be taken, you need to create a schedule.
        choices: ['time_interval']

    time_interval_days:
        description: time interval in days
        required: false
        type: int

    time_interval_hours:
        description: time interval in hours
        required: false
        type: int

    time_interval_minutes:
        description: time interval in minutes
        required: false
        type: int


    name:
        required: false
        note: required when action == 'create'
        description:
        - Name for the snapshot

    snapshot_name:
        required: false
        description:
        - Name for the created snapshots

    volumes:
        required: false
        note: required when action == create
        type: list
        description:
        - Volume IDs that you want to set the snapshot schedule for.
        - At least 1 volume ID is required for creating a new schedule.

    retention:
        required: false
        note: HH:mm:ss format
        description: Retention period for the snapshot.

    schedule_id:
        required: false
        note: required when action == 'update'
        description:
        - The schedule ID for the schedule that you want to update or delete.

    starting_date:
        required: false
        format: 2016--12--01T00:00:00Z
        note:
        -   required when action == 'create'
        -   Please use two '-' in the above format, or you may see the following error:
        -   TypeError: datetime.datetime(2016, 12, 1, 0, 0) is not JSON serializable description. The starting date and time for the schedule.

'''

EXAMPLES = """
   - name: Create Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: create
       name: AnsibleSnapshotSchedule
       time_interval_days: 1
       starting_date: 2016--12--01T00:00:00Z
       volumes: 7

   - name: Update Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: update
       schedule_id: 6
       recurring: True
       snapshot_name: AnsibleSnapshots

   - name: Delete Snapshot schedule
     sf_snapshot_schedule_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: delete
       schedule_id: 6
"""

RETURN = """
msg:
    description: Successful creation of schedule
    returned: success
    type: string
    sample: '{"changed": true, "key": value}'

msg:
    description: Successful update of schedule
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successful removal of schedule
    returned: success
    type: string
    sample: '{"changed": true}'

"""

'''

    Todo:

        Before updating a schedule, check the previous (current) attributes to currently report
        the 'changed' property.

        Add support for weekly and monthly time intervals.

'''
import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory
from solidfire.custom.models import TimeIntervalFrequency
from solidfire.models import Schedule, ScheduleInfo


class SolidFireSnapShotSchedule(object):

    def __init__(self):

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'update']),

                # interval is required when action == create
                # interval=dict(choices=['time_interval', 'weekly', 'monthly']),

                time_interval_days=dict(required=False, type='int', default=1),
                time_interval_hours=dict(required=False, type='int', default=0),
                time_interval_minutes=dict(required=False, type='int', default=0),

                pause=dict(required=False, type='bool'),
                recurring=dict(required=False, type='bool'),

                starting_date=dict(type='str'),

                name=dict(type='str'),

                snapshot_name=dict(required=False, type='str'),
                volumes=dict(required=False, type='list'),
                retention=dict(required=False, type='str'),

                schedule_id=dict(type='int'),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['name', 'starting_date', 'volumes']),
                ('action', 'update', ['schedule_id'])
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        # self.interval = p['interval']

        self.time_interval_days = p['time_interval_days']
        self.time_interval_hours = p['time_interval_hours']
        self.time_interval_minutes = p['time_interval_minutes']

        self.pause = p['pause']
        self.recurring = p['recurring']

        self.starting_date = p['starting_date']
        if self.starting_date is not None:
            self.starting_date = self.starting_date.replace("--", "-")

        self.name = p['name']

        self.snapshot_name = p['snapshot_name']
        self.volumes = p['volumes']
        self.retention = p['retention']

        self.schedule_id = p['schedule_id']

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def create_schedule(self):
        logger.debug('Creating schedule %s', self.name)

        try:
            sched = Schedule()
            # if self.interval == 'time_interval':
            sched.frequency = TimeIntervalFrequency(days=self.time_interval_days, hours=self.time_interval_hours,
                                                    minutes=self.time_interval_minutes)

            # Create schedule
            sched.name = self.name
            sched.schedule_info = ScheduleInfo(
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
            sched.frequency = TimeIntervalFrequency(days=self.time_interval_days, hours=self.time_interval_hours,
                                                    minutes=self.time_interval_minutes)

            if self.volumes is not None:
                sched.schedule_info.volume_ids = self.volumes
            if self.retention is not None:
                sched.schedule_info.retention = self.retention
            if self.snapshot_name is not None:
                sched.schedule_info.snapshot_name = self.snapshot_name

            sched.name = self.name

            sched.paused = self.pause
            sched.recurring = self.recurring
            sched.starting_date = self.starting_date

            # Make API call
            self.sfe.modify_schedule(schedule=sched)

        except:
            err = get_exception()
            logger.exception('Error updating account %s : %s', self.schedule_id, str(err))
            raise

    def apply(self):
        changed = False

        if self.action == 'create':
            self.create_schedule()
            changed = True

        elif self.action == 'delete':
            self.delete_schedule()
            changed = True

        elif self.action == 'update':
            self.update_schedule()
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireSnapShotSchedule()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

main()
