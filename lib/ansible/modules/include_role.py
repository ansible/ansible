# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
author: Ansible Core Team (@ansible)
module: include_role
short_description: Load and execute a role
description:
  - Dynamically loads and executes a specified role as a task.
  - May be used only where Ansible tasks are allowed - inside C(pre_tasks), C(tasks), or C(post_tasks) play objects, or as a task inside a role.
  - Task-level keywords, loops, and conditionals apply only to the C(include_role) statement itself.
  - To apply keywords to the tasks within the role, pass them using the O(apply) option or use M(ansible.builtin.import_role) instead.
  - Ignores some keywords, like C(until) and C(retries).
  - This module is also supported for Windows targets.
  - Does not work in handlers.
version_added: "2.2"
options:
  apply:
    description:
      - Accepts a hash of task keywords (for example C(tags), C(become)) that will be applied to all tasks within the included role.
    version_added: '2.7'
  name:
    description:
      - The name of the role to be executed.
    type: str
    required: True
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
  public:
    description:
      - This option dictates whether the role's C(vars) and C(defaults) are exposed to the play. If set to V(true)
        the variables will be available to tasks following the C(include_role) task. This functionality differs from
        standard variable exposure for roles listed under the C(roles) header or M(ansible.builtin.import_role) as they are exposed
        to the play at playbook parsing time, and available to earlier roles and tasks as well.
    type: bool
    default: no
    version_added: '2.7'
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
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
    - action_core
    - action_core.include
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
notes:
  - Handlers and are made available to the whole play.
  - After Ansible 2.4, you can use M(ansible.builtin.import_role) for B(static) behaviour and this action for B(dynamic) one.
seealso:
- module: ansible.builtin.import_playbook
- module: ansible.builtin.import_role
- module: ansible.builtin.import_tasks
- module: ansible.builtin.include_tasks
- ref: playbooks_reuse
  description: More information related to including and importing playbooks, roles and tasks.
"""

EXAMPLES = r"""
- ansible.builtin.include_role:
    name: myrole

- name: Run tasks/other.yaml instead of 'main'
  ansible.builtin.include_role:
    name: myrole
    tasks_from: other

- name: Pass variables to role
  ansible.builtin.include_role:
    name: myrole
  vars:
    rolevar1: value from task

- name: Use role in loop
  ansible.builtin.include_role:
    name: '{{ roleinputvar }}'
  loop:
    - '{{ roleinput1 }}'
    - '{{ roleinput2 }}'
  loop_control:
    loop_var: roleinputvar

- name: Conditional role
  ansible.builtin.include_role:
    name: myrole
  when: not idontwanttorun

- name: Apply tags to tasks within included file
  ansible.builtin.include_role:
    name: install
    apply:
      tags:
        - install
  tags:
    - always
"""

RETURN = r"""
# This module does not return anything except tasks to execute.
"""
