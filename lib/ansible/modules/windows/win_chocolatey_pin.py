#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Simon Baerlocher <s.baerlocher@sbaerlocher.ch>
# Copyright: (c) 2018, ITIGO AG <opensource@itigo.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey_facts
version_added: '2.7'
short_description: Pin Chocolatey Packages
description:
   - This module can be chocolatey Packete pinted and unpinted.
options:
  name:
    description:
    - The name of the Software to set pin.
    - Run C(choco.exe list -lo) to get a list of Software that can be
      pinted.
    required: yes
  state:
    description:
    - When C(add) then the Software will be pinted.
    - When C(remove) then the Software will be unpinted.
    choices:
    - add
    - remove
    default: add
  version:
     description:
    - Specific version of the package to be installed.
    - Ignored when C(remove). 
author:
    - Simon Bärlocher (@sbaerlocher)
    - ITIGO AG (@itigoag)
'''

EXAMPLES = r'''
- name: pin firefox
  win_chocolatey_pin:
    name: firefox

- name: pin firefox with state
  win_chocolatey_pin:
    name: firefox
    state: add
  
- name: pin firefox with state and version
  win_chocolatey_pin:
    name: firefox
    state: add
    version: 60.0.0.1

- name: remove pin firefox
  win_chocolatey_pin:
    name: firefox
    state: remove
'''

RETURN = r'''
'''