#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Marc Tschapek <marc.tschapek@bitgroup.de>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: win_disk_setup
version_added: "1.0"
short_description: A windows disk module
description:
  - Find a disk on the server and set it up. To find the disk and to setup the disk you have several options.
options:
  FindSize:
    description:
      - Size of the disk to find
    required: true
    default: 5
    aliases: []
  FindPartitionStyle:
    description:
      - Partition style which should be set on the disk to find
    required: false
    default: RAW
    choices:
      - RAW
      - MBR
      - GPT
  FindOperationalStatus:
    description:
      - Operational Status which should be set on the disk to find
    required: false
    default: Offline
    choices:
      - Offline
      - Online
  SetPartitionStyle:
    description:
      - Partition style which should be set on found disk
    required: false
    default: GPT
    choices:
      - GPT
      - MBR
  SetDriveLetter:
    description:
      - Drive letter which should be set for the partition on found disk (Protected letters are C and D)
    required: false
    default: E
  SetAllocUnitSize:
    description:
      - Allocation Unit size which should be set for the file system on found disk (possible values for file system NTFS are 4,8,16,32,64KB; possible value for file system ReFs is 64KB)
    required: false
    default: 4
    choices:
      - 8
      - 16
      - 32
      - 64
  SetFileSystem:
    description:
      - File system which should be set on found disk
    required: false
    default: NTFS
    choices:
      - NTFS
      - ReFs
  SetLabel:
    description:
      - File system label which should be set for the file system on found disk
    required: false
    default: AdditionalDisk
  SetLargeFRS:
    description:
      - Switch to set Large FRS option for file system on found disk, only for NTFS file system
    required: false
    default: false
    choices:
      - true
      - false
  SetShortNames:
    description:
      - Switch to set Short Names option for file system on found disk, only for NTFS file system
    required: false
    default: false
    choices:
      - true
      - false
  SetIntegrityStreams:
    description:
      - Switch to set Integrity Streams option for file system on found disk, only for ReFs file system
    required: false
    default: false
    choices:
      - true
      - false
author: "Marc Tschapek (@marctschapek)"
'''

EXAMPLES = '''
- name: Find a defined disk and set it up as specified
  win_disk:
    FindSize: 100
    FindPartitionStyle: RAW
    FindOperationalStatus: Offline    
    SetPartitionStyle: MBR
    SetDriveLetter: E
    SetFileSystem: NTFS
    SetLabel: DatabaseDisk
    SetAllocUnitSize: 4
    SetLargeFRS: true
    SetShortNames: true

- name: Find a defined disk and set it up as specified
  win_disk:
    FindSize: 50
    FindPartitionStyle: MBR
    FindOperationalStatus: Online
    SetPartitionStyle: GPT
    SetDriveLetter: F
    SetFileSystem: ReFs
    SetLabel: ApplicationDisk
    SetAllocUnitSize: 64
    SetIntegrityStreams: true
'''
