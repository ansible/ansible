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
module: import_role
short_description: Import a role into a play
description:
  - Much like the `roles:` keyword, this task loads a role, but it allows you to control it when the role tasks run in
    between other tasks of the play.
  - Most keywords, loops and conditionals will only be applied to the imported tasks, not to this statement itself. If
    you want the opposite behavior, use M(include_role) instead. To better understand the difference you can read
    the L(Including and Importing Guide,../user_guide/playbooks_reuse_includes.html).
version_added: "2.4"
options:
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
'''

EXAMPLES = """
- hosts: all
  tasks:
    - import_role:
        name: myrole

    - name: Run tasks/other.yaml instead of 'main'
      import_role:
        name: myrole
        tasks_from: other

    - name: Pass variables to role
      import_role:
        name: myrole
      vars:
        rolevar1: value from task

    - name: Apply condition to each task in role
      import_role:
        name: myrole
      when: not idontwanttorun
"""

RETURN = """
# This module does not return anything except tasks to execute.
"""
