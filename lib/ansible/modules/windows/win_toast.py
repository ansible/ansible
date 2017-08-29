#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_toast
version_added: "2.4"
short_description: Sends Toast windows notification to Windows 10 or later hosts
description:
    - Sends alerts which appear in the Action Center area of the windows desktop.
options:
  expire_secs:
    description:
      - How long in seconds before the notification expires.
    default: 45
  group:
    description:
      - Which notification group to add the notification to.
    default: Powershell
  msg:
    description:
      - The message to appear inside the notification.  May include \n to format the message to appear within the Action Center.
    default: 'Hello, World!'
  popup:
    description:
      - If false, the notification will not pop up and will only appear in the Action Center.
    type: bool
    default: 'Yes'
  tag:
    description:
      - The tag to add to the notification.
    default: Ansible
  title:
    description:
      - The notification title, which appears in the pop up..
    default: Notification HH:mm
author:
- Jon Hawkesworth (@jhawkesworth)
notes:
   - This module must run on a windows 10 or Server 2016 host, so ensure your play targets windows hosts, or delegates to a windows host.
   - Messages are only sent to the local host where the module is run.
   - You must run this module with async, otherwise it will hang until the expire_secs period has passed.
'''

EXAMPLES = r'''
- name: Warn logged in users of impending upgrade (note use of async to stop the module from waiting until notification expires).
  win_toast:
    expire_secs: 60
    title: System Upgrade Notification
    msg: Automated upgrade about to start.  Please save your work and log off before {{ deployment_start_time }}
  async: 60
  poll: 0
'''

RETURN = r'''
expire_secs:
    description: Requested time in seconds before notification expires.
    returned: allways
    type: int
    sample: 5
expire_at_utc:
    description: Calculated utc date time when the notification expires.
    returned: allways
    type: string
    sample: 07 July 2017 04:50:54
group:
    description: Requested group for the notification to belong to.
    returned: allways
    type: string
    sample: Powershell
msg:
    description: Text of the message that was sent.
    returned: allways
    type: string
    sample: Automated upgrade about to start.\nPlease save your work and log off before 22 July 2017 18:00:00
popup:
    description: Whether notification pop up was requested or not.
    returned: allways
    type: boolean
    sample: true
runtime_seconds:
    description: How long the module took to run on the remote windows host.
    returned: allways
    type: float
    sample: 0.3706631999999997
sent_localtime:
    description: local date time when the notification was sent.
    returned: allways
    type: string
    sample: 07 July 2017 05:45:54
tag:
    description: Requested tag to associated with the notification.

    returned: allways
    type: string
    sample: Ansible
title:
    description: The requested text for the notification title, which appears in the popup and Action Center if specified.
    returned: success
    type: string
    sample: Notification 05:45
'''
