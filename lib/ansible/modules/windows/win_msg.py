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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_msg
version_added: "2.3"
short_description: Sends a message to logged in users on Windows hosts.
description:
    - Wraps the msg.exe command in order to send messages to Windows hosts.
options:
  to:
    description:
      - Who to send the message to. Can be a username, sessionname or sessionid.
    default: '*'
  display_seconds:
    description:
      - How long to wait for receiver to acknowledge message, in seconds.
    default: 10
  wait:
    description:
      - Whether to wait for users to respond.  Module will only wait for the number of seconds specified in display_seconds or 10 seconds if not specified.
        However, if I(wait) is true, the message is sent to each logged on user in turn, waiting for the user to either press 'ok' or for
        the timeout to elapse before moving on to the next user.
    type: bool
    default: 'no'
  msg:
    description:
      - The text of the message to be displayed.
    default: Hello world!
author:
- Jon Hawkesworth (@jhawkesworth)
notes:
   - This module must run on a windows host, so ensure your play targets windows
     hosts, or delegates to a windows host.
   - Messages are only sent to the local host where the module is run.
   - The module does not support sending to users listed in a file.
   - Setting wait to true can result in long run times on systems with many logged in users.
'''

EXAMPLES = r'''
- name: Warn logged in users of impending upgrade
  win_msg:
    display_seconds: 60
    msg: Automated upgrade about to start.  Please save your work and log off before {{ deployment_start_time }}
'''

RETURN = r'''
msg:
    description: Test of the message that was sent.
    returned: changed
    type: string
    sample: Automated upgrade about to start.  Please save your work and log off before 22 July 2016 18:00:00
display_seconds:
    description: Value of display_seconds module parameter.
    returned: success
    type: string
    sample: 10
rc:
    description: The return code of the API call
    returned: always
    type: int
    sample: 0
runtime_seconds:
    description: How long the module took to run on the remote windows host.
    returned: success
    type: string
    sample: 22 July 2016 17:45:51
sent_localtime:
    description: local time from windows host when the message was sent.
    returned: success
    type: string
    sample: 22 July 2016 17:45:51
wait:
    description: Value of wait module parameter.
    returned: success
    type: boolean
    sample: false
'''
