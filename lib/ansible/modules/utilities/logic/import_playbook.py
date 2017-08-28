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
module: import_playbook
short_description: import a playbook.
description:
     - Includes a file with a list of plays to be executed.
     - Files with a list of plays can only be included at the top level, you cannot use this action inside a Play.
version_added: "2.4"
options:
  free-form:
    description:
        - This action allows you to specify the name of the file directly w/o any other options.
notes:
    - This is really not a module, this is a feature of the Ansible Engine, as such it cannot be overridden the same way a module can.
'''

EXAMPLES = """
- name: include a play after another play
  hosts: localhost
  tasks:
    - debug:
        msg: "play1"

- import_playbook: otherplays.yml


- name: This DOES NOT WORK
  hosts: all
  tasks:
    - debug:
        msg: task1

    - name: This failes because I'm inside a play already
      import_playbook: stuff.yml
"""

RETURN = """
# this module does not return anything except plays to execute
"""
