#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['deprecated'],
    'supported_by': 'core'
}


DOCUMENTATION = '''
---
author: Ansible Core Team (@ansible)
module: include
short_description: Include a play or task list
description:
  - Includes a file with a list of plays or tasks to be executed in the current playbook.
  - Files with a list of plays can only be included at the top level. Lists of tasks can only be included where tasks
    normally run (in play).
  - Before Ansible version 2.0, all includes were 'static' and were executed when the play was compiled.
  - Static includes are not subject to most directives. For example, loops or conditionals are applied instead to each
    inherited task.
  - Since Ansible 2.0, task includes are dynamic and behave more like real tasks. This means they can be looped,
    skipped and use variables from any source. Ansible tries to auto detect this, but you can use the `static`
    directive (which was added in Ansible 2.1) to bypass autodetection.
  - This module is also supported for Windows targets.
version_added: "0.6"
options:
  free-form:
    description:
      - This module allows you to specify the name of the file directly without any other options.
notes:
  - This is a core feature of Ansible, rather than a module, and cannot be overridden like a module.
  - Include has some unintuitive behaviours depending on if it is running in a static or dynamic in play or in playbook context,
    in an effort to clarify behaviours we are moving to a new set modules (M(include_tasks), M(include_role), M(import_playbook), M(import_tasks))
    that have well established and clear behaviours.
    This module will still be supported for some time but we are looking at deprecating it in the near future.
'''

EXAMPLES = """
- hosts: localhost
  tasks:
    - debug:
        msg: play1

- name: Include a play after another play
  include: otherplays.yaml


- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Include task list in play
      include: stuff.yaml

    - debug:
        msg: task10

- hosts: all
  tasks:
    - debug:
        msg: task1

    - name: Include task list in play only if the condition is true
      include: "{{ hostvar }}.yaml"
      static: no
      when: hostvar is defined
"""

RETURN = """
# This module does not return anything except plays or tasks to execute.
"""
