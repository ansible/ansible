#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: proxysql_scheduler
version_added: "2.3"
author: "Ben Mildren (@bmildren)"
short_description: Adds or removes schedules from proxysql admin interface.
description:
   - The M(proxysql_scheduler) module adds or removes schedules using the
     proxysql admin interface.
options:
  active:
    description:
      - A schedule with I(active) set to C(False) will be tracked in the
        database, but will be never loaded in the in-memory data structures.
    default: True
  interval_ms:
    description:
      - How often (in millisecond) the job will be started. The minimum value
        for I(interval_ms) is 100 milliseconds.
    default: 10000
  filename:
    description:
      - Full path of the executable to be executed.
    required: True
  arg1:
    description:
      - Argument that can be passed to the job.
  arg2:
    description:
      - Argument that can be passed to the job.
  arg3:
    description:
      - Argument that can be passed to the job.
  arg4:
    description:
      - Argument that can be passed to the job.
  arg5:
    description:
      - Argument that can be passed to the job.
  comment:
    description:
      - Text field that can be used for any purposed defined by the user.
  state:
    description:
      - When C(present) - adds the schedule, when C(absent) - removes the
        schedule.
    choices: [ "present", "absent" ]
    default: present
  force_delete:
    description:
      - By default we avoid deleting more than one schedule in a single batch,
        however if you need this behaviour and you're not concerned about the
        schedules deleted, you can set I(force_delete) to C(True).
    default: False
extends_documentation_fragment:
  - proxysql.managing_config
  - proxysql.connectivity
'''

EXAMPLES = '''
---
# This example adds a schedule, it saves the scheduler config to disk, but
# avoids loading the scheduler config to runtime (this might be because
# several servers are being added and the user wants to push the config to
# runtime in a single batch using the M(proxysql_manage_config) module).  It
# uses supplied credentials to connect to the proxysql admin interface.

- proxysql_scheduler:
    login_user: 'admin'
    login_password: 'admin'
    interval_ms: 1000
    filename: "/opt/maintenance.py"
    state: present
    load_to_runtime: False

# This example removes a schedule, saves the scheduler config to disk, and
# dynamically loads the scheduler config to runtime.  It uses credentials
# in a supplied config file to connect to the proxysql admin interface.

- proxysql_scheduler:
    config_file: '~/proxysql.cnf'
    filename: "/opt/old_script.py"
    state: absent
'''

RETURN = '''
stdout:
    description: The schedule modified or removed from proxysql
    returned: On create/update will return the newly modified schedule, on
              delete it will return the deleted record.
    type: dict
    "sample": {
        "changed": true,
        "filename": "/opt/test.py",
        "msg": "Added schedule to scheduler",
        "schedules": [
            {
                "active": "1",
                "arg1": null,
                "arg2": null,
                "arg3": null,
                "arg4": null,
                "arg5": null,
                "comment": "",
                "filename": "/opt/test.py",
                "id": "1",
                "interval_ms": "10000"
            }
        ],
        "state": "present"
    }
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native

# ===========================================
# proxysql module specific support methods.
#


def perform_checks(module):
    if module.params["login_port"] < 0 \
       or module.params["login_port"] > 65535:
        module.fail_json(
            msg="login_port must be a valid unix port number (0-65535)"
        )

    if module.params["interval_ms"] < 100 \
       or module.params["interval_ms"] > 100000000:
        module.fail_json(
            msg="interval_ms must between 100ms & 100000000ms"
        )

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)


def save_config_to_disk(cursor):
    cursor.execute("SAVE SCHEDULER TO DISK")
    return True


def load_config_to_runtime(cursor):
    cursor.execute("LOAD SCHEDULER TO RUNTIME")
    return True


class ProxySQLSchedule(object):

    def __init__(self, module):
        self.state = module.params["state"]
        self.force_delete = module.params["force_delete"]
        self.save_to_disk = module.params["save_to_disk"]
        self.load_to_runtime = module.params["load_to_runtime"]
        self.active = module.params["active"]
        self.interval_ms = module.params["interval_ms"]
        self.filename = module.params["filename"]

        config_data_keys = ["arg1",
                            "arg2",
                            "arg3",
                            "arg4",
                            "arg5",
                            "comment"]

        self.config_data = dict((k, module.params[k])
                                for k in config_data_keys)

    def check_schedule_config(self, cursor):
        query_string = \
            """SELECT count(*) AS `schedule_count`
               FROM scheduler
               WHERE active = %s
                 AND interval_ms = %s
                 AND filename = %s"""

        query_data = \
            [self.active,
             self.interval_ms,
             self.filename]

        for col, val in iteritems(self.config_data):
            if val is not None:
                query_data.append(val)
                query_string += "\n  AND " + col + " = %s"

        cursor.execute(query_string, query_data)
        check_count = cursor.fetchone()
        return int(check_count['schedule_count'])

    def get_schedule_config(self, cursor):
        query_string = \
            """SELECT *
               FROM scheduler
               WHERE active = %s
                 AND interval_ms = %s
                 AND filename = %s"""

        query_data = \
            [self.active,
             self.interval_ms,
             self.filename]

        for col, val in iteritems(self.config_data):
            if val is not None:
                query_data.append(val)
                query_string += "\n  AND " + col + " = %s"

        cursor.execute(query_string, query_data)
        schedule = cursor.fetchall()
        return schedule

    def create_schedule_config(self, cursor):
        query_string = \
            """INSERT INTO scheduler (
               active,
               interval_ms,
               filename"""

        cols = 0
        query_data = \
            [self.active,
             self.interval_ms,
             self.filename]

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                query_string += ",\n" + col

        query_string += \
            (")\n" +
             "VALUES (%s, %s, %s" +
             ", %s" * cols +
             ")")

        cursor.execute(query_string, query_data)
        return True

    def delete_schedule_config(self, cursor):
        query_string = \
            """DELETE FROM scheduler
               WHERE active = %s
                 AND interval_ms = %s
                 AND filename = %s"""

        query_data = \
            [self.active,
             self.interval_ms,
             self.filename]

        for col, val in iteritems(self.config_data):
            if val is not None:
                query_data.append(val)
                query_string += "\n  AND " + col + " = %s"

        cursor.execute(query_string, query_data)
        check_count = cursor.rowcount
        return True, int(check_count)

    def manage_config(self, cursor, state):
        if state:
            if self.save_to_disk:
                save_config_to_disk(cursor)
            if self.load_to_runtime:
                load_config_to_runtime(cursor)

    def create_schedule(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.create_schedule_config(cursor)
            result['msg'] = "Added schedule to scheduler"
            result['schedules'] = \
                self.get_schedule_config(cursor)
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Schedule would have been added to" +
                             " scheduler, however check_mode" +
                             " is enabled.")

    def delete_schedule(self, check_mode, result, cursor):
        if not check_mode:
            result['schedules'] = \
                self.get_schedule_config(cursor)
            result['changed'] = \
                self.delete_schedule_config(cursor)
            result['msg'] = "Deleted schedule from scheduler"
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Schedule would have been deleted from" +
                             " scheduler, however check_mode is" +
                             " enabled.")

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None, type='str'),
            login_password=dict(default=None, no_log=True, type='str'),
            login_host=dict(default="127.0.0.1"),
            login_unix_socket=dict(default=None),
            login_port=dict(default=6032, type='int'),
            config_file=dict(default="", type='path'),
            active=dict(default=True, type='bool'),
            interval_ms=dict(default=10000, type='int'),
            filename=dict(required=True, type='str'),
            arg1=dict(type='str'),
            arg2=dict(type='str'),
            arg3=dict(type='str'),
            arg4=dict(type='str'),
            arg5=dict(type='str'),
            comment=dict(type='str'),
            state=dict(default='present', choices=['present',
                                                   'absent']),
            force_delete=dict(default=False, type='bool'),
            save_to_disk=dict(default=True, type='bool'),
            load_to_runtime=dict(default=True, type='bool')
        ),
        supports_check_mode=True
    )

    perform_checks(module)

    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    config_file = module.params["config_file"]

    cursor = None
    try:
        cursor = mysql_connect(module,
                               login_user,
                               login_password,
                               config_file,
                               cursor_class=mysql_driver.cursors.DictCursor)
    except mysql_driver.Error as e:
        module.fail_json(
            msg="unable to connect to ProxySQL Admin Module.. %s" % to_native(e)
        )

    proxysql_schedule = ProxySQLSchedule(module)
    result = {}

    result['state'] = proxysql_schedule.state
    result['filename'] = proxysql_schedule.filename

    if proxysql_schedule.state == "present":
        try:
            if not proxysql_schedule.check_schedule_config(cursor) > 0:
                proxysql_schedule.create_schedule(module.check_mode,
                                                  result,
                                                  cursor)
            else:
                result['changed'] = False
                result['msg'] = ("The schedule already exists and doesn't" +
                                 " need to be updated.")
                result['schedules'] = \
                    proxysql_schedule.get_schedule_config(cursor)
        except mysql_driver.Error as e:
            module.fail_json(
                msg="unable to modify schedule.. %s" % to_native(e)
            )

    elif proxysql_schedule.state == "absent":
        try:
            existing_schedules = \
                proxysql_schedule.check_schedule_config(cursor)
            if existing_schedules > 0:
                if existing_schedules == 1 or proxysql_schedule.force_delete:
                    proxysql_schedule.delete_schedule(module.check_mode,
                                                      result,
                                                      cursor)
                else:
                    module.fail_json(
                        msg=("Operation would delete multiple records" +
                             " use force_delete to override this")
                    )
            else:
                result['changed'] = False
                result['msg'] = ("The schedule is already absent from the" +
                                 " memory configuration")
        except mysql_driver.Error as e:
            module.fail_json(
                msg="unable to remove schedule.. %s" % to_native(e)
            )

    module.exit_json(**result)

if __name__ == '__main__':
    main()
