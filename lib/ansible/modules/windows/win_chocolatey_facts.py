#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
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
short_description: Create a facts collection for chocolatey
description:
   - This module shows information from chocolatey, such as installed packages, configuration, feature and sources.
author:
    - Simon Bärlocher (@sbaerlocher)
    - ITIGO AG (@itigoag)
'''

EXAMPLES = r'''
- name: Gather facts from chocolatey
  win_chocolatey_facts:

- name: Displays the Configuration
  debug:
    var: ansible_chocolatey.config

- name: Displays the Feature
  debug:
    var: ansible_chocolatey.feature

- name: Displays the Sources
  debug:
    var: ansible_chocolatey.sources

- name: Displays the Packages
  debug:
    var: ansible_chocolatey.packages
'''

RETURN = r'''
ansible_facts:
    description: Detailed information about the chocolatey installation.
    returned: always
    type: complex
    contains:
        ansible_chocolatey:
            description: Detailed information about the Chocolatey installation.
            returned: infos when choco is found.
            type: dict
            contains:
                config:
                    description: Detailed information about stored the Configurations.
                    returned: always
                    type: dict
                feature:
                    description: Detailed information about enabled and disabled functions.
                    returned: always
                    type: dict
                sources:
                    description: Detailed information about the deposited Chocolatey sources.
                    returned: always
                    type: complex
                    admin_only:
                        returned: always
                        type: string
                    allow_self_service:
                        returned: always
                        type: string
                    bypass_proxy:
                        returned: always
                        type: string
                    certificate:
                        returned: always
                        type: string
                    disabled:
                        returned: always
                        type: string
                    name:
                        returned: always
                        type: string
                    priority:
                        returned: always
                        type: string
                    source:
                        returned: always
                        type: string
                    source_username:
                        returned: always
                        type: string
                packages:
                    description: Detailed information about the installed Packages.
                    returned: alway
                    type: complex
                    package:
                        description: Returns name of Package.
                        returned: alway
                        type: string
                    version:
                        description: Returns version of Package.
                        returned: alway
                        type: dict
'''
