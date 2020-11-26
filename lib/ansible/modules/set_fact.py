#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: set_fact
short_description: Set host facts from a task
version_added: "1.2"
description:
    - This module allows setting new variables.
    - Variables are set on a host-by-host basis just like facts discovered by the setup module.
    - These variables will be available to subsequent plays during an ansible-playbook run.
    - Set C(cacheable) to C(yes) to save variables across executions
      using a fact cache. Variables created with set_fact have different precedence depending on whether they are or are not cached.
    - Per the standard Ansible variable precedence rules, many other types of variables have a higher priority, so this value may be overridden.
    - This module is also supported for Windows targets.
options:
  key_value:
    description:
      - The C(set_fact) module takes key=value pairs as variables to set
        in the playbook scope. Or alternatively, accepts complex arguments
        using the C(args:) statement.
    required: true
  cacheable:
    description:
      - This boolean converts the variable into an actual 'fact' which will also be added to the fact cache, if fact caching is enabled.
      - Normally this module creates 'host level variables' and has much higher precedence, this option changes the nature and precedence
        (by 7 steps) of the variable created.
        U(https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable)
      - "This actually creates 2 copies of the variable, a normal 'set_fact' host variable with high precedence and
        a lower 'ansible_fact' one that is available for persistance via the facts cache plugin.
        This creates a possibly confusing interaction with C(meta: clear_facts) as it will remove the 'ansible_fact' but not the host variable."
    type: bool
    default: no
    version_added: "2.4"
notes:
    - "The C(var=value) notation can only create strings or booleans.
      If you want to create lists/arrays or dictionary/hashes use C(var: [val1, val2])."
    - Since 'cacheable' is now a module param, 'cacheable' is no longer a valid fact name as of Ansible 2.4.
    - This module is also supported for Windows targets.
seealso:
- module: ansible.builtin.include_vars
- ref: ansible_variable_precedence
  description: More information related to variable precedence and which type of variable wins over others.
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Setting host facts using key=value pairs, note that this always creates strings or booleans
  set_fact: one_fact="something" other_fact="{{ local_var }}"

- name: Setting host facts using complex arguments
  set_fact:
    one_fact: something
    other_fact: "{{ local_var * 2 }}"
    another_fact: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"

- name: Setting facts so that they will be persisted in the fact cache
  set_fact:
    one_fact: something
    other_fact: "{{ local_var * 2 }}"
    cacheable: yes

# As of Ansible 1.8, Ansible will convert boolean strings ('true', 'false', 'yes', 'no')
# to proper boolean values when using the key=value syntax, however it is still
# recommended that booleans be set using the complex argument style:
- name:  Setting booleans using complex argument style
  set_fact:
    one_fact: yes
    other_fact: no

'''
