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
module: net_vlan
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VLANs on network devices
description:
  - This module provides declarative management of VLANs
    on network devices.
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN.
  interfaces:
    description:
      - List of interfaces the VLAN should be configured on.
  collection:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the collections parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
"""

EXAMPLES = """
- name: configure VLAN ID and name
  net_vlan:
    vlan_id: 20
    name: test-vlan

- name: remove configuration
  net_vlan:
    state: absent

- name: configure VLAN state
  net_vlan:
    vlan_id:
    state: suspend

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan 20
    - name test-vlan

rpc:
  description: load-configuration RPC send to the device
  returned: C(rpc) is returned only for junos device
            when configuration is changed on device
  type: string
  sample: "<vlans><vlan><name>test-vlan-4</name></vlan></vlans>"
"""
