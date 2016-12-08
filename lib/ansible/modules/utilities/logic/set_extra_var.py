#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016 Pieter Voet <pietervoet@nl.ibm.com>
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
author: "Pieter Voet (pietervoet@nl.ibm.com)"
module: set_extra_var
short_description: Sets an extra variable from a playbook.
description:
     - This module allows setting new variables.  Variables are set on a global basis
     - These variables will survive between plays during an Ansible run, even for different host groups 
options:
  key_value:
    description:
      - The C(set_extra_var) module takes name=var_name value=var_value pairs as variables to set
        in the playbook scope. Or alternatively, accepts complex arguments
        using the C(args:) statement.
    required: true
    default: null
version_added: "1.2"
'''

EXAMPLES = '''
# Example setting host facts using key=value pairs
- set_extra_var: name="my_var" value="my_value"
# Example setting host facts using other variables
- set_extra_var:
     name: my_var
     value: "{{ local_var * 2 }}"
     
# Example inventory : 
  group_all = { host_1, host_2, host_3 }
  group_one = { host_1 }
  group_two = { host_2, host3 }
  
# Example playbook
---
- hosts: group_one
  tasks:
  - name: list /tmp
    shell: ls /tmp
    register: out
  - name: set global variable
    set_extra_var: name=myvar value="{{out}}"
- hosts: group_two
  tasks:
  - debug: msg="{{myvar}}"
# Example command 
ansible-playbook  my_playbook.yml --limit group_all
'''
