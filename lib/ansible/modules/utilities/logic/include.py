#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright:  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
author:
    - "Ansible Core Team (@ansible)"
module: include
short_description: include a play or task list.
description:
     - Includes a file with a list of plays or tasks to be executed in the current playbook.
     - Files with a list of plays can only be included at the top level, lists of tasks can only be included where tasks normally run (in play).
     - Before 2.0 all includes were 'static', executed at play compile time.
     - Static includes are not subject to most directives, for example, loops or conditionals, they are applied instead to each inherited task.
     - Since 2.0 task includes are dynamic and behave more like real tasks.  This means they can be looped, skipped and use variables from any source.
       Ansible tries to auto detect this, use the `static` directive (new in 2.1) to bypass autodetection.
     - This module is also supported for Windows targets.
version_added: "0.6"
options:
  free-form:
    description:
        - This module allows you to specify the name of the file directly w/o any other options.
notes:
    - This is really not a module, though it appears as such, this is a feature of the Ansible Engine, as such it cannot be overridden the same way a
      module can.
    - This module is also supported for Windows targets.
'''

EXAMPLES = """
# include a play after another play
- hosts: localhost
  tasks:
    - debug:
        msg: "play1"

- include: otherplays.yml


# include task list in play
- hosts: all
  tasks:
    - debug:
        msg: task1

    - include: stuff.yml

    - debug:
        msg: task10

# dyanmic include task list in play
- hosts: all
  tasks:
    - debug:
        msg: task1

    - include: "{{ hostvar }}.yml"
      static: no
      when: hostvar is defined
"""

RETURN = """
# this module does not return anything except plays or tasks to execute
"""
