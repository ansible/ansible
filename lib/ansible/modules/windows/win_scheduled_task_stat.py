#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_scheduled_task_stat
version_added: "2.5"
short_description: Get information about Windows Scheduled Tasks
description:
- Will return whether the folder and task exists.
- Returns the names of tasks in the folder specified.
- Use M(win_scheduled_task) to configure a scheduled task.
options:
  path:
    description: The folder path where the task lives.
    type: str
    default: \
  name:
    description:
    - The name of the scheduled task to get information for.
    - If C(name) is set and exists, will return information on the task itself.
    type: str
seealso:
- module: win_scheduled_task
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Get information about a folder
  win_scheduled_task_stat:
    path: \folder name
  register: task_folder_stat

- name: Get information about a task in the root folder
  win_scheduled_task_stat:
    name: task name
  register: task_stat

- name: Get information about a task in a custom folder
  win_scheduled_task_stat:
    path: \folder name
    name: task name
  register: task_stat
'''

RETURN = r'''
actions:
  description: A list of actions.
  returned: name is specified and task exists
  type: list
  sample: [
      {
          "Arguments": "/c echo hi",
          "Id": null,
          "Path": "cmd.exe",
          "Type": "TASK_ACTION_EXEC",
          "WorkingDirectory": null
      }
  ]
folder_exists:
  description: Whether the folder set at path exists.
  returned: always
  type: bool
  sample: true
folder_task_count:
  description: The number of tasks that exist in the folder.
  returned: always
  type: int
  sample: 2
folder_task_names:
  description: A list of tasks that exist in the folder.
  returned: always
  type: list
  sample: [ 'Task 1', 'Task 2' ]
principal:
  description: Details on the principal configured to run the task.
  returned: name is specified and task exists
  type: complex
  contains:
    display_name:
      description: The name of the user/group that is displayed in the Task
        Scheduler UI.
      returned: ''
      type: str
      sample: Administrator
    group_id:
      description: The group that will run the task.
      returned: ''
      type: str
      sample: BUILTIN\Administrators
    id:
      description: The ID for the principal.
      returned: ''
      type: str
      sample: Author
    logon_type:
      description: The logon method that the task will run with.
      returned: ''
      type: str
      sample: TASK_LOGON_INTERACTIVE_TOKEN
    run_level:
      description: The level of user rights used to run the task.
      returned: ''
      type: str
      sample: TASK_RUNLEVEL_LUA
    user_id:
      description: The user that will run the task.
      returned: ''
      type: str
      sample: SERVER\Administrator
registration_info:
  description: Details on the task registration info.
  returned: name is specified and task exists
  type: complex
  contains:
    author:
      description: The author os the task.
      returned: ''
      type: str
      sample: SERVER\Administrator
    date:
      description: The date when the task was register.
      returned: ''
      type: str
      sample: '2017-01-01T10:00:00'
    description:
      description: The description of the task.
      returned: ''
      type: str
      sample: task description
    documentation:
      description: The documentation of the task.
      returned: ''
      type: str
      sample: task documentation
    security_descriptor:
      description: The security descriptor of the task.
      returned: ''
      type: str
      sample: security descriptor
    source:
      description: The source of the task.
      returned: ''
      type: str
      sample: source
    uri:
      description: The URI/path of the task.
      returned: ''
      type: str
      sample: \task\task name
    version:
      description: The version of the task.
      returned: ''
      type: str
      sample: 1.0
settings:
  description: Details on the task settings.
  returned: name is specified and task exists
  type: complex
  contains:
    allow_demand_start:
      description: Whether the task can be started by using either the Run
        command of the Context menu.
      returned: ''
      type: bool
      sample: true
    allow_hard_terminate:
      description: Whether the task can terminated by using TerminateProcess.
      returned: ''
      type: bool
      sample: true
    compatibility:
      description: The compatibility level of the task
      returned: ''
      type: int
      sample: 2
    delete_expired_task_after:
      description: The amount of time the Task Scheduler will wait before
        deleting the task after it expires.
      returned: ''
      type: str
      sample: PT10M
    disallow_start_if_on_batteries:
      description: Whether the task will not be started if the computer is
        running on battery power.
      returned: ''
      type: bool
      sample: false
    disallow_start_on_remote_app_session:
      description: Whether the task will not be started when in a remote app
        session.
      returned: ''
      type: bool
      sample: true
    enabled:
      description: Whether the task is enabled.
      returned: ''
      type: bool
      sample: true
    execution_time_limit:
      description: The amount of time allowed to complete the task.
      returned: ''
      type: str
      sample: PT72H
    hidden:
      description: Whether the task is hidden in the UI.
      returned: ''
      type: bool
      sample: false
    idle_settings:
      description: The idle settings of the task.
      returned: ''
      type: dict
      sample: {
          "idle_duration": "PT10M",
          "restart_on_idle": false,
          "stop_on_idle_end": true,
          "wait_timeout": "PT1H"
      }
    maintenance_settings:
      description: The maintenance settings of the task.
      returned: ''
      type: str
      sample: null
    mulitple_instances:
      description: Indicates the behaviour when starting a task that is already
        running.
      returned: ''
      type: int
      sample: 2
    network_settings:
      description: The network settings of the task.
      returned: ''
      type: dict
      sample: {
          "id": null,
          "name": null
      }
    priority:
      description: The priority level of the task.
      returned: ''
      type: int
      sample: 7
    restart_count:
      description: The number of times that the task will attempt to restart
        on failures.
      returned: ''
      type: int
      sample: 0
    restart_interval:
      description: How long the Task Scheduler will attempt to restart the
        task.
      returned: ''
      type: str
      sample: PT15M
    run_only_id_idle:
      description: Whether the task will run if the computer is in an idle
        state.
      returned: ''
      type: bool
      sample: true
    run_only_if_network_available:
      description: Whether the task will run only when a network is available.
      returned: ''
      type: bool
      sample: false
    start_when_available:
      description: Whether the task can start at any time after its scheduled
        time has passed.
      returned: ''
      type: bool
      sample: false
    stop_if_going_on_batteries:
      description: Whether the task will be stopped if the computer begins to
        run on battery power.
      returned: ''
      type: bool
      sample: true
    use_unified_scheduling_engine:
      description: Whether the task will use the unified scheduling engine.
      returned: ''
      type: bool
      sample: false
    volatile:
      description: Whether the task is volatile.
      returned: ''
      type: bool
      sample: false
    wake_to_run:
      description: Whether the task will wake the computer when it is time to
        run the task.
      returned: ''
      type: bool
      sample: false
state:
  description: Details on the state of the task
  returned: name is specified and task exists
  type: complex
  contains:
    last_run_time:
      description: The time the registered task was last run.
      returned: ''
      type: str
      sample: '2017-09-20T20:50:00'
    last_task_result:
      description: The results that were returned the last time the task was
        run.
      returned: ''
      type: int
      sample: 267009
    next_run_time:
      description: The time when the task is next scheduled to run.
      returned: ''
      type: str
      sample: '2017-09-20T22:50:00'
    number_of_missed_runs:
      description: The number of times a task has missed a scheduled run.
      returned: ''
      type: int
      sample: 1
    status:
      description: The status of the task, whether it is running, stopped, etc.
      returned: ''
      type: str
      sample: TASK_STATE_RUNNING
task_exists:
  description: Whether the task at the folder exists.
  returned: name is specified
  type: bool
  sample: true
triggers:
  description: A list of triggers.
  returned: name is specified and task exists
  type: list
  sample: [
      {
          "delay": "PT15M",
          "enabled": true,
          "end_boundary": null,
          "execution_time_limit": null,
          "id": null,
          "repetition": {
              "duration": null,
              "interval": null,
              "stop_at_duration_end": false
          },
          "start_boundary": null,
          "type": "TASK_TRIGGER_BOOT"
      },
      {
          "days_of_month": "5,15,30",
          "enabled": true,
          "end_boundary": null,
          "execution_time_limit": null,
          "id": null,
          "months_of_year": "june,december",
          "random_delay": null,
          "repetition": {
              "duration": null,
              "interval": null,
              "stop_at_duration_end": false
          },
          "run_on_last_day_of_month": true,
          "start_boundary": "2017-09-20T03:44:38",
          "type": "TASK_TRIGGER_MONTHLY"
    }
  ]
'''
