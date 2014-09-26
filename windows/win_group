#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Chris Hoffman <choffman@chathamfinancial.com>
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
module: win_group
version_added: "1.7"
short_description: Add and remove local groups
description:
    - Add and remove local groups
options:
  name:
    description:
      - Name of the group
    required: true
    default: null
    aliases: []
  description:
    description:
      - Description of the group
    required: false
    default: null
    aliases: []
  state:
    description:
      - Create or remove the group
    required: false
    choices:
      - present
      - absent
    default: present
    aliases: []
author: Chris Hoffman
'''

EXAMPLES = '''
  # Create a new group
  win_group:
    name: deploy
    description: Deploy Group
    state: present

  # Remove a group
  win_group:
    name: deploy
    state: absent
'''
