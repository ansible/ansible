#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
# Copyright: (c) 2017, Artem Zinenko <zinenkoartem@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_firewall_rule
version_added: "2.0"
author:
  - Artem Zinenko (@ar7z1)
  - Timothy Vandenbrande (@TimothyVandenbrande)
short_description: Windows firewall automation
description:
  - Allows you to create/remove/update firewall rules.
options:
  enabled:
    description:
      - Is this firewall rule enabled or disabled.
    type: bool
    default: 'yes'
    aliases: [ enable ]
  state:
    description:
      - Should this rule be added or removed.
    choices: [ absent, present ]
    default: present
  name:
    description:
      - The rules name
    required: yes
  direction:
    description:
      - Is this rule for inbound or outbound traffic.
    required: yes
    choices: [ in, out ]
  action:
    description:
      - What to do with the items this rule is for.
    required: yes
    choices: [ allow, block, bypass ]
  description:
    description:
      - Description for the firewall rule.
  localip:
    description:
      - The local ip address this rule applies to.
    default: any
  remoteip:
    description:
      - The remote ip address/range this rule applies to.
    default: any
  localport:
    description:
      - The local port this rule applies to.
  remoteport:
    description:
      - The remote port this rule applies to.
  program:
    description:
      - The program this rule applies to.
  service:
    description:
      - The service this rule applies to.
  protocol:
    description:
      - The protocol this rule applies to.
    default: any
  profiles:
    description:
      - The profile this rule applies to.
    type: list
    default: domain,private,public
    aliases: [ profile ]
  force:
    description:
    - Replace any existing rule by removing it first.
    - This is no longer required in 2.4 as rules no longer need replacing when being modified.
    - DEPRECATED in 2.4 and will be removed in 2.9.
    type: bool
    default: 'no'
'''

EXAMPLES = r'''
- name: Firewall rule to allow SMTP on TCP port 25
  win_firewall_rule:
    name: SMTP
    localport: 25
    action: allow
    direction: in
    protocol: tcp
    state: present
    enabled: yes

- name: Firewall rule to allow RDP on TCP port 3389
  win_firewall_rule:
    name: Remote Desktop
    localport: 3389
    action: allow
    direction: in
    protocol: tcp
    profiles: private
    state: present
    enabled: yes
'''
