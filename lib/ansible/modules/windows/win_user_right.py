#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017, Jordan Borean <jborean93@gmail.com>
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
module: win_user_right
version_added: '2.4'
short_description: Manage Windows User Rights
description:
- Add, remove or set User Rights for a group or users or groups.
- You can set user rights for both local and domain accounts.
notes:
- If the server is domain joined this module can change a right but if a GPO
  governs this right then the changes won't last.
options:
  name:
    description:
    - The name of the User Right as shown by the C(Constant Name) value from
      U(https://technet.microsoft.com/en-us/library/dd349804.aspx).
    - If this right is not a valid entry then the module will return an error.
    required: True
  users:
    description:
    - A list of users or groups to add/remove on the User Right.
    - These can be in the form DOMAIN\user-group, user-group@DOMAIN.COM for
      domain users/groups.
    - For local users/groups it can be in the form user-group, .\user-group,
      SERVERNAME\user-group where SERVERNAME is the name of the remote server.
    - You can also add special local accounts like SYSTEM and others.
    required: True
  action:
    description:
    - C(add) will add the users/groups to the existing right.
    - C(remove) will remove the users/groups from the existing right.
    - C(set) will replace the users/groups of the existing right.
    default: set
    choices: [set, add, remove]
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
---
- name: replace the entries of Deny log on locally
  win_user_right:
    name: SeDenyInteractiveLogonRight
    users:
    - Guest
    - Users
    action: set

- name: add account to Log on as a service
  win_user_right:
    name: SeServiceLogonRight
    users:
    - .\Administrator
    - '{{ansible_hostname}}\local-user'
    action: add

- name: remove accounts who can create Symbolic links
  win_user_right:
    name: SeCreateSymbolicLinkPrivilege
    users:
    - SYSTEM
    - Administrators
    - DOMAIN\User
    - group@DOMAIN.COM
    action: remove
'''

RETURN = r'''
added:
  description: A list of accounts that were added to the right, this is empty
    if no accounts were added.
  returned: success
  type: list
  sample: ["NT AUTHORITY\\SYSTEM", "DOMAIN\\User"]
import_log:
  description: The log of the SecEdit.exe /configure job that configured the
    user rights. This is used for debugging purposes on failures.
  returned: change occurred
  type: string
  sample: Completed 6 percent (0/15) \tProcess Privilege Rights area.
rc:
  description: The return code after a failure when running SecEdit.exe.
  returned: failure with secedit calls
  type: int
  sample: -1
removed:
  description: A list of accounts that were removed from the right, this is
    empty if no accounts were removed.
  returned: success
  type: list
  sample: ["SERVERNAME\\Administrator", "BUILTIN\\Administrators"]
stderr:
  description: The output of the STDERR buffer after a failure when running
    SecEdit.exe.
  returned: failure with secedit calls
  type: string
  sample: failed to import security policy
stdout:
  description: The output of the STDOUT buffer after a failure when running
    SecEdit.exe.
  returned: failure with secedit calls
  type: string
  sample: check log for error details
'''
