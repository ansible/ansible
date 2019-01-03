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
options:
  letter:
    description:
    - The letter of the network path to map to.
    - This letter must not already be in use with Windows.
    type: str
    required: yes
  password:
    description:
    - The password for C(username) that is used when testing the initial
      connection.
    - This is never saved with a mapped drive, use the M(win_credential) module
      to persist a username and password for a host.
    type: str
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
    type: str
    choices: [ absent, present ]
    default: present
  username:
    description:
    - The username that is used when testing the initial connection.
    - This is never saved with a mapped drive, the the M(win_credential) module
      to persist a username and password for a host.
    - This is required if the mapped drive requires authentication with
      custom credentials and become, or CredSSP cannot be used.
    - If become or CredSSP is used, any credentials saved with
      M(win_credential) will automatically be used instead.
    type: str
notes:
- You cannot use this module to access a mapped drive in another Ansible task,
  drives mapped with this module are only accessible when logging in
  interactively with the user through the console or RDP.
- It is recommend to run this module with become or CredSSP when the remote
  path requires authentication.
- When using become or CredSSP, the task will have access to any local
  credentials stored in the user's vault.
- If become or CredSSP is not available, the I(username) and I(password)
  options can be used for the initial authentication but these are not
  persisted.
seealso:
- module: win_credential
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
    win_credential:
      name: server
      type: domain_password
      username: username@DOMAIN
      secret: Password01
      state: present

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

- name: Create mapped drive with credentials that do not persist on the next logon
  win_mapped_drive:
    letter: M
    path: \\SERVER\C$
    state: present
    username: '{{ ansible_user }}'
    password: '{{ ansible_password }}'
'''

RETURN = r'''
'''
