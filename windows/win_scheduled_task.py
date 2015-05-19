#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
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
      - Supports * as wildcard
    required: true
  enabled:
    description:
      - State that the task should become
    required: false
    choices:
      - yes
      - no
    default: yes
author: Peter Mounce
'''

EXAMPLES = '''
  # Disable the scheduled tasks with "WindowsUpdate" in their name
  win_scheduled_task: name="*WindowsUpdate*" enabled=no
'''
