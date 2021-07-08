#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: set_vars
short_description: set a variable to a value at a given scope
description:
     - This module allows setting variables in the current ansible run at different scopesA
     - If a variable already exists it will be overriden or merged depending on 'hash behaviour'
       otherwise it will be created
author: Ansible Project
options:
  defs:
    description:
      - A list of dictionaries that represent a variable definition
    type: list
    required: true
  scope:
    required: false
    choices: ['host', 'host_fact', 'extra', 'play']
    description:
        - scope to which variables apply to, this sets the default for every definition but each one can override it
    type: string
    default: 'host'
version_added: "2.12"
'''

EXAMPLES = r'''
- name: create/update an extra var
  set_vars:
    scope: extra
    defs:
      - name: packages_to_install
        value:
            - apache
            - nginx
            - haproxy
            - pound

- name: set a host fact (not the same as set_facts + cacheable=true, only 1 var is created)
  set_vars:
    defs:
      - name: pretty
        value: no
        scope: host_fact

- name: set a host variable (higher priority than facts), this is equivalent of set_fact + cacheable=false
  set_vars:
    defs:
      - name: presents
        value: all
        scope: host
'''

RETURNS = r'''
# should i return list of var names + scope set?
'''
