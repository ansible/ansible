#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Matt Martz <matt@sivel.net>, and others
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
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_user
version_added: "1.7"
short_description: Manages local Windows user accounts
description:
     - Manages local Windows user accounts
     - For non-Windows targets, use the M(user) module instead.
options:
  name:
    description:
      - Name of the user to create, remove or modify.
    required: true
  fullname:
    description:
      - Full name of the user
    required: false
    default: null
    version_added: "1.9"
  description:
    description:
      - Description of the user
    required: false
    default: null
    version_added: "1.9"
  password:
    description:
      - Optionally set the user's password to this (plain text) value.
    required: false
    default: null
  update_password:
    description:
      - C(always) will update passwords if they differ.  C(on_create) will
        only set the password for newly created users.
    required: false
    choices: [ 'always', 'on_create' ]
    default: always
    version_added: "1.9"
  password_expired:
    description:
      - C(yes) will require the user to change their password at next login.
        C(no) will clear the expired password flag.
    required: false
    choices: [ 'yes', 'no' ]
    default: null
    version_added: "1.9"
  password_never_expires:
    description:
      - C(yes) will set the password to never expire.  C(no) will allow the
        password to expire.
    required: false
    choices: [ 'yes', 'no' ]
    default: null
    version_added: "1.9"
  user_cannot_change_password:
    description:
      - C(yes) will prevent the user from changing their password.  C(no) will
        allow the user to change their password.
    required: false
    choices: [ 'yes', 'no' ]
    default: null
    version_added: "1.9"
  account_disabled:
    description:
      - C(yes) will disable the user account.  C(no) will clear the disabled
        flag.
    required: false
    choices: [ 'yes', 'no' ]
    default: null
    version_added: "1.9"
  account_locked:
    description:
      - C(no) will unlock the user account if locked.
    required: false
    choices: [ 'no' ]
    default: null
    version_added: "1.9"
  groups:
    description:
      - Adds or removes the user from this comma-separated lis of groups,
        depending on the value of I(groups_action). When I(groups_action) is
        C(replace) and I(groups) is set to the empty string ('groups='), the
        user is removed from all groups.
    required: false
    version_added: "1.9"
  groups_action:
    description:
      - If C(replace), the user is added as a member of each group in
        I(groups) and removed from any other groups.  If C(add), the user is
        added to each group in I(groups) where not already a member.  If
        C(remove), the user is removed from each group in I(groups).
    required: false
    choices: [ "replace", "add", "remove" ]
    default: "replace"
    version_added: "1.9"
  state:
    description:
      - When C(present), creates or updates the user account.  When C(absent),
        removes the user account if it exists.  When C(query) (new in 1.9),
        retrieves the user account details without making any changes.
    required: false
    choices:
      - present
      - absent
      - query
    default: present
    aliases: []
notes:
     - For non-Windows targets, use the M(user) module instead.
author:
    - "Paul Durivage (@angstwad)"
    - "Chris Church (@cchurch)"
'''

EXAMPLES = r'''
- name: Ensure user bob is present
  win_user:
    name: bob
    password: B0bP4ssw0rd
    state: present
    groups:
      - Users

- name: Ensure user bob is absent
  win_user:
    name: bob
    state: absent
'''
