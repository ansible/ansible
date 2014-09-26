#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013 Dag Wieers <dag@wieers.com>
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

DOCUMENTATION = '''
---
author: Dag Wieers
module: set_fact
short_description: Set host facts from a task
description:
     - This module allows setting new variables.  Variables are set on a host-by-host basis
       just like facts discovered by the setup module.
     - These variables will survive between plays.
options:
  key_value:
    description:
      - The C(set_fact) module takes key=value pairs as variables to set
        in the playbook scope. Or alternatively, accepts complex arguments
        using the C(args:) statement.
    required: true
    default: null
version_added: "1.2"
'''

EXAMPLES = '''
# Example setting host facts using key=value pairs
- set_fact: one_fact="something" other_fact="{{ local_var * 2 }}"

# Example setting host facts using complex arguments
- set_fact:
     one_fact: something
     other_fact: "{{ local_var * 2 }}"

# As of 1.8, Ansible will convert boolean strings ('true', 'false', 'yes', 'no')
# to proper boolean values when using the key=value syntax, however it is still
# recommended that booleans be set using the complex argument style:
- set_fact:
    one_fact: true
    other_fact: false

'''
