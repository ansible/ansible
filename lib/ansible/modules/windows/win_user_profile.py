#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_user_profile
version_added: '2.8'
short_description: Manages the Windows user profiles.
description:
- Used to create or remove user profiles on a Windows host.
- This can be used to create a profile before a user logs on or delete a
  profile when removing a user account.
- A profile can be created for both a local or domain account.
options:
  name:
    description:
    - Specifies the base name for the profile path.
    - When I(state) is C(present) this is used to create the profile for
      I(username) at a specific path within the profile directory.
    - This cannot be used to specify a path outside of the profile directory
      but rather it specifies a folder(s) within this directory.
    - If a profile for another user already exists at the same path, then a 3
      digit incremental number is appended by Windows automatically.
    - When I(state) is C(absent) and I(username) is not set, then the module
      will remove all profiles that point to the profile path derived by this
      value.
    - This is useful if the account no longer exists but the profile still
      remains.
    type: str
  remove_multiple:
    description:
    - When I(state) is C(absent) and the value for I(name) matches multiple
      profiles the module will fail.
    - Set this value to C(yes) to force the module to delete all the profiles
      found.
    default: no
    type: bool
  state:
    description:
    - Will ensure the profile exists when set to C(present).
    - When creating a profile the I(username) option must be set to a valid
      account.
    - Will remove the profile(s) when set to C(absent).
    - When removing a profile either I(username) must be set to a valid
      account, or I(name) is set to the profile's base name.
    default: present
    choices:
    - absent
    - present
    type: str
  username:
    description:
    - The account name of security identifier (SID) for the profile.
    - This must be set when I(state) is C(present) and must be a valid account
      or the SID of a valid account.
    - When I(state) is C(absent) then this must still be a valid account number
      but the SID can be a deleted user's SID.
seealso:
- module: win_user
- module: win_domain_user
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Create a profile for an account
  win_user_profile:
    username: ansible-account
    state: present

- name: Create a profile for an account at C:\Users\ansible
  win_user_profile:
    username: ansible-account
    name: ansible
    state: present

- name: Remove a profile for a still valid account
  win_user_profile:
    username: ansible-account
    state: absent

- name: Remove a profile for a deleted account
  win_user_profile:
    name: ansible
    state: absent

- name: Remove a profile for a deleted account based on the SID
  win_user_profile:
    username: S-1-5-21-3233007181-2234767541-1895602582-1305
    state: absent

- name: Remove multiple profiles that exist at the basename path
  win_user_profile:
    name: ansible
    state: absent
    remove_multiple: yes
'''

RETURN = r'''
path:
  description: The full path to the profile for the account. This will be null
    if C(state=absent) and no profile was deleted.
  returned: always
  type: str
  sample: C:\Users\ansible
'''
