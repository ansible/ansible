#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Daniele Lazzari <lazzari@mailup.com>
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

# This is a windows documentation stub.  Actual code lives in the .ps1
# file of the same name.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_route
version_added: "2.4"
short_description: Add or remove a static route.
description:
    - Add or remove a static route.
options:
  destination:
    description:
      - Destination IP address in CIDR format (ip address/prefix length)
    required: true
  gateway:
    description:
        - The gateway used by the static route.
        - If C(gateway) is not provided it will be set to C(0.0.0.0).
  metric:
    description:
        - Metric used by the static route.
    default: 1
  state:
    description:
      - If present, it adds a network static route.
        If absent, it removes a network static route.
    default: present
notes:
  - Works only with Windows 2012 R2 and newer.
author: Daniele Lazzari
'''

EXAMPLES = r'''
---

- name: Add a network static route
  win_route:
    destination: 192.168.2.10/32
    gateway: 192.168.1.1
    metric: 1
    state: present

- name: Remove a network static route
  win_route:
    destination: 192.168.2.10/32
    state: absent
'''
RETURN = r'''
output:
    description: A message describing the task result.
    returned: always
    type: string
    sample: "Route added"
'''
