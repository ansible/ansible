#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    - Timezone to set to.
    - 'Example: Central Standard Time'
    required: yes
notes:
- The module will check if the provided timezone is supported on the machine.
- A list of possible timezones is available from C(tzutil.exe /l) and from
  U(https://msdn.microsoft.com/en-us/library/ms912391.aspx)
- If running on Server 2008 the hotfix
  U(https://support.microsoft.com/en-us/help/2556308/tzutil-command-line-tool-is-added-to-windows-vista-and-to-windows-server-2008)
  needs to be installed to be able to run this module.
author:
- Phil Schwartz (@schwartzmx)
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
