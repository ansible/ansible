#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
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
module: debug
short_description: Print statements during execution
description:
     - This module prints statements during execution and can be useful
       for debugging variables or expressions without necessarily halting
       the playbook. Useful for debugging together with the 'when:' directive.

version_added: "0.8"
options:
  msg:
    description:
      - The customized message that is printed. If omitted, prints a generic
        message.
    required: false
    default: "Hello world!"
  var:
    description:
      - A variable name to debug.  Mutually exclusive with the 'msg' option.
author: Dag Wieers, Michael DeHaan
'''

EXAMPLES = '''
# Example that prints the loopback address and gateway for each host
- debug: msg="System {{ inventory_hostname }} has uuid {{ ansible_product_uuid }}"

- debug: msg="System {{ inventory_hostname }} has gateway {{ ansible_default_ipv4.gateway }}"
  when: ansible_default_ipv4.gateway is defined

- shell: /usr/bin/uptime
  register: result

- debug: var=result

- name: Display all variables/facts known for a host
  debug: var=hostvars[inventory_hostname]
'''
