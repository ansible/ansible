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
   - This module pins and unpins chocolatey packages.
options:
  name:
    description:
    - The name of the Packages to pin.
    - Run C(choco.exe list -lo) to get a list of Packages that can be pinned.
    required: yes
  state:
    description:
    - When C(pinned) then the Packages will be pinned.
    - When C(unpinned) then the Packages will be unpinned.
    choices:
    - pinned
    - unpinned
    default: pinned
  version:
     description:
    - Specific version of the package to be installed.
    - Ignored when C(unpinned). 
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
    state: pinned
  
- name: pin firefox with state and version
  win_chocolatey_pin:
    name: firefox
    state: pinned
    version: 60.0.0.1

- name: remove pin firefox
  win_chocolatey_pin:
    name: firefox
    state: unpinned
'''

RETURN = r'''
'''