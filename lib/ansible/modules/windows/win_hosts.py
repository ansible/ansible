#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_hosts
version_added: ''
short_description: Modify hosts file entries on windows
description:
- Allows addition, replacement, and removal of hostname entries in the windows system hosts file.
options:
  state:
    description:
      - Whether the host entry should be present or absent.
    choices:
	  - absent
	  - present
    default: present
  host_name:
    description:
      - The dns name of the host entry.
    required: true
  ip_address:
    description:
      - The ip address of the host entry.
      - Can be omitted for C(state=absent).
	  - Required for C(state=present).
author:
- Micah Hunsberger (@mhunsber)
notes:
- See also M(win_template), M(win_file), M(win_copy)
'''

EXAMPLES = r'''
- name: Ensure localhost is present
  win_hosts:
    state: present
    host_name: localhost
    ip_address: 127.0.0.1

- name: Remove localhost from the list of hosts
  win_environment:
    state: absent
    name: localhost
	
- name: Change localhost to the ipv6 loopback address
  win_hosts:
    state: present
	host_name: localhost
	ip_address: '::1'
'''