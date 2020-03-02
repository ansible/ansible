#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Brian Scholer <@briantist>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_psrepository_info
version_added: '2.10'
short_description: Gather information about PSRepositories
description:
  - Gather information about all or a specific PSRepository.
options:
  name:
    description:
      - The name of the repository to retrieve.
      - Supports any wildcard pattern supported by C(Get-PSRepository).
      - If omitted then all repositories will returned.
    type: str
    default: '*'
requirements:
  - C(PowerShellGet) module
seealso:
  - module: win_psrepository
author:
  - Brian Scholer (@briantist)
'''

EXAMPLES = r'''
- name: Get info for a single repository
  win_psrepository_info:
    name: PSGallery
  register: repo_info

- name: Find all repositories that start with 'MyCompany'
  win_psrepository_info:
    name: MyCompany*

- name: Get info for all repositories
  win_psrepository_info:
  register: repo_info

- name: Remove all repositories that don't have a publish_location set
  win_psrepository:
    name: "{{ item }}"
    state: absent
  loop: "{{ repo_info.repositories | rejectattr('publish_location', 'none') | list }}"
'''

RETURN = r'''
repositories:
  description:
    - A list of repositories (or an empty list is there are none).
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description:
        - The name of the repository.
      type: str
      sample: PSGallery
    installation_policy:
      description:
        - The installation policy of the repository. The sample values are the only possible values.
      type: str
      sample:
        - Trusted
        - Untrusted
    trusted:
      description:
        - A boolean flag reflecting the value of C(installation_policy) as to whether the repository is trusted.
      type: bool
    package_management_provider:
      description:
        - The name of the package management provider for this repository.
      type: str
      sample: NuGet
    provider_options:
      description:
        - Provider-specific options for this repository.
      type: dict
    source_location:
      description:
        - The location used to find and retrieve modules. This should always have a value.
      type: str
      sample: https://www.powershellgallery.com/api/v2
    publish_location:
      description:
        - The location used to publish modules.
      type: str
      sample: https://www.powershellgallery.com/api/v2/package/
    script_source_location:
      description:
        - The location used to find and retrieve scripts.
      type: str
      sample: https://www.powershellgallery.com/api/v2/items/psscript
    script_publish_location:
      description:
        - The location used to publish scripts.
      type: str
      sample: https://www.powershellgallery.com/api/v2/package/
    registered:
      description:
        - Whether the module is registered. Should always be C(True)
      type: bool
'''
