#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Hitachi ID Systems, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a windows documentation stub. The actual code lives in the .ps1
# file of the same name.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_dns_record
version_added: "2.8"
short_description: Manage Windows Server DNS records
description:
- Manages DNS records within an existing Windows Server DNS zone
author: John Nelson (@johnboy2)
options:
  name:
    description:
    - The name of the record
    required: yes
  state:
    description:
    - Whether the record should exist or not
    choices: [ absent, present ]
    default: present
  ttl:
    description:
    - The "time to live" of the record, in seconds. Must be at least 900
      (ie 15 minutes).
    default: 3600
  type:
    description:
    - The type of DNS record to manage.
    choices: [ A, AAAA, CNAME, MX, NS, TXT, PTR ]
    required: yes
  value:
    description:
    - The value(s) to specify. Required when `state=present`.
    aliases: [ values ]
  zone:
    description:
    - The name of the zone to manage (eg "example.com"). The zone must already
      exist.
    required: yes
'''

EXAMPLES = r'''
- name: Create database server alias
  win_dns_record:
    name: db1
    type: CNAME
    value: cgyl1404p.amer.example.com
    zone: amer.example.com

- name: Remove static record
  win_dns_record:
    name: db1
    type: A
    state: absent
    zone: amer.example.com
'''

RETURN = r'''
'''
