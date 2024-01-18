# -*- coding: utf-8 -*-

# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Ansible Core Team (@ansible)
module: include_tasks
short_description: Dynamically include a task list
description:
  - Includes a file with a list of tasks to be executed in the current playbook.
version_added: '2.4'
options:
  file:
    description:
      - Specifies the name of the file that lists tasks to add to the current playbook.
    type: str
    version_added: '2.7'
  apply:
    description:
      - Accepts a hash of task keywords (e.g. C(tags), C(become)) that will be applied to the tasks within the include.
    type: str
    version_added: '2.7'
  free-form:
    description:
      - |
        Specifies the name of the imported file directly without any other option C(- include_tasks: file.yml).
      - Is the equivalent of specifying an argument for the I(file) parameter.
      - Most keywords, including loop, with_items, and conditionals, apply to this statement unlike M(ansible.builtin.import_tasks).
      - The do-until loop is not supported.
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
    - action_core
    - action_core.include
attributes:
    check_mode:
        support: none
    diff_mode:
        support: none
seealso:
- module: ansible.builtin.import_playbook
- module: ansible.builtin.import_role
- module: ansible.builtin.import_tasks
- module: ansible.builtin.include_role
- ref: playbooks_reuse
  description: More information related to including and importing playbooks, roles and tasks.
'''

EXAMPLES = r'''
- hosts: all
  tasks:
    - ansible.builtin.debug:
        msg: task1

    - name: Include task list in play
      ansible.builtin.include_tasks:
        file: stuff.yaml

    - ansible.builtin.debug:
        msg: task10

- hosts: all
  tasks:
    - ansible.builtin.debug:
        msg: task1

    - name: Include task list in play only if the condition is true
      ansible.builtin.include_tasks: "{{ hostvar }}.yaml"
      when: hostvar is defined

- name: Apply tags to tasks within included file
  ansible.builtin.include_tasks:
    file: install.yml
    apply:
      tags:
        - install
  tags:
    - always

- name: Apply tags to tasks within included file when using free-form
  ansible.builtin.include_tasks: install.yml
  args:
    apply:
      tags:
        - install
  tags:
    - always
'''

RETURN = r'''
# This module does not return anything except tasks to execute.
'''
