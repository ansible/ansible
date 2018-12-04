#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright:  Ansible Project
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
module: include_tasks
short_description: Dynamically include a task list
description:
  - Includes a file with a list of tasks to be executed in the current playbook.
version_added: "2.4"
options:
  file:
    description:
      - The name of the imported file is specified directly without any other option.
      - Unlike M(import_tasks), most keywords, including loops and conditionals, apply to this statement.
    version_added: '2.7'
  apply:
    description:
      - Accepts a hash of task keywords (e.g. C(tags), C(become)) that will be applied to the tasks within the include.
    version_added: '2.7'
  free-form:
    description:
      - |
        Supplying a file name via free-form C(- include_tasks: file.yml) of a file to be included is the equivalent
        of specifying an argument of I(file).
notes:
  - This is a core feature of the Ansible, rather than a module, and cannot be overridden like a module.
'''

EXAMPLES = """
- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Include task list in play
      include_tasks: stuff.yaml

    - debug:
        msg: task10

- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Include task list in play only if the condition is true
      include_tasks: "{{ hostvar }}.yaml"
      when: hostvar is defined

- name: Apply tags to tasks within included file
  include_tasks:
    file: install.yml
    apply:
      tags:
        - install
  tags:
    - always

- name: Apply tags to tasks within included file when using free-form
  include_tasks: install.yml
  args:
    apply:
      tags:
        - install
  tags:
    - always
"""

RETURN = """
# This module does not return anything except tasks to execute.
"""
