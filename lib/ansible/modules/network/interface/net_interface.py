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
module: net_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on network devices
description:
  - This module provides declarative management of Interfaces
    on network devices.
extends_documentation_fragment: network_agnostic
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
      - Configure interface link status.
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
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
    default: 10
  aggregate:
    description: List of Interfaces definitions.
  purge:
    description:
      - Purge Interfaces not defined in the aggregate parameter.
        This applies only for logical interface.
    default: no
  state:
    description:
      - State of the Interface configuration, C(up) indicates present and
        operationally up and C(down) indicates present and operationally C(down)
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
    enabled: True

- name: make interface down
  net_interface:
    name: ge-0/0/1
    description: test-interface
    enabled: False

- name: Create interface using aggregate
  net_interface:
    aggregate:
      - { name: ge-0/0/1, description: test-interface-1 }
      - { name: ge-0/0/2, description: test-interface-2 }
    speed: 1g
    duplex: full
    mtu: 512

- name: Delete interface using aggregate
  junos_interface:
    aggregate:
      - { name: ge-0/0/1 }
      - { name: ge-0/0/2 }
    state: absent

- name: Check intent arguments
  net_interface:
    name: fxp0
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)

- name: Config + intent
  net_interface:
    name: fxp0
    enabled: False
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
