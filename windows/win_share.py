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

DOCUMENTATION = '''
---
module: win_share
version_added: "2.1"
short_description: Manage Windows shares
description:
     - Add, modify or remove Windows share and set share permissions.
requirements:
    - Windows 8.1 / Windows 2012 or newer
options:
  name:
    description:
      - Share name
    required: yes
  path:
    description:
      - Share directory
    required: yes
  state:
    description:
      - Specify whether to add C(present) or remove C(absent) the specified share
    required: no
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - Share description
    required: no
    default: none
  list:
    description:
      - Specify whether to allow or deny file listing, in case user got no permission on share
    required: no
    choices:
      - yes
      - no
    default: none
  read:
    description:
      - Specify user list that should get read access on share, separated by comma.
    required: no
    default: none
  change:
    description:
      - Specify user list that should get read and write access on share, separated by comma.
    required: no
    default: none
  full:
    description:
      - Specify user list that should get full access on share, separated by comma.
    required: no
    default: none
  deny:
    description:
      - Specify user list that should get no access, regardless of implied access on share, separated by comma.
    required: no
    default: none
author: Hans-Joachim Kliemeck (@h0nIg)
'''

EXAMPLES = '''
# Playbook example
# Add share and set permissions
---
- name: Add secret share
  win_share:
    name: internal
    description: top secret share
    path: C:/shares/internal
    list: 'no'
    full: Administrators,CEO
    read: HR-Global
    deny: HR-External

- name: Add public company share
  win_share:
    name: company
    description: top secret share
    path: C:/shares/company
    list: 'yes'
    full: Administrators,CEO
    read: Global

# Remove previously added share
  win_share:
    name: internal
    state: absent
'''

RETURN = '''

'''