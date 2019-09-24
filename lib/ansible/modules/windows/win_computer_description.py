#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, RusoSova
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: win_computer_description
short_description: Set windows description, owner and organization
description:
 - This module sets Windows description that is shown under My Computer properties. Module also sets
   Windows license owner and organization. License information can be viewed by running winver commad.
options:
 description:
   description:
     - String value to apply to Windows descripton. Specify value of "" to clear the value.
   required: false
   type: str
 organization:
   description:
     - String value of organization that the Windows is licensed to. Specify value of "" to clear the value.
   required: false
   type: str
 owner:
   description:
     - String value of the persona that the Windows is licensed to. Specify value of "" to clear the value.
   required: false
   type: str
version_added: '2.10'
author:
 - RusoSova (@RusoSova)
'''

EXAMPLES = r'''
- name: Set Windows description, owner and organization
  win_computer_description:
   description: Best Box
   owner: RusoSova
   organization: MyOrg
  register: result

- name: Set Windows description only
  win_computer_description:
   description: This is my Windows machine
  register: result

- name: Set organization and clear owner field
  win_computer_description:
   owner: ''
   organization: Black Mesa

- name: Clear organization, description and owner
  win_computer_description:
   organization: ""
   owner: ""
   description: ""
  register: result
'''

RETURN = r'''
#
'''
