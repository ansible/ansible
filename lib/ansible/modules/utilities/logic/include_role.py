#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
author:
    - "Ansible Core Team (@ansible)"
module: include_role
short_description: Load and execute a role
description:
     - Loads and executes a role as a task, this frees roles from the `role:` directive and allows them to be treated more as tasks.
     - This module is also supported for Windows targets.
version_added: "2.2"
options:
  name:
    description:
      - The name of the role to be executed.
    required: True
  tasks_from:
    description:
      - "File to load from a Role's tasks/ directory."
    required: False
    default: 'main'
  vars_from:
    description:
      - "File to load from a Role's vars/ directory."
    required: False
    default: 'main'
  defaults_from:
    description:
      - "File to load from a Role's defaults/ directory."
    required: False
    default: 'main'
  allow_duplicates:
    description:
      - Overrides the role's metadata setting to allow using a role more than once with the same parameters.
    required: False
    default: True
  private:
    description:
      - If True the variables from defaults/ and vars/ in a role will not be made available to the rest of the play.
    default: None
notes:
    - Handlers are made available to the whole play.
    - simple dependencies seem to work fine.
    - As with C(include) this task can be static or dynamic, If static it implies that it won't need templating nor loops nor conditionals and will
      show included tasks in the --list options. Ansible will try to autodetect what is needed, but you can set `static` to `yes` or `no` at task
      level to control this.
    - This module is also supported for Windows targets.
'''

EXAMPLES = """
- include_role:
    name: myrole

- name: Run tasks/other.yml instead of 'main'
  include_role:
    name: myrole
    tasks_from: other

- name: Pass variables to role
  include_role:
    name: myrole
  vars:
    rolevar1: 'value from task'

- name: Use role in loop
  include_role:
    name: myrole
  with_items:
    - '{{ roleinput1 }}'
    - '{{ roleinput2 }}'
  loop_control:
    loop_var: roleinputvar

- name: conditional role
  include_role:
    name: myrole
  when: not idontwanttorun
"""

RETURN = """
# this module does not return anything except tasks to execute
"""
