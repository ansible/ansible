#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright:  Ansible Project
# Copyright:  Estelle Poulin <dev@inspiredby.es>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Estelle Poulin (@estheruary)
module: do
short_description: Dynamically include a task block
description:
  - Includes a block with a list of tasks to be executed in the current playbook.
version_added: '2.11'
options:
  apply:
    description:
      - Accepts a hash of task keywords (e.g. C(tags), C(become)) that will be applied to the tasks within the include.
    type: str
  free-form:
    description:
      - |
        Accepts a list of tasks specificed in the same manner as C(block).
notes:
  - This is a core feature of the Ansible, rather than a module, and cannot be overridden like a module.
seealso:
- module: ansible.builtin.include
- module: ansible.builtin.include_tasks
- ref: playbooks_reuse_includes
  description: More information related to including and importing playbooks, roles and tasks.
'''

EXAMPLES = r'''
- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Run a task list within a play.
      do:
        - debug:
            msg: stuff

    - debug:
        msg: task10

- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Run the task list only if the condition is true.
      do:
        - debug:
            msg: stuff
      when: hostvar is defined

- name: Apply tags to tasks within included file
  do:
    - debug:
        msg: stuff
  args:
    apply:
      tags: [install]
  tags: [always]

- name: Loop over a block of tasks.
  do:
    - debug:
       var: item
  loop: [1, 2, 3]

'''

RETURN = r'''
# This module does not return anything except tasks to execute.
'''
