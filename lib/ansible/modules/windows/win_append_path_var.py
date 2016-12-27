#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, RajeshKumar Palani SyedShabir
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
module: win_append_path_var
version_added: "2.3"
short_description: Append Path environment variables on windows hosts.
description:
    - Uses .net Environment to set path environment variables and can set at User, Machine and Process level.  
    - User level path environment variables will be set, but available until the particular session is closed.
options:
 pathvalue:
    description: 
      - The value to store in the path environment variable.
    required: true
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
author: "SyedShabir, RajeshKumar Palani"
notes: 
   - This module does not broadcast change events.  
     This means that the minority of windows applications which can have 
     their environment changed without restarting will not be notified and 
     therefore will need restarting to pick up new environment settings.  
     User level environment variables will not require the user to log out 
     and in again before they become available.
'''

EXAMPLES = '''
  # Set an path environment variable for all users
  win_append_path_var:
    pathvalue: 'C:\Program Files\Java\bin'
    level: machine
  # Expand an path environment variable for the current users
  win_append_path_var:
    pathvalue: '%JAVA_HOME%/bin'
    level: user
'''

RETURN = '''
'''
