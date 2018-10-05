#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_hosts
version_added: '2.8'
short_description: Modify hosts file entries on windows.
description:
  - Allows  the addition, replacement, and removal of ip addresses and aliases from host entries in the windows system hosts file.
  - Modifies %windir%\system32\drivers\etc\hosts.
options:
  state:
    description:
      - Whether the host should be present or absent.
      - If only C(host_name) is provided when C(state=absent), the host_name alias will be removed from all host entries.
      - If only C(ip_address) is provided when C(state=absent), the host entry and all aliases will be removed.
    choices:
      - absent
      - present
    default: present
  host_name:
    description:
      - An alias or dns name for the host.
      - required for C(state=present).
  ip_address:
    description:
      - The ip address of the host.
      - Required for C(state=present).
  ip_action:
    choices:
      - add
      - replace
    description:
      - Only applicable with C(state=absent).
      - If C(add), the I(host_name) will be added as an entry to I(ip_address).
      - If C(replace), the I(host_name) will be added as an entry to I(ip_address) and removed from any other entries.
    default: replace
author:
  - Micah Hunsberger (@mhunsber)
notes:
  - See also M(win_template), M(win_file), M(win_copy)
'''

EXAMPLES = r'''
- name: Map localhost to 127.0.0.1
  win_hosts:
    state: present
    host_name: localhost
    ip_address: 127.0.0.1

- name: Add ::1 as an ip for localhost
  win_environment:
    state: present
    ip_action: add
    host_name: localhost
    ip_address: '::1'

- name: Remove 'foo' from the list of aliases for 192.168.1.100
  win_hosts:
    state: absent
    host_name: foo
    ip_address: 192.168.1.100

- name: Remove alias 'bar' from all host entries
  win_hosts:
    state: absent
    host_name: bar

- name: Remove 10.2.0.1 from the list of hosts
  win_hosts:
    state: absent
    ip_address: 10.2.0.1
'''

RETURN = r'''
'''
