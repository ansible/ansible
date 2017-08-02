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
module: net_vrf
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VRFs on network devices
description:
  - This module provides declarative management of VRFs
    on network devices.
options:
  name:
    description:
      - Name of the VRF.
  interfaces:
    description:
      - List of interfaces the VRF should be configured on.
  aggregate:
    description: List of VRFs definitions
  purge:
    description:
      - Purge VRFs not defined in the aggregates parameter.
    default: no
  state:
    description:
      - State of the VRF configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create VRF named MANAGEMENT
  net_vrf:
    name: MANAGEMENT

- name: remove VRF named MANAGEMENT
  net_vrf:
    name: MANAGEMENT
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - vrf definition MANAGEMENT
"""
