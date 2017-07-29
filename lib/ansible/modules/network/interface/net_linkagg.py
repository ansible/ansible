#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: net_linkagg
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage link aggregation groups on network devices
description:
  - This module provides declarative management of link aggregation groups
    on network devices.
options:
  name:
    description:
      - Name of the link aggregation group.
    required: true
  mode:
    description:
      - Mode of the link aggregation group. A value of C(on) will enable LACP.
        C(active) configures the link to actively information about the state of the link,
        or it can be configured in C(passive) mode ie. send link state information only when
        received them from another link.
    default: on
    choices: ['on', 'active', 'passive']
  members:
    description:
      - List of members interfaces of the link aggregation group. The value can be
        single interface or list of interfaces.
    required: true
  min_links:
    description:
      - Minimum members that should be up
        before bringing up the link aggregation group.
  aggregate:
    description: List of link aggregation definitions.
  purge:
    description:
      - Purge link aggregation groups not defined in the aggregates parameter.
    default: no
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure link aggregation group
  net_linkagg:
    name: bond0
    members:
      - eth0
      - eth1

- name: remove configuration
  net_linkagg:
    name: bond0
    state: absent

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set interfaces bonding bond0
    - set interfaces ethernet eth0 bond-group 'bond0'
    - set interfaces ethernet eth1 bond-group 'bond0'
"""
