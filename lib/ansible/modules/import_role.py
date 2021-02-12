#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Ansible Core Team (@ansible)
module: import_role
short_description: Import a role into a play
description:
  - Much like the C(roles:) keyword, this task loads a role, but it allows you to control when the role tasks run in
    between other tasks of the play.
  - Most keywords, loops and conditionals will only be applied to the imported tasks, not to this statement itself. If
    you want the opposite behavior, use M(ansible.builtin.include_role) instead.
  - Does not work in handlers.
version_added: '2.4'
options:
  name:
    description:
      - The name of the role to be executed.
    type: str
    required: true
  tasks_from:
    description:
      - File to load from a role's C(tasks/) directory.
    type: str
    default: main
  vars_from:
    description:
      - File to load from a role's C(vars/) directory.
    type: str
    default: main
  defaults_from:
    description:
      - File to load from a role's C(defaults/) directory.
    type: str
    default: main
  allow_duplicates:
    description:
      - Overrides the role's metadata setting to allow using a role more than once with the same parameters.
    type: bool
    default: yes
  handlers_from:
    description:
      - File to load from a role's C(handlers/) directory.
    type: str
    default: main
    version_added: '2.8'
  rolespec_validate:
    description:
      - Perform role argument spec validation if an argument spec is defined.
    type: bool
    default: yes
    version_added: '2.11'
notes:
  - Handlers are made available to the whole play.
  - Since Ansible 2.7 variables defined in C(vars) and C(defaults) for the role are exposed to the play at playbook parsing time.
    Due to this, these variables will be accessible to roles and tasks executed before the location of the
    M(ansible.builtin.import_role) task.
  - Unlike M(ansible.builtin.include_role) variable exposure is not configurable, and will always be exposed.
seealso:
- module: ansible.builtin.import_playbook
- module: ansible.builtin.import_tasks
- module: ansible.builtin.include_role
- module: ansible.builtin.include_tasks
- ref: playbooks_reuse_includes
  description: More information related to including and importing playbooks, roles and tasks.
'''

EXAMPLES = r'''
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
'''

RETURN = r'''
# This module does not return anything except tasks to execute.
'''
