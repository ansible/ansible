#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Iago Garrido <iago086@gmail.com>
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

DOCUMENTATION = """
---
module: win_hosts
version_added: "2.3"
short_description: Manages hosts file.
description:
    - Manages hosts file in a windows machine
options:
  ip:
    description:
      - IP address to add to hosts file.
    required: true
  hostname:
    description:
      - Host name to add to the hosts file.
    required: true
  comment:
    description:
      - Comment to add to the line in the hosts file.
    defaults: null
    required: false
  state:
    description:
      - If hostname resolution must be present or not.
    choices:
      - present
      - absent
    required: true
author: Iago Garrido (@iagogarrido)
notes:
    - Part of this code is based on code from this repo (https://github.com/jeremy-jameson/Toolbox)
    - Tested on Windows Server 2k12 R2
"""

EXAMPLES = """
# Sample hosts modification
---
- name: Adds host name resolution
  win_hosts:
    ip: "8.8.8.8"
    hostname: "defaultdns"
    state: present

---
- name: Removes host name resolution for the specified IP
  win_hosts:
    ip: "192.0.2.100"
    hostname: "webnode1"
    state: absent
"""

RETURN = """
exception:
    description: Output exception message.
    returned: error
    type: string
    sample: No hosts file found
changed:
    description: Whether or not any changes were made.
    returned: always
    type: bool
    sample: False
"""
