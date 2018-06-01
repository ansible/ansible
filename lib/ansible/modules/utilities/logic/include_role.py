#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'core'
}


DOCUMENTATION = '''
---
author: Ansible Core Team (@ansible)
module: include_role
short_description: Load and execute a role
description:
  - Loads and executes a role as a task dynamically. This frees roles from the `roles:` directive and allows them to be
    treated more as tasks.
  - Unlike M(import_role), most keywords, including loops and conditionals, apply to this statement.
  - This module is also supported for Windows targets.
version_added: "2.2"
options:
  apply:
    description:
      - Accepts a hash of task keywords (e.g. C(tags), C(become)) that will be applied to the tasks within the include.
    version_added: '2.7'
  name:
    description:
      - The name of the role to be executed.
    required: True
  tasks_from:
    description:
      - File to load from a role's C(tasks/) directory.
    default: main
  vars_from:
    description:
      - File to load from a role's C(vars/) directory.
    default: main
  defaults_from:
    description:
      - File to load from a role's C(defaults/) directory.
    default: main
  allow_duplicates:
    description:
      - Overrides the role's metadata setting to allow using a role more than once with the same parameters.
    type: bool
    default: 'yes'
  private:
    description:
      - This option is a no op, and the functionality described in previous versions was not implemented. This
        option will be removed in Ansible v2.8.
    type: bool
    default: 'no'
notes:
  - Handlers are made available to the whole play.
  - Before Ansible 2.4, as with C(include), this task could be static or dynamic, If static, it implied that it won't
    need templating, loops or conditionals and will show included tasks in the `--list` options. Ansible would try to
    autodetect what is needed, but you can set `static` to `yes` or `no` at task level to control this.
  - After Ansible 2.4, you can use M(import_role) for 'static' behaviour and this action for 'dynamic' one.
'''

EXAMPLES = """
- include_role:
    name: myrole

- name: Run tasks/other.yaml instead of 'main'
  include_role:
    name: myrole
    tasks_from: other

- name: Pass variables to role
  include_role:
    name: myrole
  vars:
    rolevar1: value from task

- name: Use role in loop
  include_role:
    name: myrole
  with_items:
    - '{{ roleinput1 }}'
    - '{{ roleinput2 }}'
  loop_control:
    loop_var: roleinputvar

- name: Conditional role
  include_role:
    name: myrole
  when: not idontwanttorun

- name: Apply tags to tasks within included file
  include_role:
    name: install
    apply:
      tags:
        - install
  tags:
    - always
"""

RETURN = """
# This module does not return anything except tasks to execute.
"""
