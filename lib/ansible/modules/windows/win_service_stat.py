#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Trond Hindenes <trond@hindenes.com>
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

DOCUMENTATION = r'''
---
module: win_service_stat
version_added: "2.5"
short_description: Returns info about a Windows service
description:
    - Returns info about a Windows service, and wether or not it exists
options:
  name:
    description:
      - The name of the service to check
    required: true
author: Trond Hindenes
'''

EXAMPLES = r'''
# Playbook example
  - name: Extract zip file
    win_service_stat:
      name: winrm
'''

RETURN = r'''
win_service_stat:
    description: Information about the service
    returned: always
    type: complex
    sample:
    contains:
      exists:
          description: Boolean indicating wether the service exists or not
      state:
          description: 'current state of the service. Will be null of service doesn't exist'
      caption:
          description: 'Service display name (returned if service exists)'
      name:
          description: 'Name of the service (returned if service exists)'
      path_name:
          description: 'path and parameters to start the service (returned if service exists)'
      start_mode:
          description: 'start mode of the service. Can be auto, manual, disabled (returned if service exists)'
      start_name:
          description: 'user account running the service (returned if service exists)'

'''
