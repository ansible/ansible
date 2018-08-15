#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey_config
version_added: '2.7'
short_description: Manages Chocolatey config settings
description:
- Used to manage Chocolatey config settings as well as unset the values.
options:
  name:
    description:
    - The name of the config setting to manage.
    - See U(https://chocolatey.org/docs/chocolatey-configuration) for a list of
      valid configuration settings that can be changed.
    - Any config values that contain encrypted values like a password are not
      idempotent as the plaintext value cannot be read.
    required: yes
  state:
    description:
    - When C(absent), it will ensure the setting is unset or blank.
    - When C(present), it will ensure the setting is set to the value of
      I(value).
    choices:
    - absent
    - present
    default: present
  value:
    description:
    - Used when C(state=present) that contains the value to set for the config
      setting.
    - Cannot be null or an empty string, use C(state=absent) to unset a config
      value instead.
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: set the cache location
  win_chocolatey_config:
    name: cacheLocation
    state: present
    value: D:\chocolatey_temp

- name: unset the cache location
  win_chocolatey_config:
    name: cacheLocation
    state: absent
'''

RETURN = r'''
'''
