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
short_description: Manages hosts file entries on Windows.
description:
  - Manages hosts file entries on Windows.
  - Maps IPv4 or IPv6 addresses to canonical names.
  - Adds, removes, or sets cname records for ip and hostname pairs.
  - Modifies %windir%\\system32\\drivers\\etc\\hosts.
options:
  state:
    description:
      - Whether the entry should be present or absent.
      - If only I(canonical_name) is provided when C(state=absent), then
        all hosts entries with the canonical name of I(canonical_name)
        will be removed.
      - If only I(ip_address) is provided when C(state=absent), then all
        hosts entries with the ip address of I(ip_address) will be removed.
      - If I(ip_address) and I(canonical_name) are both omitted when
        C(state=absent), then all hosts entries will be removed.
    choices:
      - absent
      - present
    default: present
    type: str
  canonical_name:
    description:
      - A canonical name for the host entry.
      - required for C(state=present).
    type: str
  ip_address:
    description:
      - The ip address for the host entry.
      - Can be either IPv4 (A record) or IPv6 (AAAA record).
      - Required for C(state=present).
    type: str
  aliases:
    description:
      - A list of additional names (cname records) for the host entry.
      - Only applicable when C(state=present).
    type: list
  action:
    choices:
      - add
      - remove
      - set
    description:
      - Controls the behavior of I(aliases).
      - Only applicable when C(state=present).
      - If C(add), each alias in I(aliases) will be added to the host entry.
      - If C(set), each alias in I(aliases) will be added to the host entry,
        and other aliases will be removed from the entry.
    default: set
    type: str
author:
  - Micah Hunsberger (@mhunsber)
notes:
  - Each canonical name can only be mapped to one IPv4 and one IPv6 address.
    If I(canonical_name) is provided with C(state=present) and is found
    to be mapped to another IP address that is the same type as, but unique
    from I(ip_address), then I(canonical_name) and all I(aliases) will
    be removed from the entry and added to an entry with the provided IP address.
  - Each alias can only be mapped to one canonical name. If I(aliases) is provided
    with C(state=present) and an alias is found to be mapped to another canonical
    name, then the alias will be removed from the entry and either added to or removed
    from (depending on I(action)) an entry with the provided canonical name.
seealso:
  - module: win_template
  - module: win_file
  - module: win_copy
'''

EXAMPLES = r'''
- name: Add 127.0.0.1 as an A record for localhost
  win_hosts:
    state: present
    canonical_name: localhost
    ip_address: 127.0.0.1

- name: Add ::1 as an AAAA record for localhost
  win_hosts:
    state: present
    canonical_name: localhost
    ip_address: '::1'

- name: Remove 'bar' and 'zed' from the list of aliases for foo (192.168.1.100)
  win_hosts:
    state: present
    canonical_name: foo
    ip_address: 192.168.1.100
    action: remove
    aliases:
      - bar
      - zed

- name: Remove hosts entries with canonical name 'bar'
  win_hosts:
    state: absent
    canonical_name: bar

- name: Remove 10.2.0.1 from the list of hosts
  win_hosts:
    state: absent
    ip_address: 10.2.0.1

- name: Ensure all name resolution is handled by DNS
  win_hosts:
    state: absent
'''

RETURN = r'''
'''
