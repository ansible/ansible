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
   - With the module you can select a disk on the server and manage it (e.g. initializing, partitioning, formatting).
   - To select the disk and to manage it you have several options which are all described in the documentation.
   - The module detects any existing volume and/or partition on selected disk and will end in this case
options:
  disk_size:
      description:
        - Size (unit GB) of the disk which will be selected
      required: true
      default: 5
  partition_style_select:
      description:
        - Partition style of the disk which will be selected
      required: false
      default: RAW
      choices:
        - RAW
        - MBR
        - GPT
  operational_status:
      description:
        - Operational Status of the disk which will be selected
      required: false
      default: Offline
      choices:
        - Offline
        - Online
  partition_style_set:
      description:
        - Partition style which will be set on selected disk
      required: false
      default: GPT
      choices:
        - GPT
        - MBR
  drive_letter:
      description:
        - Drive letter which will be set for the partition on selected disk (protected letters are C and D)
      required: false
      default: E
  file_system:
      description:
        - File system which will be set on selected disk
      required: false
      default: NTFS
      choices:
        - NTFS
        - ReFs
  label:
      description:
        - File system label which should be set for the file system on found disk
      required: false
      default: AdditionalDisk
  allocation_unit_size:
      description:
        - Allocation Unit size which will be set for the file system on selected disk (possible values for file system NTFS 4,8,16,32,64KB; ReFs 64KB)
      required: false
      default: 4
      choices:
        - 8
        - 16
        - 32
        - 64
  large_frs:
      description:
        - Switch to set Large FRS option for file system on selected disk, only for NTFS file system
      type: bool
      default: 'no'
  short_names:
      description:
        - Switch to set Short Names option for file system on selected disk, only for NTFS file system
      type: bool
      default: 'no'
  integrity_streams:
      description:
        - Switch to set Integrity Streams option for file system on selected disk, only for ReFs file system
      type: bool
      default: 'no'
author:
    - Marc Tschapek (@marqelme)
'''

EXAMPLES = r'''
- name: Select a defined disk and manage it as specified
  win_disk_management:
    disk_size: 100
    partition_style_select: RAW
    operational_status: Offline
    partition_style_set: MBR
    drive_letter: E
    file_system: NTFS
    label: DatabaseDisk
    allocation_unit_size: 4
    large_frs: true
    short_names: true

- name: Select a defined disk and manage it as specified
  win_disk_management:
    disk_size: 50
    partition_style_select: MBR
    operational_status: Online
    partition_style_set: GPT
    drive_letter: F
    file_system: ReFs
    label: ApplicationDisk
    allocation_unit_size: 64
    integrity_streams: true
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
general_log:
    description: dictionary containing all the general logs and stat data
    returned: always
    type: complex
    contains:
        rescan_disks:
            description: Documents whether rescaning the disks of the computer via diskpart was successful or not
            returned: success or failed
            type: string
            sample: "Successful"
        search_disk:
            description: Documents whether the search of the attached disk was successful or not
            returned: success or failed
            type: string
            sample: "Successful"
        set_operational_status:
            description: Documents whether setting the operational status of the disk was successful or not
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "Successful"
        set_writeable_status:
            description: Documents whether setting the writeable status of the disk was successful or not
            returned: success or failed (only displayed if writeable status was set)
            type: string
            sample: "Successful"
        check_parameters:
            description: Documents whether all set paramters for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "Successful"
        check_switches:
            description: Documents whether all set switches for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "Failed"
        initialize_convert_disk:
            description: Documents whether the initialization of the disk or convertion of the partition style was successful or not
            returned: success or failed (disk will be inititialized or convert, not both)
            type: string
            sample: "Successful"
        check_volumes_partitions:
            description: Documents whether the disk passed all the checks of existing volumes or partitions
            returned: success or failed
            type: string
            sample: "Successful"
        create_partition:
            description: Documents whether the new partition on the disk could be created or not
            returned: success or failed
            type: string
            sample: "Failed"
        create_volume:
            description: Documents whether the new volume on the partition of the disk could be created or not
            returned: success or failed
            type: string
            sample: "Successful"
        maintain_shellhw_service:
            description: Documents whether maintaining the ShellHWService (Start,Stop) was successful or not
            returned: success or failed
            type: string
            sample: "Failed"
log:
    description: dictionary containing all the detailed logs and stat data of the general log parts
    returned: always
    type: complex
    contains:
        disk:
            returned: success or failed
            type: string
            sample: "Disks found: 1, Disk number: 1, Location: PCIROOT(0)#PCI(1F00)#SCSI(P00T00L00), Serial Number: f78c2db7b54562, Unique ID: 31414634313031"
        operational_status:
            description: Detailed information about setting operational status of the disk
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "Disk set not online because partition style is RAW"
        disk_writeable:
            description: Detailed information if disk was set to writeable and if not why it was not set to it
            returned: success or failed (only displayed if writeable status was set
            type: string
            sample: "Disk need not set to writeable because partition style is RAW"
        existing_volumes:
            description: Detailed information about found volumes on the searched disk
            returned: success or failed
            type: string
            sample: "Volumes found: 1"
        existing_partitions:
            description: Detailed information about found partitions on the searched disk
            returned: success or failed
            type: string
            sample: "Partition Style: RAW, Partitions found: 0"
        initialize_disk:
            description: Detailed information about initializing the disk
            returned: success or failed (only displayed if disk was initialized)
            type: string
            sample: "Disk initialization successful - Partition style RAW (FindPartitionStyle) was initalized to GPT (SetPartitionStyle)"
        convert_disk:
            description: Detailed information about converting the partition style of the disk (in case of converting no initalization of disk)
            returned: success or failed (only displayed if partition style was converted)
            type: string
            sample: "Partition style GPT (FindPartitionStyle) could not be converted to MBR (SetPartitionStyle)"
        partitioning:
            description: Detailed information about partition creation on the found disk
            returned: success or failed
            type: string
            sample: "Initial partition Basic was created successfully on partition style GPT"
        formatting:
            description: Detailed information about volume creation on partitoned disk
            returned: success or failed
            type: string
            sample: "Volume ReFS was created successfully on partiton Basic"
        shellhw_service_state:
            description: Detailed information about maintaining ShellHWService (Start,Stop)
            returned: success or failed
            type: string
            sample: "Service was stopped already and need not to be started again"
parameters:
    description: All values of the selected parameters
    returned: always
    type: complex
    contains:
        disk_size:
            description: Shows the chosen disk size
            returned: success or failed
            type: string
            sample: "64 GB"
        drive_letter_set:
            description: Shows the chosen drive letter
            returned: success or failed
            type: string
            sample: "R"
        drive_letter_used:
            description: Documents whether the chosen drive letter is already in use on the computer
            returned: success or failed
            type: string
            sample: "No"
        forbidden_drive_letter_set:
            description: Documents whether the chosen drive letter is forbidden letter C or D
            returned: success or failed
            type: string
            sample: "No"
        file_system:
            description: Shows the chosen File System
            returned: success or failed
            type: string
            sample: "ReFs"
        allocation_unit_size:
            description: Shows the chosen Allocation Unit Size and whether it was adjusted or not
            returned: success or failed
            type: string
            sample: "64 KB (adjusted for ReFs)"
switches:
    description: All values of the selected switches
    returned: always
    type: complex
    contains:
        integrity_streams:
            description: Shows whether integrity streams are activated or not
            returned: success or failed
            type: string
            sample: "Disabled"
        large_frs:
            description: Shows whether LargeFRS is activated or not
            returned: success or failed
            type: string
            sample: "Enabled"
        short_names:
            description: Shows whether short names are activated or not
            returned: success or failed
            type: string
            sample: "Disabled"
'''
