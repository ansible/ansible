#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: net_vrf
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VRFs on network devices
description:
  - This module provides declarative management of VRFs
    on network devices.
deprecated:
    removed_in: "2.13"
    alternative: Use platform-specific "[netos]_vrf" module
    why: Updated modules released with more functionality
extends_documentation_fragment: network_agnostic
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
      - Purge VRFs not defined in the I(aggregate) parameter.
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

- name: Create aggregate of VRFs with purge
  net_vrf:
    aggregate:
      - { name: test4, rd: "1:204" }
      - { name: test5, rd: "1:205" }
    state: present
    purge: yes

- name: Delete aggregate of VRFs
  net_vrf:
    aggregate:
      - name: test2
      - name: test3
      - name: test4
      - name: test5
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
