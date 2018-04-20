#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
author:
- Dag Wieers (@dagwieers)
module: set_fact
short_description: Set host facts from a task
description:
    - This module allows setting new variables.  Variables are set on a host-by-host basis just like facts discovered by the setup module.
    - These variables will be available to subsequent plays during an ansible-playbook run, but will not be saved across executions even if you use
      a fact cache.
    - Per the standard Ansible variable precedence rules, many other types of variables have a higher priority, so this value may be overridden.
      See L(Variable Precedence Guide,../user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) for more information.
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
      - This boolean indicates if the facts set will also be added to the
        fact cache, if fact caching is enabled.
    type: bool
    default: 'no'
    version_added: "2.4"
version_added: "1.2"
notes:
    - "The `var=value` notation can only create strings or booleans.
      If you want to create lists/arrays or dictionary/hashes use `var: [val1, val2]`"
    - This module is also supported for Windows targets.
    - Since 'cacheable' is now a module param, 'cacheable' is no longer a valid fact name as of 2.4.
'''

EXAMPLES = '''
# Example setting host facts using key=value pairs, note that this always creates strings or booleans
- set_fact: one_fact="something" other_fact="{{ local_var }}"

# Example setting host facts using complex arguments
- set_fact:
     one_fact: something
     other_fact: "{{ local_var * 2 }}"
     another_fact: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"

# Example setting facts so that they will be persisted in the fact cache
- set_fact:
    one_fact: something
    other_fact: "{{ local_var * 2 }}"
    cacheable: true

# As of 1.8, Ansible will convert boolean strings ('true', 'false', 'yes', 'no')
# to proper boolean values when using the key=value syntax, however it is still
# recommended that booleans be set using the complex argument style:
- set_fact:
    one_fact: true
    other_fact: false

'''
