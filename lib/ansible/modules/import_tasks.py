# -*- coding: utf-8 -*-

# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Ansible Core Team (@ansible)
module: import_tasks
short_description: Import a task list
description:
  - Imports a list of tasks to be added to the current playbook for subsequent execution.
version_added: "2.4"
options:
  free-form:
    description:
      - |
        Specifies the name of the imported file directly without any other option C(- import_tasks: file.yml).
      - Most keywords, including loops and conditionals, only apply to the imported tasks, not to this statement itself.
      - If you need any of those to apply, use M(ansible.builtin.include_tasks) instead.
  file:
    description:
      - Specifies the name of the file that lists tasks to add to the current playbook.
    type: str
    version_added: '2.7'
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
    - action_core
    - action_core.import
attributes:
    check_mode:
      support: none
    diff_mode:
      support: none
notes:
  - This is a core feature of Ansible, rather than a module, and cannot be overridden like a module
seealso:
- module: ansible.builtin.import_playbook
- module: ansible.builtin.import_role
- module: ansible.builtin.include_role
- module: ansible.builtin.include_tasks
- ref: playbooks_reuse_includes
  description: More information related to including and importing playbooks, roles and tasks.
'''

EXAMPLES = r'''
- hosts: all
  tasks:
    - ansible.builtin.debug:
        msg: task1

    - name: Include task list in play
      ansible.builtin.import_tasks:
        file: stuff.yaml

    - ansible.builtin.debug:
        msg: task10

- hosts: all
  tasks:
    - ansible.builtin.debug:
        msg: task1

    - name: Apply conditional to all imported tasks
      ansible.builtin.import_tasks: stuff.yaml
      when: hostvar is defined
'''

RETURN = r'''
# This module does not return anything except tasks to execute.
'''
