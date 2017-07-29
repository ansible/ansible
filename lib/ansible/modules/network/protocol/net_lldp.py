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
module: net_lldp
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage LLDP service configuration on network devices
description:
  - This module provides declarative management of LLDP service configuration
    on network devices.
options:
  state:
    description:
      - State of the LLDP service configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP service
  net_lldp:
    state: present

- name: Disable LLDP service
  net_lldp:
    state: lldp
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set service lldp
"""
