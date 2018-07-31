#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Liran Nisanov <lirannis@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_pagefile
version_added: "2.4"
short_description: Query or change pagefile configuration
description:
    - Query current pagefile configuration.
    - Enable/Disable AutomaticManagedPagefile.
    - Create new or override pagefile configuration.
options:
  drive:
    description:
      - The drive of the pagefile.
  initial_size:
    description:
      - The initial size of the pagefile in megabytes.
    type: int
  maximum_size:
    description:
      - The maximum size of the pagefile in megabytes.
    type: int
  override:
    description:
      - Override the current pagefile on the drive.
    type: bool
    default: 'yes'
  system_managed:
    description:
      - Configures current pagefile to be managed by the system.
    type: bool
    default: 'no'
  automatic:
    description:
      - Configures AutomaticManagedPagefile for the entire system.
    type: bool
  remove_all:
    description:
      - Remove all pagefiles in the system, not including automatic managed.
    type: bool
    default: 'no'
  test_path:
    description:
      - Use Test-Path on the drive to make sure the drive is accessible before creating the pagefile.
    type: bool
    default: 'yes'
  state:
    description:
      - State of the pagefile.
    choices: [ absent, present, query ]
    default: query
notes:
- There is difference between automatic managed pagefiles that configured once for the entire system and system managed pagefile that configured per pagefile.
- InitialSize 0 and MaximumSize 0 means the pagefile is managed by the system.
- Value out of range exception may be caused by several different issues, two common problems - No such drive, Pagefile size is too small.
- Setting a pagefile when AutomaticManagedPagefile is on will disable the AutomaticManagedPagefile.
author:
- Liran Nisanov (@LiranNis)
'''

EXAMPLES = r'''
- name: Query pagefiles configuration
  win_pagefile:

- name: Query C pagefile
  win_pagefile:
    drive: C

- name: Set C pagefile, don't override if exists
  win_pagefile:
    drive: C
    initial_size: 1024
    maximum_size: 1024
    override: no
    state: present

- name: Set C pagefile, override if exists
  win_pagefile:
    drive: C
    initial_size: 1024
    maximum_size: 1024
    state: present

- name: Remove C pagefile
  win_pagefile:
    drive: C
    state: absent

- name: Remove all current pagefiles, enable AutomaticManagedPagefile and query at the end
  win_pagefile:
    remove_all: yes
    automatic: yes

- name: Remove all pagefiles disable AutomaticManagedPagefile and set C pagefile
  win_pagefile:
    drive: C
    initial_size: 2048
    maximum_size: 2048
    remove_all: yes
    automatic: no
    state: present

- name: Set D pagefile, override if exists
  win_pagefile:
    drive: d
    initial_size: 1024
    maximum_size: 1024
    state: present
'''

RETURN = r'''
automatic_managed_pagefiles:
    description: Whether the pagefiles is automatically managed.
    returned: When state is query.
    type: boolean
    sample: true
pagefiles:
    description: Contains caption, description, initial_size, maximum_size and name for each pagefile in the system.
    returned: When state is query.
    type: list
    sample:
      [{"caption": "c:\\ 'pagefile.sys'", "description": "'pagefile.sys' @ c:\\", "initial_size": 2048, "maximum_size": 2048, "name": "c:\\pagefile.sys"},
       {"caption": "d:\\ 'pagefile.sys'", "description": "'pagefile.sys' @ d:\\", "initial_size": 1024, "maximum_size": 1024, "name": "d:\\pagefile.sys"}]

'''
