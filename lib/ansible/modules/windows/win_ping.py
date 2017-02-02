#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
#
# This file is part of Ansible
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_ping
version_added: "1.7"
short_description: A windows version of the classic ping module
description:
  - Checks management connectivity of a windows host.
  - This is NOT ICMP ping, this is just a trivial test module.
  - For non-Windows targets, use the M(ping) module instead.
options:
  data:
    description:
      - Alternate data to return instead of 'pong'.
      - If this parameter is set to C(crash), the module will cause an exception.
    default: pong
notes:
  - For non-Windows targets, use the M(ping) module instead.
author:
- Chris Church (@cchurch)
'''

EXAMPLES = r'''
# Test connectivity to a windows host
# ansible winserver -m win_ping

# Example from an Ansible Playbook
- win_ping:

# Induce an exception to see what happens
- win_ping:
    data: crash
'''

RETURN = '''
ping:
    description: value provided with the data parameter
    returned: success
    type: string
    sample: pong
'''
