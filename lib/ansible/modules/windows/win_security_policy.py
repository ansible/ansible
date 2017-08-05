#!/usr/bin/python
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

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_security_policy
version_added: '2.4'
short_description: changes local security policy settings
description:
- Allows you to set the local security policies that are configured by
  SecEdit.exe.
notes:
- This module uses the SecEdit.exe tool to configure the values, more details
  of the areas and keys that can be configured can be found here
  U(https://msdn.microsoft.com/en-us/library/bb742512.aspx).
- If you are in a domain environment these policies may be set by a GPO policy,
  this module can temporarily change these values but the GPO will override
  it if the value differs.
- You can also run C(SecEdit.exe /export /cfg C:\temp\output.ini) to view the
  current policies set on your system.
options:
  section:
    description:
    - The ini section the key exists in.
    - If the section does not exist then the module will return an error.
    - Example sections to use are 'Account Policies', 'Local Policies',
      'Event Log', 'Restricted Groups', 'System Services', 'Registry' and
      'File System'
    required: yes
  key:
    description:
    - The ini key of the section or policy name to modify.
    - The module will return an error if this key is invalid.
    required: yes
  value:
    description:
    - The value for the ini key or policy name.
    - If the key takes in a boolean value then 0 = False and 1 = True.
    required: yes
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: change the guest account name
  win_security_policy:
    section: System Access
    key: NewGuestName
    value: Guest Account

- name: set the maximum password age
  win_security_policy:
    section: System Access
    key: MaximumPasswordAge
    value: 15

- name: do not store passwords using reversible encryption
  win_security_policy:
    section: System Access
    key: ClearTextPassword
    value: 0

- name: enable system events
  win_security_policy:
    section: Event Audit
    key: AuditSystemEvents
    value: 1
'''

RETURN = r'''
rc:
  description: The return code after a failure when running SecEdit.exe.
  returned: failure with secedit calls
  type: int
  sample: -1
stdout:
  description: The output of the STDOUT buffer after a failure when running
    SecEdit.exe.
  returned: failure with secedit calls
  type: string
  sample: check log for error details
stderr:
  description: The output of the STDERR buffer after a failure when running
    SecEdit.exe.
  returned: failure with secedit calls
  type: string
  sample: failed to import security policy
import_log:
  description: The log of the SecEdit.exe /configure job that configured the
    local policies. This is used for debugging purposes on failures.
  returned: secedit.exe /import run and change occurred
  type: string
  sample: Completed 6 percent (0/15) \tProcess Privilege Rights area.
key:
  description: The key in the section passed to the module to modify.
  returned: success
  type: string
  sample: NewGuestName
section:
  description: The section passed to the module to modify.
  returned: success
  type: string
  sample: System Access
value:
  description: The value passed to the module to modify to.
  returned: success
  type: string
  sample: Guest Account
'''
