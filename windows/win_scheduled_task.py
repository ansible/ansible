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

DOCUMENTATION = '''
---
module: win_scheduled_task
version_added: "2.0"
short_description: Manage scheduled tasks
description:
    - Manage scheduled tasks
options:
  name:
    description:
      - Name of the scheduled task
    required: true
  description:
    description:
      - The description for the scheduled task
    required: false
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
      - User to run scheduled task as
    required: false
  execute:
    description:
      - Command the scheduled task should execute
    required: false
  argument:
    description:
      - Arguments to provide scheduled task action
    required: false
  frequency:
    description:
      - The frequency of the command, not idempotent
    required: false
    choices:
      - daily
      - weekly
  time:
    description:
      - Time to execute scheduled task, not idempotent
    required: false
  days_of_week:
    description:
      - Days of the week to run a weekly task, not idempotent
    required: false
  path:
    description:
      - Folder path of scheduled task
    default: '\'
'''

EXAMPLES = '''
  # Create a scheduled task to open a command prompt
  win_scheduled_task: name="TaskName" execute="cmd" frequency="daily" time="9am" description="open command prompt" path="example" enable=yes state=present user=SYSTEM
'''
