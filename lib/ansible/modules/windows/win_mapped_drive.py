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
module: win_mapped_drive
version_added: '2.4'
short_description: maps a network drive for a user
description:
- Allows you to modify mapped network drives for individual users.
notes:
- This can only map a network drive for the current executing user and does not
  allow you to set a default drive for all users of a system. Use other
  Microsoft tools like GPOs to achieve this goal.
options:
  letter:
    description:
    - The letter of the network path to map to.
    - This letter must not already be in use with Windows.
    required: yes
  password:
    description:
    - The password for C(username).
  path:
    description:
    - The UNC path to map the drive to.
    - This is required if C(state=present).
    - If C(state=absent) and path is not set, the module will delete the mapped
      drive regardless of the target.
    - If C(state=absent) and the path is set, the module will throw an error if
      path does not match the target of the mapped drive.
  state:
    description:
    - If C(state=present) will ensure the mapped drive exists.
    - If C(state=absent) will ensure the mapped drive does not exist.
    choices: [ absent, present ]
    default: present
  username:
    description:
    - Credentials to map the drive with.
    - The username MUST include the domain or servername like SERVER\user, see
      the example for more information.
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: create a mapped drive under Z
  win_mapped_drive:
    letter: Z
    path: \\domain\appdata\accounting

- name: delete any mapped drives under Z
  win_mapped_drive:
    letter: Z
    state: absent

- name: only delete the mapped drive Z if the paths match (error is thrown otherwise)
  win_mapped_drive:
    letter: Z
    path: \\domain\appdata\accounting
    state: absent

- name: create mapped drive with local credentials
  win_mapped_drive:
    letter: M
    path: \\SERVER\c$
    username: SERVER\Administrator
    password: Password

- name: create mapped drive with domain credentials
  win_mapped_drive:
    letter: M
    path: \\domain\appdata\it
    username: DOMAIN\IT
    password: Password
'''

RETURN = r'''
'''
