#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
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
            description: Detailed information about the chocolatey installation.
            returned: infos when choco is found.
            type: dict
            contains:
                config:
                    description: Dict of Configurations.
                    returned: always
                    type: dict
                feature:
                    description: Dict of Feature.
                    returned: always
                    type: dict
                sources:
                    description: Dict of Sources.
                    returned: always
                    type: dict
                packages:
                    description: Dict of Packages.
                    returned: alway
                    type: dict
'''
