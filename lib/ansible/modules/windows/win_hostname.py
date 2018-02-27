#!/usr/bin/python
# -*- coding: utf-8 -*-

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

# Copyright: (c) 2018, Ripon Banik (@riponbanik)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: win_hostname
version_added: "2.6"
short_description: Manages local Windows computer name
description:
     - Manages local Windows computer name. 
     - A reboot is required for the computer name to take effect.
options:
  name:
    description:
      - Name of the computer.
    required: true    
  author: Ripon Banik (@riponbanik)
'''

EXAMPLES = '''
- name: Change hostname with the new name
  win_hostname: 
    name: myhost
'''

