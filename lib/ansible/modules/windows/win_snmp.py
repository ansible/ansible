#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: win_snmp
version_added: '2.8'
short_description: Configures the Windows SNMP service
description:
    - This module configures the Windows SNMP service.
options:
    permitted_managers:
        description:
        - The list of permitted SNMP managers.
        type: list
    community_strings:
        description:
        - The list of read-only SNMP community strings.
        type: list
    action:
        description:
        - C(add) will add new SNMP community strings and/or SNMP managers
        - C(set) will replace SNMP community strings and/or SNMP managers. An
          empty list for either C(community_strings) or C(permitted_managers)
          will result in the respective lists being removed entirely.
        - C(remove) will remove SNMP community strings and/or SNMP managers
        type: str
        choices: [ add, set, remove ]
        default: set
author:
    - Michael Cassaniti (@mcassaniti)
'''

EXAMPLES = r'''
---
  - hosts: Windows
    tasks:
      - name: Replace SNMP communities and managers
        win_snmp:
          community_strings:
            - public
          permitted_managers:
            - 192.168.1.2
          action: set

  - hosts: Windows
    tasks:
      - name: Replace SNMP communities and clear managers
        win_snmp:
          community_strings:
            - public
          permitted_managers: []
          action: set
'''

RETURN = r'''
community_strings:
    description: The list of community strings for this machine.
    type: list
    returned: always
    sample:
      - public
      - snmp-ro
permitted_managers:
    description: The list of permitted managers for this machine.
    type: list
    returned: always
    sample:
      - 192.168.1.1
      - 192.168.1.2
'''
