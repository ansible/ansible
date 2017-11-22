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
module: import_playbook
short_description: Import a playbook
description:
  - Includes a file with a list of plays to be executed.
  - Files with a list of plays can only be included at the top level. You cannot use this action inside a play.
version_added: "2.4"
options:
  free-form:
    description:
      - The name of the imported playbook is specified directly without any other option.
notes:
  - This is a core feature of Ansible, rather than a module, and cannot be overridden like a module.
'''

EXAMPLES = """
- hosts: localhost
  tasks:
    - debug:
        msg: play1

- name: Include a play after another play
  import_playbook: otherplays.yaml


- name: This DOES NOT WORK
  hosts: all
  tasks:
    - debug:
        msg: task1

    - name: This fails because I'm inside a play already
      import_playbook: stuff.yaml
"""

RETURN = """
# This module does not return anything except plays to execute.
"""
