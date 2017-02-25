#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = r'''
---
module: win_service_stat
version_added: "2.3"
short_description: returns information about a Windows service
description:
- This module will return information about a service such as whether it
  exist or not as well as things like the state, startup type and more.
options:
  name:
    description: The name of the Windows service to get info for.
    required: True
author: Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: get details on a service
  win_service_stat:
    name: spooler
  register: spooler_info
'''

RETURN = r'''
exists:
    description: whether the service exists or not
    returned: success
    type: boolean
    sample: true
name:
    description: the service name or id of the service
    returned: success and service exists
    type: string
    sample: CoreMessagingRegistrar
display_name:
    description: the display name of the installed service
    returned: success and service exists
    type: string
    sample: CoreMessaging
status:
    description: the current running status of the service
    returned: success and service exists
    type: string
    sample: stopped
start_mode:
    description: the startup type of the service
    returned: success and service exists
    type: string
    sample: manual
path:
    description:
    returned: success and service exists
    type: string
    sample: C:\Windows\system32\svchost.exe -k LocalServiceNoNetwork
description:
    description: the path to the executable of the service
    returned: success and service exists
    type: string
    sample: Manages communication between system components.
username:
    description: the username that runs the service
    returned: success and service exists
    type: string
    sample: LocalSystem
desktop_interact:
    description: Whether the current user is allowed to interact with the desktop
    returned: success and service exists
    type: boolean
    sample: False
dependencies:
    description: A list of dependencies the service relies on
    returned: success and service exists
    type: List
    sample: False
depended_by:
    description: A list of dependencies this service relies on
    returned: success and service exists
    type: List
    sample: False
'''
