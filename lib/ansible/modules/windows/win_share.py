#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
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
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_share
version_added: "2.1"
short_description: Manage Windows shares
description:
  - Add, modify or remove Windows share and set share permissions.
requirements:
  - As this module used newer cmdlets like New-SmbShare this can only run on
    Windows 8 / Windows 2012 or newer.
  - This is due to the reliance on the WMI provider MSFT_SmbShare
    U(https://msdn.microsoft.com/en-us/library/hh830471) which was only added
    with these Windows releases.
options:
  name:
    description:
      - Share name.
    required: True
  path:
    description:
      - Share directory.
    required: True
  state:
    description:
      - Specify whether to add C(present) or remove C(absent) the specified share.
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - Share description
  list:
    description:
      - Specify whether to allow or deny file listing, in case user got no permission on share.
    type: bool
    default: 'no'
  read:
    description:
      - Specify user list that should get read access on share, separated by comma.
  change:
    description:
      - Specify user list that should get read and write access on share, separated by comma.
  full:
    description:
      - Specify user list that should get full access on share, separated by comma.
  deny:
    description:
      - Specify user list that should get no access, regardless of implied access on share, separated by comma.
  caching_mode:
    description:
      - Set the CachingMode for this share.
    choices:
      - BranchCache
      - Documents
      - Manual
      - None
      - Programs
      - Unknown
    default: "Manual"
    version_added: "2.3"
  encrypt:
    description: Sets whether to encrypt the traffic to the share or not.
    type: bool
    default: 'no'
    version_added: "2.4"
author:
  - Hans-Joachim Kliemeck (@h0nIg)
  - David Baumann (@daBONDi)
'''

EXAMPLES = r'''
# Playbook example
# Add share and set permissions
---
- name: Add secret share
  win_share:
    name: internal
    description: top secret share
    path: C:\shares\internal
    list: no
    full: Administrators,CEO
    read: HR-Global
    deny: HR-External

- name: Add public company share
  win_share:
    name: company
    description: top secret share
    path: C:\shares\company
    list: yes
    full: Administrators,CEO
    read: Global

- name: Remove previously added share
  win_share:
    name: internal
    state: absent
'''

RETURN = r'''
actions:
    description: A list of action cmdlets that were run by the module.
    returned: success
    type: list
    sample: ['New-SmbShare -Name share -Path C:\temp']
'''
