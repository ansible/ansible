#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_timezone
version_added: '2.1'
short_description: Sets Windows machine timezone
description:
- Sets machine time to the specified timezone.
options:
  timezone:
    description:
    - Timezone to set to. Example Central Standard Time
    required: true
notes:
- The module will check if the provided timezone is supported on the machine.
- A list of possible timezones is available from C(tzutil.exe /l) and from
  U(https://msdn.microsoft.com/en-us/library/ms912391.aspx)
- If running on Server 2008 the hotfix
  U(https://support.microsoft.com/en-us/help/2556308/tzutil-command-line-tool-is-added-to-windows-vista-and-to-windows-server-2008)
  needs to be installed to be able to run this module.
author: Phil Schwartz
'''

EXAMPLES = r'''
- name: Set timezone to 'Romance Standard Time' (GMT+01:00)
  win_timezone:
    timezone: Romance Standard Time

- name: Set timezone to 'GMT Standard Time' (GMT)
  win_timezone:
    timezone: GMT Standard Time

- name: Set timezone to 'Central Standard Time' (GMT-06:00)
  win_timezone:
    timezone: Central Standard Time
'''

RETURN = r'''
previous_timezone:
    description: The previous timezone if it was changed, otherwise the existing timezone
    returned: success
    type: string
    sample: Central Standard Time
timezone:
    description: The current timezone (possibly changed)
    returned: success
    type: string
    sample: Central Standard Time
'''
