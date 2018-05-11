#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: net_static_route
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage static IP routes on network appliances (routers, switches et. al.)
description:
  - This module provides declarative management of static
    IP routes on network appliances (routers, switches et. al.).
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
  aggregate:
    description: List of static route definitions
  purge:
    description:
      - Purge static routes not defined in the I(aggregate) parameter.
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

- name: configure aggregates of static routes
  net_static_route:
    aggregate:
      - { prefix: 192.168.2.0, mask 255.255.255.0, next_hop: 10.0.0.1 }
      - { prefix: 192.168.3.0, mask 255.255.255.0, next_hop: 10.0.2.1 }

- name: Remove static route collections
  net_static_route:
    aggregate:
      - { prefix: 172.24.1.0/24, next_hop: 192.168.42.64 }
      - { prefix: 172.24.3.0/24, next_hop: 192.168.42.64 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ip route 192.168.2.0/24 10.0.0.1
"""
