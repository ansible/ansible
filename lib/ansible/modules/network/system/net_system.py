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
module: net_system
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage the system attributes on network devices
description:
  - This module provides declarative management of node system attributes
    on network devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
  domain_name:
    description:
      - Configure the IP domain name
        on the remote device to the provided value. Value
        should be in the dotted name form and will be
        appended to the C(hostname) to create a fully-qualified
        domain name.
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
  lookup_source:
    description:
      - Provides one or more source
        interfaces to use for performing DNS lookups.  The interface
        provided in C(lookup_source) must be a valid interface configured
        on the device.
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostname and domain name
  net_system:
    hostname: ios01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - cisco.com

- name: remove configuration
  net_system:
    state: absent

- name: configure DNS lookup sources
  net_system:
    lookup_source: MgmtEth0/0/CPU0/0

- name: configure name servers
  net_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname ios01
    - ip domain name test.example.com

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
