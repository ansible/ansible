#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Michae Eaton <meaton@iforium.com>
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

DOCUMENTATION = r'''
---
module: win_firewall
short_description: Manages Windows Firewall
description:
    - Manages Windows Firewall
options:
  profile:
    description:
    - Specify the profile to change
    choices:
    - Public
    - Domain
    - Private
    - *
  enabled:
    description:
    - true or false

author: "Michael Eaton (@MichaelEaton83)"
'''

EXAMPLES = r'''
- name: Manage Windows Firewall.
  win_firewall:
     profile: "{{ item }}"
     enabled: false
  with_items:
      - Domain
      - Public
      - Private
  tags: disable_firewall

- name: Manage Windows Firewall.
  win_firewall:
     profile: Domain
     enabled: true
  tags: enable_firewall
'''