#!/usr/bin/env python

# (c) 2014, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_firewall_rule
version_added: "2.0"
author: Timothy Vandenbrande
short_description: Windows firewall automation
description:
    - allows you to create/remove/update firewall rules
options:
    enabled:
        description:
            - is this firewall rule enabled or disabled
        default: 'yes'
        choices: [ 'no', 'yes' ]
        aliases: [ 'enable' ]
    state:
        description:
            - should this rule be added or removed
        default: "present"
        choices: ['present', 'absent']
    name:
        description:
            - the rules name
        required: true
    direction:
        description:
            - is this rule for inbound or outbound traffic
        required: true
        choices: ['in', 'out']
    action:
        description:
            - what to do with the items this rule is for
        required: true
        choices: ['allow', 'block', 'bypass']
    description:
        description:
            - description for the firewall rule
    localip:
        description:
            - the local ip address this rule applies to
        default: 'any'
    remoteip:
        description:
            - the remote ip address/range this rule applies to
        default: 'any'
    localport:
        description:
            - the local port this rule applies to
        default: 'any'
    remoteport:
        description:
            - the remote port this rule applies to
        default: 'any'
    program:
        description:
            - the program this rule applies to
    service:
        description:
            - the service this rule applies to
        default: 'any'
    protocol:
        description:
            - the protocol this rule applies to
        default: 'any'
    profiles:
        description:
            - the profile this rule applies to, e.g. Domain,Private,Public
        default: 'any'
        aliases: [ 'profile' ]
    force:
        description:
            - Enforces the change if a rule with different values exists
        default: 'no'
        choices: [ 'no', 'yes' ]
'''

EXAMPLES = r'''
- name: Firewall rule to allow SMTP on TCP port 25
  win_firewall_rule:
    name: smtp
    localport: 25
    action: allow
    direction: in
    protocol: TCP
    state: present
    enabled: yes

- name: Firewall rule to allow RDP on TCP port 3389
  win_firewall_rule:
    name: Remote Desktop
    localport: 3389
    action: allow
    direction: in
    protocol: TCP
    profiles: private
    state: present
    enabled: yes
'''
