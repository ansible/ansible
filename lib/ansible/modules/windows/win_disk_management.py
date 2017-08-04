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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_disk_management
version_added: '2.4'
short_description: A Windows disk management module
description:
   - Find a disk on the server (unit GB) and manage it. To find the disk and to setup the disk you have several options.
options:
  FindSize:
      description:
        - Size of the disk to find
      required: true
      default: 5
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
        - Drive letter which should be set for the partition on found disk (protected letters are C and D)
      required: false
      default: E
  SetAllocUnitSize:
      description:
        - Allocation Unit size which should be set for the file system on found disk (possible values for file system NTFS 4,8,16,32,64KB; ReFs 64KB)
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
      type: bool
      default: 'no'
  SetShortNames:
      description:
        - Switch to set Short Names option for file system on found disk, only for NTFS file system
      type: bool
      default: 'no'
  SetIntegrityStreams:
      description:
        - Switch to set Integrity Streams option for file system on found disk, only for ReFs file system
      type: bool
      default: 'no'
author:
    - Marc Tschapek (@marqelme)
'''

EXAMPLES = r'''
- name: Select a defined disk and manage it as specified
  win_disk_management:
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

- name: Select a defined disk and manage it as specified
  win_disk_management:
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

RETURN = r'''
changed:
    description: Whether anything was changed
    returned: always
    type: boolean
    sample: True
msg:
    description: Possible error message on failure
    returned: failed
    type: string
    sample: No disk found (size or property is wrong or disk is not attached).
generallog:
    description: dictionary containing all the general logs and stat data
    returned: always
    type: complex
    contains:
        Rescan disks:
            description: Documents whether rescaning the disks of the computer via diskpart was successful or not
            returned: success or failed
            type: string
            sample: "Successful"
        Search disk:
            description: Documents whether the search of the attached disk was successful or not
            returned: success or failed
            type: string
            sample: "Successful"
        Set Operational Status:
            description: Documents whether setting the operational status of the disk was successful or not
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "Successful"
        Set Writeable Status:
            description: Documents whether setting the writeable status of the disk was successful or not
            returned: success or failed (only displayed if writeable status was set)
            type: string
            sample: "Successful"
        Check parameters:
            description: Documents whether all set paramters for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "Successful"
        Check switches:
            description: Documents whether all set switches for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "Failed"
        Initialize / convert disk:
            description: Documents whether the initialization of the disk or convertion of the partition style was successful or not
            returned: success or failed (disk will be inititialized or convert, not both)
            type: string
            sample: "Successful"
        Check volumes / partitions:
            description: Documents whether the disk passed all the checks of existing volumes or partitions
            returned: success or failed
            type: string
            sample: "Successful"
        Create Partition:
            description: Documents whether the new partition on the disk could be created or not
            returned: success or failed
            type: string
            sample: "Failed"
        Create Volume:
            description: Documents whether the new volume on the partition of the disk could be created or not
            returned: success or failed
            type: string
            sample: "Successful"
        Maintain ShellHWService:
            description: Documents whether maintaining the ShellHWService (Start,Stop) was successful or not
            returned: success or failed
            type: string
            sample: "Failed"
log:
    description: dictionary containing all the detailed logs and stat data of the general log parts
    returned: always
    type: complex
    contains:
        Disk:
            description: Detailed information about found disk
            returned: success or failed
            type: string
            sample: "Disks found: 1, Disk number: 1, Location: PCIROOT(0)#PCI(1F00)#SCSI(P00T00L00), Serial Number: f78c2db7b54562, Unique ID: 31414634313031"
        Operational Status:
            description: Detailed information about setting operational status of the disk
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "Disk set not online because partition style is RAW"
        Disk Writeable:
            description: Detailed information if disk was set to writeable and if not why it was not set to it
            returned: success or failed (only displayed if writeable status was set
            type: string
            sample: "Disk need not set to writeable because partition style is RAW"
        Existing volumes:
            description: Detailed information about found volumes on the searched disk
            returned: success or failed
            type: string
            sample: "Volumes found: 1"
        Existing partitions:
            description: Detailed information about found partitions on the searched disk
            returned: success or failed
            type: string
            sample: "Partition Style: RAW, Partitions found: 0"
        Initialize disk:
            description: Detailed information about initializing the disk
            returned: success or failed (only displayed if disk was initialized)
            type: string
            sample: "Disk initialization successful - Partition style RAW (FindPartitionStyle) was initalized to GPT (SetPartitionStyle)"
        Convert disk (no initialization needed):
            description: Detailed information about converting the partition style of the disk
            returned: success or failed (only displayed if partition style was converted)
            type: string
            sample: "Partition style GPT (FindPartitionStyle) could not be converted to MBR (SetPartitionStyle)"
        Partitioning:
            description: Detailed information about partition creation on the found disk
            returned: success or failed
            type: string
            sample: "Initial partition Basic was created successfully on partition style GPT"
        Formatting:
            description: Detailed information about volume creation on partitoned disk
            returned: success or failed
            type: string
            sample: "Volume ReFS was created successfully on partiton Basic"
        ShellHWService State:
            description: Detailed information about maintaining ShellHWService (Start,Stop)
            returned: success or failed
            type: string
            sample: "Service was stopped already and need not to be started again"
parameters:
    description: All values of the set parameters
    returned: always
    type: complex
    contains:
        Set drive letter:
            description: Shows the chosen drive letter
            returned: success or failed
            type: string
            sample: "R"
        Found same drive letter:
            description: Documents whether the chosen drive letter is already in use on the computer
            returned: success or failed
            type: string
            sample: "No"
        Set forbidden drive letter C or D:
            description: Documents whether the chosen drive letter is not C or D
            returned: success or failed
            type: string
            sample: "No"
        File system:
            description: Shows the chosen File System
            returned: success or failed
            type: string
            sample: "ReFs"
        Allocation Unit size:
            description: Shows the chosen Allocation Unit Size and whether it was adjusted or not
            returned: success or failed
            type: string
            sample: "64 KB (adjusted for ReFs)"
switches:
    description: All values of the set switches
    returned: always
    type: complex
    contains:
        Integrity Streams:
            description: Shows whether integrity streams are activated or not
            returned: success or failed
            type: string
            sample: "Disabled"
        LargeFRS:
            description: Shows whether LargeFRS is activated or not
            returned: success or failed
            type: string
            sample: "Enabled"
        Short Names:
            description: Shows whether short names are activated or not
            returned: success or failed
            type: string
            sample: "Disabled"
'''
