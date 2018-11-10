#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_defrag
version_added: '2.4'
short_description: Consolidate fragmented files on local volumes
description:
- Locates and consolidates fragmented files on local volumes to improve system performance.
- 'More information regarding C(win_defrag) is available from: U(https://technet.microsoft.com/en-us/library/cc731650(v=ws.11).aspx)'
options:
  include_volumes:
    description:
    - A list of drive letters or mount point paths of the volumes to be defragmented.
    - If this parameter is omitted, all volumes (not excluded) will be fragmented.
    type: list
  exclude_volumes:
    description:
    - A list of drive letters or mount point paths to exclude from defragmentation.
    type: list
  freespace_consolidation:
    description:
    - Perform free space consolidation on the specified volumes.
  priority:
    description:
    - Run the operation at low or normal priority.
    choices: [ low, normal ]
    default: low
  parallel:
    description:
    - Run the operation on each volume in parallel in the background.
    type: bool
    default: 'no'
requirements:
- defrag.exe
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Defragment all local volumes (in parallel)
  win_defrag:
    parallel: yes

- name: 'Defragment all local volumes, except C: and D:'
  win_defrag:
    exclude_volumes: [ C, D ]

- name: 'Defragment volume D: with normal priority'
  win_defrag:
    include_volumes: D
    priority: normal

- name: Consolidate free space (useful when reducing volumes)
  win_defrag:
    freespace_consolidation: yes
'''

RETURN = r'''
cmd:
    description: The complete command line used by the module
    returned: always
    type: string
    sample: defrag.exe /C /V
rc:
    description: The return code for the command
    returned: always
    type: int
    sample: 0
stdout:
    description: The standard output from the command
    returned: always
    type: string
    sample: Success.
stderr:
    description: The error output from the command
    returned: always
    type: string
    sample:
msg:
    description: Possible error message on failure
    returned: failed
    type: string
    sample: Command 'defrag.exe' not found in $env:PATH.
changed:
    description: Whether or not any changes were made.
    returned: always
    type: bool
    sample: True
'''
