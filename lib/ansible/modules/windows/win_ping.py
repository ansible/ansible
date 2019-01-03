#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
  - For Network targets, use the M(net_ping) module instead.
options:
  data:
    description:
      - Alternate data to return instead of 'pong'.
      - If this parameter is set to C(crash), the module will cause an exception.
    type: str
    default: pong
seealso:
- module: ping
author:
- Chris Church (@cchurch)
'''

EXAMPLES = r'''
# Test connectivity to a windows host
# ansible winserver -m win_ping

- name: Example from an Ansible Playbook
  win_ping:

- name: Induce an exception to see what happens
  win_ping:
    data: crash
'''

RETURN = r'''
ping:
    description: Value provided with the data parameter.
    returned: success
    type: str
    sample: pong
'''
