#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: 2019, rnsc(@rnsc) <github@rnsc.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_data_deduplication
version_added: "2.10"
short_description: Module to enable Data Deduplication on a volume.
description:
- This module can be used to enable Data Deduplication on a Windows volume.
- The module will install the FS-Data-Deduplication feature (a reboot will be necessary).
options:
  drive_letter:
    description:
    - Windows drive letter on which to enable data deduplication.
    required: yes
    type: str
  state:
    description:
    - Wether to enable or disable data deduplication on the selected volume.
    default: present
    type: str
    choices: [ present, absent ]
  settings:
    description:
    - Dictionary of settings to pass to the Set-DedupVolume powershell command.
    type: dict
    suboptions:
      minimum_file_size:
        description:
          - Minimum file size you want to target for deduplication.
          - It will default to 32768 if not defined or if the value is less than 32768.
        type: int
        default: 32768
      minimum_file_age_days:
        description:
          - Minimum file age you want to target for deduplication.
        type: int
        default: 2
      no_compress:
        description:
          - Wether you want to enabled filesystem compression or not.
        type: bool
        default: no
      optimize_in_use_files:
        description:
          - Indicates that the server attempts to optimize currently open files.
        type: bool
        default: no
      verify:
        description:
          - Indicates whether the deduplication engine performs a byte-for-byte verification for each duplicate chunk
            that optimization creates, rather than relying on a cryptographically strong hash.
          - This option is not recommend.
          - Setting this parameter to True can degrade optimization performance.
        type: bool
        default: no
author:
- rnsc (@rnsc)
'''

EXAMPLES = r'''
- name: Enable Data Deduplication on D
  win_data_deduplication:
    drive_letter: 'D'
    state: present

- name: Enable Data Deduplication on D
  win_data_deduplication:
    drive_letter: 'D'
    state: present
    settings:
      no_compress: true
      minimum_file_age_days: 1
      minimum_file_size: 0
'''

RETURN = r'''
#
'''
