#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
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

DOCUMENTATION = '''
---
module: win_timezone
version_added: "2.1"
short_description: Sets Windows machine timezone
description:
    - Sets machine time to the specified timezone, the module will check if the provided timezone is supported on the machine.
options:
  timezone:
    description:
      - Timezone to set to.  Example Central Standard Time
    required: true
    default: null
    aliases: []

author: Phil Schwartz
'''


EXAMPLES = '''
  # Set machine's timezone to Central Standard Time
  win_timezone:
    timezone: "Central Standard Time"
'''

RETURN = '''# '''
