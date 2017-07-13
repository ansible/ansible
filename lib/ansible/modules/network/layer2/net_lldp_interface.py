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
module: net_lldp_interface
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage LLDP interfaces configuration on network devices
description:
  - This module provides declarative management of LLDP interfaces configuration
    on network devices.
options:
  name:
    description: Name of the interface LLDP should be configured on.
  aggregate:
    description: List of interfaces LLDP should be configured on.
  purge:
    description:
      - Purge interfaces not defined in the interfaces parameter.
    default: no
  state:
    description:
      - State of the LLDP configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP on specific interface
  net_lldp_interface:
    name:  eth1
    state: present

- name: Disable LLDP on specific interface
  net_lldp_interface:
    name:  eth1
    state: absent

- name: Enable LLDP on list of interfaces
  net_lldp_interface:
    aggregate:
      - { name: eth1 }
      - { name: eth2, state: absent }
    state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set service lldp eth1
    - set service lldp eth2
"""
