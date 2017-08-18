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

ANSIBLE_METADATA = r'''
    metadata_version: '1.1'
    supported_by: 'community'
    status: ['preview']
'''

DOCUMENTATION = r'''
---
module: win_disk_management
version_added: '2.4'
short_description: A Windows disk management module
description:
   - With the module you can select a disk on the computer and manage it (e.g. initializing, partitioning, formatting).
   - To select the disk and to manage it you have several options which are all described in the documentation.
   - If more than one disk with the exact same specifications was found on the computer, the first found disk will be selected.
   - The module detects any existing volume and/or partition on the selected disk and will end the module in this case.
   - If parameter file_system is set to "refs" the parameter allocation_unit_size will be automatically adjusted to "64" (KB).
   - The module recognizes whether the selected switches are suitable with the selected parameters.
   - If they do not fit with the selected parameters, the switches will be automatically deactivated.
requirements:
    - Windows 8.1 / Windows 2012R2 (NT 6.3) or newer
author:
    - Marc Tschapek (@marqelme)
options:
  disk_size:
      description:
        - Size of the disk in gigabyte which will be selected
        - Data type can be int or string
      required: true
      default: 5
  partition_style_select:
      description:
        - Partition style of the disk which will be selected
      required: false
      default: raw
      choices:
        - raw
        - mbr
        - gpt
  operational_status:
      description:
        - Operational Status of the disk which will be selected
      required: false
      default: offline
      choices:
        - offline
        - online
  partition_style_set:
      description:
        - Partition style which will be set on selected disk
      required: false
      default: gpt
      choices:
        - gpt
        - mbr
  drive_letter:
      description:
        - Drive letter which will be set for the partition on selected disk (protected letters are C and D)
      required: false
      default: e
  file_system:
      description:
        - File system which will be set on selected disk
      required: false
      default: ntfs
      choices:
        - ntfs
        - refs
  label:
      description:
        - File system label which should be set for the file system on found disk
      required: false
      default: ansible_disk
  allocation_unit_size:
      description:
        - Allocation Unit size which will be set for the file system on selected disk (possible values for file system NTFS 4,8,16,32,64KB; ReFs 64KB)
        - Data type can be int or string
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
'''

EXAMPLES = r'''
- name: Select a specified disk and manage it as specified
  win_disk_management:
    disk_size: 100
    partition_style_select: raw
    operational_status: offline
    partition_style_set: mbr
    drive_letter: e
    file_system: ntfs
    label: database_disk
    allocation_unit_size: 4
    large_frs: true
    short_names: true
- name: Select a specified disk and manage it as specified
  win_disk_management:
    disk_size: 50
    partition_style_select: mbr
    operational_status: online
    partition_style_set: gpt
    drive_letter: f
    file_system: refs
    label: application_disk
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
            returned: always
            type: string
            sample: "successful"
        search_disk:
            description: Documents whether disk search with the selected options was successful or not
            returned: success or failed
            type: string
            sample: "successful"
        set_operational_status:
            description: Documents whether setting the operational status of the disk was successful or not
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "successful"
        set_writeable_status:
            description: Documents whether setting the writeable status of the disk was successful or not
            returned: success or failed (only displayed if writeable status was set)
            type: string
            sample: "successful"
        check_parameters:
            description: Documents whether all set paramters for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "successful"
        check_switches:
            description: Documents whether all set switches for the disk passed the checks or not
            returned: success or failed
            type: string
            sample: "failed"
        initialize_convert_disk:
            description: Documents whether the initialization of the disk or convertion of the partition style was successful or not
            returned: success or failed (disk will be inititialized or convert, not both)
            type: string
            sample: "successful"
        check_volumes_partitions:
            description: Documents whether the disk passed all the checks of existing volumes or partitions
            returned: success or failed
            type: string
            sample: "successful"
        create_partition:
            description: Documents whether the new partition on the disk could be created or not
            returned: success or failed
            type: string
            sample: "failed"
        create_volume:
            description: Documents whether the new volume on the partition of the disk could be created or not
            returned: success or failed
            type: string
            sample: "successful"
        maintain_shellhw_service:
            description: Documents whether maintaining the ShellHWService (Start,Stop) was successful or not
            returned: success or failed
            type: string
            sample: "failed"
search_log:
    description: dictionary containing all the detailed information about the selected disk and the current status of it
    returned: always
    type: complex
    contains:
        disk:
            description: Detailed information about the selected and found disk
            returned: always
            type: complex
            contains:
                disks_found:
                    description: Information about how many disks were found with the select disk options
                    returned: always
                    type: string
                    sample: "2"
                disk_number_chosen:
                    description: Information about which disk number was chosen (if more than one disk was found with the select disk options)
                    returned: success or failed
                    type: string
                    sample: "1"
                location:
                    description: Information about the location of the disk chosen
                    returned: success or failed
                    type: string
                    sample: "PCIROOT(0)#PCI(0C00)#SCSI(P00T00L00)"
                serial_number:
                    description: Information about the serial number of the disk chosen
                    returned: success or failed
                    type: string
                    sample: "488da91d1ea04457884b"
                unique_id:
                    description: Information about the unique id of the disk chosen
                    returned: success or failed
                    type: string
                    sample: "3141463431303031"
                operational_status:
                    description: Information about the operational status of the disk chosen
                    returned: success or failed
                    type: string
                    sample: "Online"
                partition_style:
                    description: Information about the partition style of the disk chosen
                    returned: success or failed
                    type: string
                    sample: "GPT"
        existing_volumes:
            description: Detailed information about existing volumes on the disk chosen
            returned: always
            type: complex
            contains:
                volumes_found:
                    description: Information about how many volumes were found on the disk chosen
                    returned: always
                    type: string
                    sample: "1"
                volumes_types:
                    description: Information about the volume types on the disk chosen
                    returned: success or failed
                    type: string
                    sample: "ReFs"
        existing_partitions:
            description: Detailed information about existing partitions on the disk chosen
            returned: always
            type: complex
            contains:
                partitions_found:
                    description: Information about how many partitions were found on the disk chosen
                    returned: always
                    type: string
                    sample: "3"
                partitions_types:
                    description: Information about the partition types on the disk chosen
                    returned: success or failed
                    type: string
                    sample: "Basic"
change_log:
    description: dictionary containing all the detailed information about changes on the selected disk
    returned: always
    type: complex
    contains:
        operational_status:
            description: Detailed information about setting operational status of the disk
            returned: success or failed (only displayed if operational status was set)
            type: string
            sample: "Disk set not online because partition style is RAW"
        disk_writeable:
            description: Detailed information if disk was set to writeable and if not why it was not set to it
            returned: success or failed (only displayed if writeable status was set)
            type: string
            sample: "Disk need not set to writeable because partition style is RAW"
        initialize_disk:
            description: Detailed information about initializing the disk
            returned: success or failed (only displayed if disk was initialized)
            type: string
            sample: "Disk initialization successful - Partition style raw (partition_style_select) was initalized to gpt (partition_style_set)"
        convert_disk:
            description: Detailed information about converting the partition style of the disk (in case of converting no initalization of disk)
            returned: success or failed (only displayed if partition style was converted)
            type: string
            sample: "Partition style gpt (partition_style_select) could not be converted to mbr (partition_style_set)"
        partitioning:
            description: Detailed information about partition creation on the found disk
            returned: success or failed
            type: string
            sample: "Initial partition Basic was created successfully on partition style gpt"
        formatting:
            description: Detailed information about volume creation on partitoned disk
            returned: success or failed
            type: string
            sample: "Volume ReFS was created successfully on partition Basic"
        shellhw_service_state:
            description: Detailed information about maintaining ShellHWService (start, stop)
            returned: success or failed
            type: string
            sample: "Service was stopped already and need not to be started again"
parameters:
    description: All values of the selected parameters
    returned: always
    type: complex
    contains:
        disk_size:
            description: Shows the chosen disk size in gigabyte
            returned: success or failed
            type: string
            sample: "64gb"
        drive_letter_set:
            description: Shows the chosen drive letter
            returned: success or failed
            type: string
            sample: "r"
        drive_letter_used:
            description: Documents whether the chosen drive letter is already in use on the computer
            returned: success or failed
            type: string
            sample: "no"
        forbidden_drive_letter_set:
            description: Documents whether the chosen drive letter is forbidden letter C or D
            returned: success or failed
            type: string
            sample: "no"
        file_system:
            description: Shows the chosen File System
            returned: success or failed
            type: string
            sample: "refs"
        allocation_unit_size:
            description: Shows the chosen Allocation Unit Size in kilobyte and whether it was adjusted or not
            returned: success or failed
            type: string
            sample: "64kb_adjusted_refs"
switches:
    description: All values of the selected switches
    returned: always
    type: complex
    contains:
        integrity_streams:
            description: Shows whether integrity streams are enabled or not and if they were deactivated automatically because of wrong file system
            returned: success or failed
            type: string
            sample: "enabled_deactivated_ntfs"
        large_frs:
            description: Shows whether LargeFRS is enabled or not and if they were deactivated automatically because of wrong file system
            returned: success or failed
            type: string
            sample: "enabled"
        short_names:
            description: Shows whether short names are enabled or not and if they were deactivated automatically because of wrong file system
            returned: success or failed
            type: string
            sample: "disabled"
'''
