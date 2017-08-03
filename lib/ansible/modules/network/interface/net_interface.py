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
      - Interface link status.
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
  aggregate:
    description: List of Interfaces definitions.
  purge:
    description:
      - Purge Interfaces not defined in the aggregate parameter.
        This applies only for logical interface.
    default: no
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
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
    state: up

- name: make interface down
  net_interface:
    name: ge-0/0/1
    description: test-interface
    state: down
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface 20
    - name test-interface
"""
