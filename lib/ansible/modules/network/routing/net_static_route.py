#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: net_static_route
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage static IP routes on network devices
description:
  - This module provides declarative management of static
    IP routes on network devices.
options:
  prefix:
    description:
      - Network prefix of the static route.
    required: true
  mask:
    description:
      - Network prefix mask of the static route.
    required: true
  next_hop:
    description:
      - Next hop IP of the static route.
    required: true
  admin_distance:
    description:
      - Admin distance of the static route.
  collection:
    description: List of static route definitions
  purge:
    description:
      - Purge static routes not defined in the collections parameter.
    default: no
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure static route
  net_static_route:
    prefix: 192.168.2.0
    mask: 255.255.255.0
    next_hop: 10.0.0.1

- name: remove configuration
  net_static_route:
    prefix: 192.168.2.0
    mask: 255.255.255.0
    next_hop: 10.0.0.1
    state: absent

- name: configure collections of static routes
  net_static_route:
    collection:
      - { prefix: 192.168.2.0, mask 255.255.255.0, next_hop: 10.0.0.1 }
      - { prefix: 192.168.3.0, mask 255.255.255.0, next_hop: 10.0.2.1 }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ip route 192.168.2.0/24 10.0.0.1
"""
