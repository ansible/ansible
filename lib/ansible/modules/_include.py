# -*- coding: utf-8 -*-

# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Ansible Core Team (@ansible)
module: include
short_description: Include a task list
description:
  - Includes a file with a list of tasks to be executed in the current playbook.
  - Lists of tasks can only be included where tasks
    normally run (in play).
  - Before Ansible 2.0, all includes were 'static' and were executed when the play was compiled.
  - Static includes are not subject to most directives. For example, loops or conditionals are applied instead to each
    inherited task.
  - Since Ansible 2.0, task includes are dynamic and behave more like real tasks. This means they can be looped,
    skipped and use variables from any source. Ansible tries to auto detect this, but you can use the C(static)
    directive (which was added in Ansible 2.1) to bypass autodetection.
  - This module is also supported for Windows targets.
version_added: "0.6"
deprecated:
    why: it has too many conflicting behaviours depending on keyword combinations and it was unclear how it should behave in each case.
        new actions were developed that were specific about each case and related behaviours.
    alternative: include_tasks, import_tasks, import_playbook
    removed_in: "2.16"
    removed_from_collection: 'ansible.builtin'
options:
  free-form:
    description:
      - This module allows you to specify the name of the file directly without any other options.
notes:
  - This is a core feature of Ansible, rather than a module, and cannot be overridden like a module.
  - Include has some unintuitive behaviours depending on if it is running in a static or dynamic in play or in playbook context,
    in an effort to clarify behaviours we are moving to a new set modules (M(ansible.builtin.include_tasks),
    M(ansible.builtin.include_role), M(ansible.builtin.import_playbook), M(ansible.builtin.import_tasks))
    that have well established and clear behaviours.
  - This module no longer supporst including plays. Use M(ansible.builtin.import_playbook) instead.
seealso:
- module: ansible.builtin.import_playbook
- module: ansible.builtin.import_role
- module: ansible.builtin.import_tasks
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
      ansible.builtin.include: stuff.yaml

    - ansible.builtin.debug:
        msg: task10

- hosts: all
  tasks:
    - ansible.builtin.debug:
        msg: task1

    - name: Include task list in play only if the condition is true
      ansible.builtin.include: "{{ hostvar }}.yaml"
      static: no
      when: hostvar is defined
'''

RETURN = r'''
# This module does not return anything except tasks to execute.
'''
