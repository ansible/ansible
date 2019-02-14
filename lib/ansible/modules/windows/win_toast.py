#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_toast
version_added: "2.4"
short_description: Sends Toast windows notification to logged in users on Windows 10 or later hosts
description:
    - Sends alerts which appear in the Action Center area of the windows desktop.
options:
  expire:
    description:
      - How long in seconds before the notification expires.
    type: int
    default: 45
  group:
    description:
      - Which notification group to add the notification to.
    type: str
    default: Powershell
  msg:
    description:
      - The message to appear inside the notification.
      - May include \n to format the message to appear within the Action Center.
    type: str
    default: Hello, World!
  popup:
    description:
      - If C(no), the notification will not pop up and will only appear in the Action Center.
    type: bool
    default: yes
  tag:
    description:
      - The tag to add to the notification.
    type: str
    default: Ansible
  title:
    description:
      - The notification title, which appears in the pop up..
    type: str
    default: Notification HH:mm
notes:
   - This module must run on a windows 10 or Server 2016 host, so ensure your play targets windows hosts, or delegates to a windows host.
   - The module does not fail if there are no logged in users to notify.
   - Messages are only sent to the local host where the module is run.
   - You must run this module with async, otherwise it will hang until the expire period has passed.
seealso:
- module: win_msg
- module: win_say
author:
- Jon Hawkesworth (@jhawkesworth)
'''

EXAMPLES = r'''
- name: Warn logged in users of impending upgrade (note use of async to stop the module from waiting until notification expires).
  win_toast:
    expire: 60
    title: System Upgrade Notification
    msg: Automated upgrade about to start.  Please save your work and log off before {{ deployment_start_time }}
  async: 60
  poll: 0
'''

RETURN = r'''
expire_at_utc:
    description: Calculated utc date time when the notification expires.
    returned: allways
    type: str
    sample: 07 July 2017 04:50:54
no_toast_sent_reason:
    description: Text containing the reason why a notification was not sent.
    returned: when no logged in users are detected
    type: str
    sample: No logged in users to notify
sent_localtime:
    description: local date time when the notification was sent.
    returned: allways
    type: str
    sample: 07 July 2017 05:45:54
time_taken:
    description: How long the module took to run on the remote windows host in seconds.
    returned: allways
    type: float
    sample: 0.3706631999999997
toast_sent:
    description: Whether the module was able to send a toast notification or not.
    returned: allways
    type: bool
    sample: false
'''
