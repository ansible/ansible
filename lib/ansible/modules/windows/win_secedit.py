#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016, Red Hat Inc  
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_secedit
version_added: "2.3"
notes:
    - If the target server is joined to a DC then it will error as any secedit modifications would be overwritten by GPO.
    - SecEdit does not error out when you try to modify a key/value with an improper value, such as passing in a string when a valid value would be an integer. 
    - Therefore, this module will attempt to configure secedit with any value supplied, then it does a second dump of secedit to see if the requested change persisted, if it didn't then it errors out, otherwise it continues as normal.
short_description: Manipulate local security policies via secedit
description:
    - Modifies key-values for local security policies via secedit 
options:
  category:
    description:
      - The category you wish to modify a value under. This can things like 'System Access', 'Event Audit', etc. If you supply an invalid category the module will error out and let you know what the valid categories are for that particular system. 
    required: true
  key:
    description:
        - The key under the category for which you wish to modify the value. For example: under the System Access category there is a key 'MinimumPasswordAge' that could be targeted. 
        - Just like with category, if an invalid key is specified, the module will error out and show what the valid keys for the given category are.
    required: true
  value:
    description:
      - The value to assign to the key. 
    required: true
author: Jonathan Davila (@defionscode) 
'''

EXAMPLES = '''
  # Set the local security policy so that the maximum password age is 30 
  - name: Set max pwd age to 30 days 
    win_secedit:
      category: System Access
      key: MaximumPasswordAge
      value: 30 

  # Configure local policy to audit system events 
  - name: Ensure system events are audited 
    win_secedit:
      category: Event Audit 
      key: AuditSystemEvents 
      value: 1 
'''

RETURN = '''
msg:
    description: whether the key was set or updated 
    returned: success or changed
    type: string 
    sample: Key updated 

category:
    description: the category targeted 
    returned: success or changed
    type: string
    sample: Event Audit 

key:
    description: the key within the category targeted 
    returned: success or changed
    type: string
    sample: AuditAccountLogon 

value:
    description: the value of the key 
    returned: success or changed
    type: string
    sample: 1 
'''
