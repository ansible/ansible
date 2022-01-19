#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: set_fact
short_description: Set host variable(s) and fact(s).
version_added: "1.2"
description:
    - This action allows setting variables associated to the current host.
    - These variables will be available to subsequent plays during an ansible-playbook run via the host they were set on.
    - Set C(cacheable) to C(yes) to save variables across executions using a fact cache.
      Variables will keep the set_fact precedence for the current run, but will used 'cached fact' precedence for subsequent ones.
    - Per the standard Ansible variable precedence rules, other types of variables have a higher priority, so this value may be overridden.
options:
  key_value:
    description:
      - "The C(set_fact) module takes C(key=value) pairs or C(key: value) (YAML notation) as variables to set in the playbook scope.
        The 'key' is the resulting variable name and the value is, of course, the value of said variable."
      - You can create multiple variables at once, by supplying multiple pairs, but do NOT mix notations.
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
    - Because of the nature of tasks, set_fact will produce 'static' values for a variable.
      Unlike normal 'lazy' variables, the value gets evaluated and templated on assignment.
    - Some boolean values (yes, no, true, false) will always be converted to boolean type,
      unless C(DEFAULT_JINJA2_NATIVE) is enabled.  This is done so the C(var=value) booleans,
      otherwise it would only be able to create strings, but it also prevents using those values to create YAML strings.
      Using the setting will restrict k=v to strings, but will allow you to specify string or boolean in YAML.
    - "To create lists/arrays or dictionary/hashes use YAML notation C(var: [val1, val2])."
    - Since 'cacheable' is now a module param, 'cacheable' is no longer a valid fact name.
    - This action does not use a connection and always executes on the controller.
seealso:
- module: ansible.builtin.include_vars
- ref: ansible_variable_precedence
  description: More information related to variable precedence and which type of variable wins over others.
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Setting host facts using key=value pairs, this format can only create strings or booleans
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

- name: Creating list and dictionary variables
  set_fact:
    one_dict:
        something: here
        other: there
    one_list:
        - a
        - b
        - c

- name: Creating list and dictionary variables using 'shorthand' YAML
  set_fact:
    two_dict: {'something': here2, 'other': somewhere}
    two_list: [1,2,3]
'''
