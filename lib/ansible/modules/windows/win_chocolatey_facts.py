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
    var: ansible_facts.chocolatey.config

- name: Displays the Feature
  debug: 
    var: ansible_facts.chocolatey.feature
 
- name: Displays the Sources
  debug: 
    var: ansible_facts.chocolatey.sources
  
- name: Displays the Packages
  debug:
    var: ansible_facts.chocolatey.packages 
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
            type: list
            contains:
                config:
                    description: List of Configurations.
                    returned: always
                feature:
                    description: List of Feature.
                    returned: always
                sources:
                    description: List of Sources.
                    returned: always
                packages:
                    description: List of Packages.
                    returned: always

'''
