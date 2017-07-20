#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_scheduled_task
author: "Peter Mounce"
version_added: "2.0"
short_description: Manage scheduled tasks
description:
    - Manage scheduled tasks
notes:
    - This module requires Windows Server 2012 or later.
options:
  name:
    description:
      - Name of the scheduled task
    required: true
  description:
    description:
      - The description for the scheduled task
  enabled:
    description:
      - Enable/disable the task
    choices:
      - yes
      - no
    default: yes
  state:
    description:
      - State that the task should become
    required: true
    choices:
      - present
      - absent
  user:
    description:
      - User to run the scheduled task as; defaults to the current user
    default: DOMAIN\user
  password:
    description:
      - Password for the user account to run the scheduled task as.  This is required for running a task without the user being
        logged in, excluding Windows built-in service accounts.  This should be used for specifying credentials during initial
        task creation, and changing stored user credentials, as setting this value will cause the task to be recreated.
    version_added: "2.4"
  runlevel:
    description:
      - The level of user rights used to run the task
    default: limited
    choices:
      - limited
      - highest
    version_added: "2.4"
  store_password:
    description:
      - Store the password for the user running the task.  If C(false), the task will only have access to local resources.
    default: true
    version_added: "2.4"
  executable:
    description:
      - Command the scheduled task should execute
    aliases: [ execute ]
  arguments:
    description:
      - Arguments to provide scheduled task action
    aliases: [ argument ]
  frequency:
    description:
      - The frequency of the command, not idempotent
    choices:
      - once
      - daily
      - weekly
  time:
    description:
      - Time to execute scheduled task, not idempotent
  days_of_week:
    description:
      - Days of the week to run a weekly task, not idempotent
  path:
    description:
      - Task folder in which this task will be stored - creates a non-existent path when C(state) is C(present),
        and removes an empty path when C(state) is C(absent)
    default: '\'
'''

EXAMPLES = r'''
# Create a scheduled task to open a command prompt
- win_scheduled_task:
    name: TaskName
    description: open command prompt
    executable: cmd
    arguments: -opt1 -opt2
    path: \example
    time: 9am
    frequency: daily
    state: present
    enabled: yes
    user: SYSTEM

- name: Create a task to run a PowerShell script as NETWORK SERVICE at the highest user rights level
  win_scheduled_task:
    name: TaskName2
    description: Run a PowerShell script
    executable: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    arguments: -ExecutionPolicy Unrestricted -NonInteractive -File C:\TestDir\Test.ps1
    time: 6pm
    frequency: once
    state: present
    enabled: yes
    user: NETWORK SERVICE
    runlevel: highest

- name: Change the above task to run under a domain user account, storing credentials for the task
  win_scheduled_task:
    name: TaskName2
    description: Run a PowerShell script
    executable: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    arguments: -ExecutionPolicy Unrestricted -NonInteractive -File C:\TestDir\Test.ps1
    time: 6pm
    frequency: once
    state: present
    enabled: yes
    user: DOMAIN\user
    password: passwordGoesHere
    runlevel: highest

- name: Change the above task again, choosing not to store the password for the account
  win_scheduled_task:
    name: TaskName2
    description: Run a PowerShell script
    executable: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    arguments: -ExecutionPolicy Unrestricted -NonInteractive -File C:\TestDir\Test.ps1
    time: 6pm
    frequency: once
    state: present
    enabled: yes
    user: DOMAIN\user
    runlevel: highest
    store_password: no
'''
