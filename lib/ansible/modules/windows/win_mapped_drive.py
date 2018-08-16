#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_mapped_drive
version_added: '2.4'
short_description: Map network drives for users
description:
- Allows you to modify mapped network drives for individual users.
notes:
- This can only map a network drive for the current executing user and does not
  allow you to set a default drive for all users of a system. Use other
  Microsoft tools like GPOs to achieve this goal.
- You cannot use this module to access a mapped drive in another Ansible task,
  drives mapped with this module are only accessible when logging in
  interactively with the user through the console or RDP.
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
    type: path
  state:
    description:
    - If C(present) will ensure the mapped drive exists.
    - If C(absent) will ensure the mapped drive does not exist.
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
- name: Create a mapped drive under Z
  win_mapped_drive:
    letter: Z
    path: \\domain\appdata\accounting

- name: Delete any mapped drives under Z
  win_mapped_drive:
    letter: Z
    state: absent

- name: Only delete the mapped drive Z if the paths match (error is thrown otherwise)
  win_mapped_drive:
    letter: Z
    path: \\domain\appdata\accounting
    state: absent

- name: Create mapped drive with local credentials
  win_mapped_drive:
    letter: M
    path: \\SERVER\c$
    username: SERVER\Administrator
    password: Password

- name: Create mapped drive with domain credentials
  win_mapped_drive:
    letter: M
    path: \\domain\appdata\it
    username: DOMAIN\IT
    password: Password
'''

RETURN = r'''
'''
