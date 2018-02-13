#!/usr/bin/python
# -*- coding: utf-8 -*-

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

# Copyright: (c) 2018, Ripon Banik (@riponbanik)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: win_hostname
version_added: "2.4"
short_description: Manages local Windows computer name
description:
     - Manages local Windows computer name. 
     - A reboot is required for the computer name to take effect.
options:
  name:
    description:
      - Name of the computer
    required: true
    default: null
    aliases: []
  author: Ripon Banik (@riponbanik)
'''

EXAMPLES = '''
# Ad-hoc example
ansible -i hosts -m win_hostname -a "name=myhost" windows
# Playbook example
- win_hostname: 
    name: myhost
'''

