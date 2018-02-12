#!/usr/bin/python
# -*- coding: utf-8 -*-

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_hostname
version_added: "2.4"
short_description: Manages local Windows computer name
description:
     - Manages local Windows computer name. 
     - A reboot is required for the computer name to take effect
options:
  name:
    description:
      - Name of the computer
    required: true
    default: null
    aliases: []
author: Ripon Banik
'''

EXAMPLES = '''
# Ad-hoc example
ansible -i hosts -m win_host -a "host_name=host ip_address=ip" windows
# Playbook example
- win_hostname: name=myhost
'''

