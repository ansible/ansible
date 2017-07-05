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
module: net_l2_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Layer-2 interface on network devices
description:
  - This module provides declarative management of Layer-2 interface
    on network devices.
options:
  name:
    description:
      - Name of the interface excluding any logical unit number.
  collection:
    description:
      - List of Layer-2 interface definitions.
  mode:
    description:
      - Mode in which interface needs to be configured.
    default: access
    choices: ['access', 'trunk']
  access_vlan:
    description:
      - Configure given VLAN in access port.
  trunk_vlans:
    description:
      - List of VLANs to be configured in trunk port.
  native_vlan:
    description:
      - Native VLAN to be configured in trunk port.
  trunk_allowed_vlans:
    description:
      - List of allowed VLAN's in a given trunk port.
  state:
    description:
      - State of the Layer-2 Interface configuration.
    default: present
    choices: ['present', 'absent',]
"""

EXAMPLES = """
- name: configure Layer-2 interface
  net_l2_interface:
    name: gigabitethernet0/0/1
    mode: access
    access_vlan: 30

- name: remove Layer-2 interface configuration
  net_l2_interface:
    name: gigabitethernet0/0/1
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface gigabitethernet0/0/1
    - switchport mode access
    - switchport access vlan 30
"""
