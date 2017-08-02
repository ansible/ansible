#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
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
module: win_group_membership
version_added: "2.4"
short_description: Manage Windows local group membership
description:
     - Allows the addition and removal of local, service and domain users,
       and domain groups from a local group.
options:
  name:
    description:
      - Name of the local group to manage membership on.
    required: true
  members:
    description:
      - A list of members to ensure are present/absent from the group.
      - Accepts local users as username, .\username, and SERVERNAME\username.
      - Accepts domain users and groups as DOMAIN\username and username@DOMAIN.
      - Accepts service users as NT AUTHORITY\username.
    required: true
  state:
    description:
      - Desired state of the members in the group.
    choices:
      - present
      - absent
    default: present
author:
    - Andrew Saraceni (@andrewsaraceni)
'''

EXAMPLES = r'''
- name: Add a local and domain user to a local group
  win_group_membership:
    name: Remote Desktop Users
    members:
      - NewLocalAdmin
      - DOMAIN\TestUser
    state: present

- name: Remove a domain group and service user from a local group
  win_group_membership:
    name: Backup Operators
    members:
      - DOMAIN\TestGroup
      - NT AUTHORITY\SYSTEM
    state: absent
'''

RETURN = r'''
name:
    description: The name of the target local group.
    returned: always
    type: string
    sample: Administrators
added:
    description: A list of members added when C(state) is C(present); this is
      empty if no members are added.
    returned: success and C(state) is C(present)
    type: list
    sample: ["NewLocalAdmin", "DOMAIN\\TestUser"]
removed:
    description: A list of members removed when C(state) is C(absent); this is
      empty if no members are removed.
    returned: success and C(state) is C(absent)
    type: list
    sample: ["DOMAIN\\TestGroup", "NT AUTHORITY\\SYSTEM"]
members:
    description: A list of all local group members at completion; this is empty
      if the group contains no members.
    returned: success
    type: list
    sample: ["DOMAIN\\TestUser", "NewLocalAdmin"]
'''
