#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey_feature
version_added: '2.7'
short_description: Manages Chocolatey features
description:
- Used to enable or disable features in Chocolatey.
options:
  name:
    description:
    - The name of the feature to manage.
    - Run C(choco.exe feature list) to get a list of features that can be
      managed.
    required: yes
  state:
    description:
    - When C(disabled) then the feature will be disabled.
    - When C(enabled) then the feature will be enabled.
    choices:
    - disabled
    - enabled
    default: enabled
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: disable file checksum matching
  win_chocolatey_feature:
    name: checksumFiles
    state: disabled

- name: stop Chocolatey on the first package failure
  win_chocolatey_feature:
    name: stopOnFirstPackageFailure
    state: enabled
'''

RETURN = r'''
'''
