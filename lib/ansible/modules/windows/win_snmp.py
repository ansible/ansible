#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: win_snmp
version_added: '2.8'
short_description: Configures the Windows SNMP service
author:
    - Michael Cassaniti (@mcassaniti)
description:
    - This module configures the Windows SNMP service.
options:
    permitted_managers:
        description:
        - The list of permitted SNMP managers.
        required: false
        type: list
    community_strings:
        description:
        - The list of read-only SNMP community strings.
        required: false
        type: list
    action:
        description:
        - C(add) will add new SNMP community strings and/or SNMP managers
        - C(set) will replace SNMP community strings and/or SNMP managers
        - C(remove) will remove SNMP community strings and/or SNMP managers
        default: set
        choices: [ add, set, remove ]
'''

EXAMPLES = '''
---
  - hosts: Windows
    tasks:
      - name: Replace SNMP communities and managers
        win_snmp:
          communities:
            - public
          managers:
            - 192.168.1.2
          action: set
'''

RETURN = r'''
'''
