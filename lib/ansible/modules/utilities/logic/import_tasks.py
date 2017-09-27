#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
author:
    - "Ansible Core Team (@ansible)"
module: import_tasks
short_description: import a task list.
description:
     - Imports a list of tasks to be added to the current playbook for subsequent execution.
version_added: "2.4"
options:
  free-form:
    description:
        - This action allows you to specify the name of the file directly w/o any other options.
        - Any loops, conditionals and most other keywords will be applied to the included tasks, not to this statement itself.
        - If you need any of those to apply to this action, use M(include_tasks) instead.
notes:
    - This is really not a module, this is a feature of the Ansible Engine, as such it cannot be overridden the same way a module can.
'''

EXAMPLES = """
# include task list in play
- hosts: all
  tasks:
    - debug:
        msg: task1

    - import_tasks: stuff.yml

    - debug:
        msg: task10

# apply conditional to all imported tasks
- hosts: all
  tasks:
    - debug:
        msg: task1

    - import_tasks: stuff.yml
      when: hostvar is defined
"""

RETURN = """
# this module does not return anything except tasks to execute
"""
