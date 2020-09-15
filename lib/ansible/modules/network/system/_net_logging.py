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
module: net_logging
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on network devices.
deprecated:
    removed_in: "2.13"
    alternative: Use platform-specific "[netos]_logging" module
    why: Updated modules released with more functionality
extends_documentation_fragment: network_agnostic
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['console', 'host']
  name:
    description:
      - If value of C(dest) is I(host) it indicates file-name
        the host name to be notified.
  facility:
    description:
      - Set logging facility.
  level:
    description:
      - Set logging severity levels.
  aggregate:
    description: List of logging definitions.
  purge:
    description:
      - Purge logging not defined in the I(aggregate) parameter.
    default: no
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure console logging
  net_logging:
    dest: console
    facility: any
    level: critical

- name: remove console logging configuration
  net_logging:
    dest: console
    state: absent

- name: configure host logging
  net_logging:
    dest: host
    name: 192.0.2.1
    facility: kernel
    level: critical

- name: Configure file logging using aggregate
  net_logging:
    dest: file
    aggregate:
    - name: test-1
      facility: pfe
      level: critical
    - name: test-2
      facility: kernel
      level: emergency
- name: Delete file logging using aggregate
  net_logging:
    dest: file
    aggregate:
    - name: test-1
      facility: pfe
      level: critical
    - name: test-2
      facility: kernel
      level: emergency
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - logging console critical
"""
