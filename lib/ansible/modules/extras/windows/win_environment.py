#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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
module: win_environment
version_added: "2.0"
short_description: Modifies environment variables on windows hosts.
description:
    - Uses .net Environment to set or remove environment variables and can set at User, Machine or Process level.  
    - User level environment variables will be set, but not available until the user has logged off and on again.
options:
  state:
    description:
      - present to ensure environment variable is set, or absent to ensure it is removed
    required: false
    default: present
    choices:
      - present
      - absent
  name:
    description:
      - The name of the environment variable
    required: true
    default: no default
  value:
    description: 
      - The value to store in the environment variable. Can be omitted for state=absent
    required: false
    default: no default
  level:
    description: 
      - The level at which to set the environment variable.
      - Use 'machine' to set for all users.
      - Use 'user' to set for the current user that ansible is connected as.
      - Use 'process' to set for the current process.  Probably not that useful.
    required: true
    default: no default
    choices:
      - machine
      - process
      - user
author: "Jon Hawkesworth (@jhawkesworth)"
notes: 
   - This module does not broadcast change events.  
     This means that the minority of windows applications which can have 
     their environment changed without restarting will not be notified and 
     therefore will need restarting to pick up new environment settings.  
     User level environment variables will require the user to log out 
     and in again before they become available.
'''

EXAMPLES = '''
  # Set an environment variable for all users
  win_environment:
    state: present
    name: TestVariable
    value: "Test value"
    level: machine
  # Remove an environment variable for the current users
  win_environment:
    state: absent
    name: TestVariable
    level: user
'''

