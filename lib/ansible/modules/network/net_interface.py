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
module: net_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on network devices
description:
  - This module provides declarative management of Interfaces
    on network devices.
options:
  name:
    description:
      - Name of the Interface.
    required: true
  description:
    description:
      - Description of Interface.
  enabled:
    description:
      - Configure operational status of the interface link.
        If value is I(yes) interface is configured in up state,
        for I(no) interface is configured in down state.
    default: yes
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet.
  duplex:
    description:
      - Interface link status
    default: auto
    choices: ['full', 'half', 'auto']
  tx_rate:
    description:
      - Transmit rate
  rx_rate:
    description:
      - Receiver rate
  collection:
    description: List of Interfaces definitions.
  purge:
    description:
      - Purge Interfaces not defined in the collections parameter.
        This applies only for logical interface.
    default: no
  state:
    description:
      - State of the Interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure interface
  net_interface:
    name: ge-0/0/1
    description: test-interface

- name: remove interface
  net_interface:
    name: ge-0/0/1
    state: absent

- name: make interface up
  net_interface:
    name: ge-0/0/1
    description: test-interface
    state: present
    enabled: True

- name: make interface down
  net_interface:
    name: ge-0/0/1
    description: test-interface
    state: present
    enabled: False
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface 20
    - name test-interface
rpc:
  description: load-configuration RPC send to the device
  returned: C(rpc) is returned only for junos device
            when configuration is changed on device
  type: string
  sample: >
            <interfaces>
                <interface>
                    <name>ge-0/0/0</name>
                    <description>test interface</description>
                </interface>
            </interfaces>

"""
