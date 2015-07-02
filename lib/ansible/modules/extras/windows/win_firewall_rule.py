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

DOCUMENTATION = '''
---
module: win_fw
version_added: "2.0"
author: Timothy Vandenbrande
short_description: Windows firewall automation
description:
    - allows you to create/remove/update firewall rules
options: 
    state:
        description:
            - create/remove/update or powermanage your VM
        default: "present"
        required: true
        choices: ['present', 'absent']
    name:
        description:
            - the rules name
        default: null
        required: true
    direction:
        description:
            - is this rule for inbound or outbound trafic
        default: null
        required: true
        choices: [ 'In', 'Out' ]
    action:
        description:
            - what to do with the items this rule is for
        default: null
        required: true
        choices: [ 'allow', 'block' ]
    description:
        description:
            - description for the firewall rule
        default: null
        required: false
    localip:
        description:
            - the local ip address this rule applies to
        default: null
        required: false
    remoteip:
        description:
            - the remote ip address/range this rule applies to
        default: null
        required: false
    localport:
        description:
            - the local port this rule applies to
        default: null
        required: false
    remoteport:
        description:
            - the remote port this rule applies to
        default: null
        required: false
    program:
        description:
            - the program this rule applies to
        default: null
        required: false
    service:
        description:
            - the service this rule applies to
        default: null
        required: false
    protocol:
        description:
            - the protocol this rule applies to
        default: null
        required: false
    profile:
        describtion:
            - the profile this rule applies to
        default: current
        choices: ['current', 'domain', 'standard', 'all']
    force:
        description:
            - Enforces the change if a rule with different values exists
        default: false
        required: false
    

'''

EXAMPLES = '''
# create smtp firewall rule
  action: win_fw
  args:
      name: smtp
      state: present
      localport: 25
      action: allow
      protocol: TCP

'''
