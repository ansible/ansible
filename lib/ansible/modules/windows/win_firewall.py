#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Michael Eaton <meaton@iforium.com>
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
module: win_firewall
version_added: "2.4"
short_description: Manages Windows Firewall
description:
    - Manages Windows Firewall
options:
  profile:
    description:
    - specify the profile to change
    choices:
    - Public
    - Domain
    - Private
  state:
    description:
    - set state of firewall for given profile
    choices:
    - enabled
    - disabled

author: "Michael Eaton (@MichaelEaton83)"
'''

EXAMPLES = r'''
- name: Enable all firewalls
  win_firewall:
      state: enabled
      profiles:
      - Domain
      - Public
      - Private
  tags: enable_firewall

- name: Disable Domain firewall
  win_firewall:
     state: disabled
     profiles:
     - Domain
  tags: disable_firewall
'''

RETURN = r'''
profile:
    description: chosen profile
    returned: always
    type: string
    sample: Domain
enabled:
    description: current firewall status for chosen profile (after any potential change)
    returned: always
    type: bool
    sample: true
'''
