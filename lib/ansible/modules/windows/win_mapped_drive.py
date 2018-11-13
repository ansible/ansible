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
- You cannot use this module to access a mapped drive in another Ansible task,
  drives mapped with this module are only accessible when logging in
  interactively with the user through the console or RDP.
- To create a mapped drive with saved credentials, use become to access the
  current user's credential store when creating the drive. Any credentials
  should be added to the store with C(cmdkey.exe).
- Using the I(username) and I(password) options will allow a module to create
  a mapped drive that requires authentication but the drive will not accessible
  on the next interactive logon as the password is not saved.
- This module will only map a drive for the current user, to map a drive for
  all users of a system, use become with the U(SYSTEM) account. This will not
  allow you to save the credentials as C(cmdkey.exe) is user specific, use
  other Microsoft tools like GPOs to achieve this goal.
options:
  letter:
    description:
    - The letter of the network path to map to.
    - This letter must not already be in use with Windows.
    required: yes
  password:
    description:
    - The password for C(username).
    - This is never saved with a mapped drive, use the C(cmdkey) executable
      with become to persist a username and password.
  path:
    description:
    - The UNC path to map the drive to.
    - This is required if C(state=present).
    - If C(state=absent) and I(path) is not set, the module will delete the
      mapped drive regardless of the target.
    - If C(state=absent) and the I(path) is set, the module will throw an error
      if path does not match the target of the mapped drive.
    type: path
  state:
    description:
    - If C(present) will ensure the mapped drive exists.
    - If C(absent) will ensure the mapped drive does not exist.
    choices: [ absent, present ]
    default: present
  username:
    description:
    - The username to store with the mapped drive configuration.
    - This is used with I(password) when attempting to map the drive in the
      module.
    - Unlike I(password), this value is saved and is used for subsequent
      authentication attempts. This will override any saved Windows credentials
      stored by C(cmdkey) and will result in a failed network connection on the
      next interactive logon as no password is saved.
    - When creating a mapped drive that requires credentials, it is recommended
      to use C(cmdkey) to create the saved Windows credentials then run this
      module with become and to not define this key, see the examples for more
      details.
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

- name: Create mapped drive with credentials and save the username and password
  block:
  - name: Save the network credentials required for the mapped drive
    win_command: cmdkey.exe /add:server /user:username@DOMAIN /pass:Password01
    no_log: True

  - name: Create a mapped drive that requires authentication
    win_mapped_drive:
      letter: M
      path: \\SERVER\C$
      state: present
  vars:
    # become is required to save and retrieve the credentials in the tasks
    ansible_become: yes
    ansible_become_method: runas
    ansible_become_user: '{{ ansible_user }}'
    ansible_become_pass: '{{ ansible_password }}'
'''

RETURN = r'''
'''
