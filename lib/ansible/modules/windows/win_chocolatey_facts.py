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
version_added: '2.8'
short_description: Create a facts collection for Chocolatey
description:
- This module shows information from Chocolatey, such as installed packages, configuration, feature and sources.
notes:
- Chocolatey must be installed beforehand, use M(win_chocolatey) to do this.
seealso:
- module: win_chocolatey
- module: win_chocolatey_config
- module: win_chocolatey_feature
- module: win_chocolatey_source
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
  description: Detailed information about the Chocolatey installation
  returned: always
  type: complex
  contains:
    ansible_chocolatey:
      description: Detailed information about the Chocolatey installation
      returned: always
      type: complex
      contains:
        config:
          description: Detailed information about stored the configurations
          returned: always
          type: dict
          sample:
            commandExecutionTimeoutSeconds: 2700
            containsLegacyPackageInstalls: true
        feature:
          description: Detailed information about enabled and disabled features
          returned: always
          type: dict
          sample:
            allowEmptyCheckums: false
            autoUninstaller: true
            failOnAutoUninstaller: false
        sources:
          description: List of Chocolatey sources
          returned: always
          type: complex
          contains:
            admin_only:
              description: Is the source visible to Administrators only
              returned: always
              type: bool
              sample: false
            allow_self_service:
              description: Is the source allowed to be used with self-service
              returned: always
              type: bool
              sample: false
            bypass_proxy:
              description: Can the source explicitly bypass configured proxies
              returned: always
              type: bool
              sample: true
            certificate:
              description: Pth to a PFX certificate for X509 authenticated feeds
              returned: always
              type: str
              sample: C:\chocolatey\cert.pfx
            disabled:
              description: Is the source disabled
              returned: always
              type: bool
              sample: false
            name:
              description: Name of the source
              returned: always
              type: str
              sample: chocolatey
            priority:
              description: The priority order of this source, lower is better, 0 is no priority
              returned: always
              type: int
              sample: 0
            source:
              description: The source, can be a folder/file or an url
              returned: always
              type: str
              sample: https://chocolatey.org/api/v2/
            source_username:
              description: Username used to access authenticated feeds
              returned: always
              type: str
              sample: username
        packages:
          description: List of installed Packages
          returned: alway
          type: complex
          contains:
            package:
              description: Name of the package
              returned: always
              type: str
              sample: vscode
            version:
              description: Version of the package
              returned: always
              type: str
              sample: '1.27.2'
'''
