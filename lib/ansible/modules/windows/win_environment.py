#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_environment
version_added: '2.0'
short_description: Modify environment variables on windows hosts
description:
- Uses .net Environment to set or remove environment variables and can set at User, Machine or Process level.
- User level environment variables will be set, but not available until the user has logged off and on again.
options:
  state:
    description:
    - Set to C(present) to ensure environment variable is set.
    - Set to C(absent) to ensure it is removed.
    type: str
    choices: [ absent, present ]
    default: present
  name:
    description:
    - The name of the environment variable.
    type: str
    required: yes
  value:
    description:
    - The value to store in the environment variable.
    - Must be set when C(state=present) and cannot be an empty string.
    - Can be omitted for C(state=absent).
    type: str
  level:
    description:
    - The level at which to set the environment variable.
    - Use C(machine) to set for all users.
    - Use C(user) to set for the current user that ansible is connected as.
    - Use C(process) to set for the current process.  Probably not that useful.
    type: str
    required: yes
    choices: [ machine, process, user ]
notes:
- This module is best-suited for setting the entire value of an
  environment variable. For safe element-based management of
  path-like environment vars, use the M(win_path) module.
- This module does not broadcast change events.
  This means that the minority of windows applications which can have
  their environment changed without restarting will not be notified and
  therefore will need restarting to pick up new environment settings.
  User level environment variables will require the user to log out
  and in again before they become available.
seealso:
- module: win_path
author:
- Jon Hawkesworth (@jhawkesworth)
'''

EXAMPLES = r'''
- name: Set an environment variable for all users
  win_environment:
    state: present
    name: TestVariable
    value: Test value
    level: machine

- name: Remove an environment variable for the current user
  win_environment:
    state: absent
    name: TestVariable
    level: user
'''

RETURN = r'''
before_value:
  description: the value of the environment key before a change, this is null if it didn't exist
  returned: always
  type: str
  sample: C:\Windows\System32
value:
  description: the value the environment key has been set to, this is null if removed
  returned: always
  type: str
  sample: C:\Program Files\jdk1.8
'''
