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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_disk_management
version_added: '2.5'
short_description: A Windows disk management module
description:
   - With the module you can select a disk on the target and manage it (e.g. initializing, partitioning, formatting).
   - To select the disk and to manage it you have several options which are all described in the documentation.
   - If you want to activate verbose logging output for the module you can use the option logging with value "verbose".
   - The values of the following options will be checked and converted if needed in the beginning of the module
   - size, allocation_unit_size, number, drive_letter.
   - If one of the values can not be converted the module will be canceled.
   - In order to find only one disk on the target you can use the size and/or number option for the search of the disk.
   - If no size and number option value was defined and multiple disks were found on the target with the defined option values
   - the module will select the first disk found.
   - The module detects any existing volume and/or partition on the selected disk and will cancel the module in this case.
   - If you want to set a specific drive letter to the selected disk you can use the option drive_letter.
   - If this drive letter is already in use on the target the module will be canceled.
   - If no drive_letter option value was defined the module will use a free drive letter on the target randomly.
   - If no free drive lettter is left on the target the module will be canceled.
   - If the selected disk size does not match with the passed value for option file_system (e.g. "ntfs") the module will be canceled.
   - If option file_system is set to "refs" the option allocation_unit_size will be automatically adjusted to "64" (KB).
   - The module recognizes whether the passed set options large_frs, integrity streams and short_names
   - are suitable with the passed file_system value. If they do not fit the set options will be automatically disabled.
   - If the disk is not yet initialized the module will initialize the disk (set partition style, online and writeable).
   - If the disk is initialized already the script will try to set the disk to "online" and "writeable" (read-only eq. false)
   - if it's not the state of the disk already.
   - Further in this case it will convert the partition style of the disk to the selected partition style if needed.
   - The script will stop and start the service "ShellHWService" again in order to avoid disk management GUI messages.
   - If the script fails with an error and the operational status was set from "offline" to "online" before, the script will set the disk to
   - operational status "offline" again.
requirements:
    - Windows 8.1 / Windows 2012R2 (NT 6.3) or newer
author:
    - Marc Tschapek (@marqelme)
options:
  size:
      description:
        - Size of the disk in gigabyte which will be selected
        - If a size is defined the module will try to select the disk with this defined size
        - Data type can be int or string
      required: false
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
  read_only:
      description:
        - Read-only status of the disk which will be selected (true,yes=read-only, false,no=writeable)
      required: false
      type: bool
      default: 'yes'
  number:
      description:
        - Number of the disk which will be selected
        - If a number is defined the module will try to select the disk with this given number
        - Data type can be int or string
      required: false
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
        - Drive letter which will be set for the partition on selected disk
        - If a drive letter is defined the module will try to set the partition on selected disk with this given drive letter
      required: false
  file_system:
      description:
        - File system which will be set on selected disk
        - Maximum volume size for ntfs is 256gb, for refs 1208925819614650gb (1yobibyte)
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
        - Switch to set Large FRS option for file system on selected disk, solely settable for NTFS file system
      required: false
      type: bool
      default: 'no'
  short_names:
      description:
        - Switch to set Short Names option for file system on selected disk, solely settable for NTFS file system
      required: false
      type: bool
      default: 'no'
  integrity_streams:
      description:
        - Switch to set Integrity Streams option for file system on selected disk, solely settable for ReFs file system
      required: false
      type: bool
      default: 'no'
  logging:
      description:
        - Logging mode of the module
        - If verbose mode is chosen the output of the module will pass back
        - the option_values_passed log
        - the general logs option_values and convert_validate_options as well as the change log convert_options
      required: false
      default: standard
      choices:
        - standard
        - verbose
'''

EXAMPLES = r'''
- name: Select a defined disk and manage it as specified
  win_disk_management:
    # select_disk_by
    partition_style_select: raw
    operational_status: offline
    read_only: true
    number: 1
    # set_disk_by
    partition_style_set: mbr
    file_system: ntfs
    label: database_disk
    allocation_unit_size: 4
    large_frs: true
    short_names: true
    # module_output
    logging: verbose
- name: Select a defined disk and manage it as specified
  win_disk_management:
    # select_disk_by
    size: 50
    partition_style_select: mbr
    operational_status: online
    read_only: false
    # set_disk_by
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
    sample: "No free drive_letter left on the target"
option_values_passed:
    description:
      - Dictionary containing all passed option values
      - Only in module output if logging option was invoked with value "verbose"
    returned: in verbose logging mode
    type: complex
    contains:
        check_mode:
            description: Shows the passed value for option check_mode
            returned: always
            type: string
            sample: "False"
        size:
            description: Shows the passed value for option size
            returned: if size option value was passed
            type: string
            sample: "100"
        partition_style_select:
            description: Shows the passed value for option partition_style_select
            returned: always
            type: string
            sample: "raw"
        operational_status:
            description: Shows the passed value for option operational_status
            returned: always
            type: string
            sample: "offline"
        read_only:
            description: Shows the passed value for option read_only
            returned: always
            type: string
            sample: "False"
        number:
            description: Shows the passed value for option number
            returned: if number option value was passed
            type: string
            sample: "1"
        partition_style_set:
            description: Shows the passed value for option partition_style_set
            returned: always
            type: string
            sample: "mbr"
        drive_letter:
            description: Shows the passed value for option drive_letter
            returned: if drive_letter option value was passed
            type: string
            sample: "e"
        file_system:
            description: Shows the passed value for option file_system
            returned: always
            type: string
            sample: "ntfs"
        label:
            description: Shows the passed value for option label
            returned: always
            type: string
            sample: "ansible_disk"
        allocation_unit_size:
            description: Shows the passed value for option allocation_unit_size
            returned: always
            type: string
            sample: "4kb"
        large_frs:
            description: Shows the passed value for option large_frs
            returned: always
            type: string
            sample: "False"
        short_names:
            description: Shows the passed value for option short_names
            returned: always
            type: string
            sample: "False"
        integrity_streams:
            description: Shows the passed value for option integrity_streams
            returned: always
            type: string
            sample: "True"
        logging:
            description: Shows the passed value for option logging
            returned: always
            type: string
            sample: "standard"
general_log:
    description: Dictionary containing all the general logs and stat data
    returned: always
    type: complex
    contains:
        convert_validate_options:
            description: Documents whether validating and converting the variables from string to integer was successful or not
            returned: if logging option was invoked with value "verbose"
            type: string
            sample: "successful"
        option_values:
            description: Documents whether adding the option_values_passed to the module output was successful
            returned: if logging option was invoked with value "verbose"
            type: string
            sample: "successful"
        rescan_disks:
            description: Documents whether rescaning the disks of the target via diskpart was successful or not
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
            returned: success or failed
            type: string
            sample: "successful"
        set_writeable_status:
            description: Documents whether setting the writeable status of the disk (disk set read-only or not) was successful or not
            returned: success, failed or untouched
            type: string
            sample: "successful"
        check_set_options:
            description: Documents whether all set option values for the selected disk, partition and volume passed the checks or not
            returned: success or failed
            type: string
            sample: "successful"
        initialize_convert:
            description: Documents whether the initialization of the disk or convertion of the partition style was successful or not
            returned: success or failed (disk will be inititialized or converted, not both)
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
            description:
              - Documents whether maintaining the ShellHWService was successful or not
              - Service needs to be stopped in order to avoid GUI messages for disk management in Windows
            returned: success or failed
            type: string
            sample: "failed"
disk_selected:
    description: Dictionary containing all the detailed information about the selected disk and the current status of it
    returned: always
    type: complex
    contains:
        disk:
            description: Information about the selected disk
            returned: always
            type: complex
            contains:
                total_found_disks:
                    description: Information about how many disks were found on the target with the passed disk options
                    returned: always
                    type: string
                    sample: "2"
                number:
                    description: Information about which disk number was selected with passed option values
                    returned: success or failed
                    type: string
                    sample: "1"
                size:
                    description: Information about which size the selected disk number has
                    returned: success or failed
                    type: string
                    sample: "100"
        existing_volumes:
            description: Information about existing volumes on the selected disk
            returned: always
            type: complex
            contains:
                volumes_found:
                    description: Information about how many volumes were found on the selected disk
                    returned: always
                    type: string
                    sample: "1"
                volumes_types:
                    description: Information about the volume types on the selected disk
                    returned: success or failed
                    type: string
                    sample: "ReFs"
        existing_partitions:
            description: Detailed information about existing partitions on the selected disk
            returned: always
            type: complex
            contains:
                partitions_found:
                    description: Information about how many partitions were found on the selected disk
                    returned: always
                    type: string
                    sample: "3"
                partitions_types:
                    description: Information about the partition types on the selected disk
                    returned: success or failed
                    type: string
                    sample: "Basic"
search_log:
    description: Dictionary containing information about searched items and states on the target
    returned: always
    type: complex
    contains:
        shellhw_service_state:
        description: Information about ShellHWService state (check)
        returned: success or failed
        type: string
        sample: "running"
change_log:
    description: Dictionary containing all the detailed information about changes on the selected disk
    returned: always
    type: complex
    contains:
        convert_options:
            description:
              - Detailed information about converting variables of options from string into integer32 or 64
              - This change log does not changes anything on the target client only in module and script environment
              - Convertion will be only take place if one of the str/int options is of type string
              - The convert of the option variables will also help to identify wrong option values
              - For instance non numeric string was used for the size option the convertion does fail and end the module
            returned: if logging option was invoked with value "verbose"
            type: complex
            contains:
                size:
                    description: Information whether the size option value was converted or not
                    returned: success or failed
                    type: string
                    sample: "Converted option variable from string to int64"
                allocation_unit_size:
                    description: Information whether the allocation_unit_size option value was converted or not
                    returned: success or failed
                    type: string
                    sample: "Converted option variable from string to int32"
                number:
                    description: Information whether the number option value was converted or not
                    returned: success or failed
                    type: string
                    sample: "No convertion of option variable needed"
                drive_letter:
                    description: Information whether the drive_letter option value was converted or not
                    returned: success or failed
                    type: string
                    sample: "No drive_letter option used, no convertion needed"
        operational_status:
            description: Detailed information about setting operational status of the disk
            returned: success or failed
            type: string
            sample: "Disk is offline, but nothing will be changed because partition style is RAW and disk will be set to online during intialization part"
        writeable_status:
            description: Detailed information if disk was set from read-only to writeable and if not why it was not set to it
            returned: success or failed
            type: string
            sample: "Disk set from read-only to writeable"
        initializing:
            description: Detailed information about initializing the disk
            returned: success or failed
            type: string
            sample: "Disk initialization successful - Partition style raw (partition_style_select) was initalized to gpt (partition_style_set)"
        converting:
            description: Detailed information about converting the partition style of the disk (in case of converting no initalization of disk)
            returned: success or failed
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
            description: Detailed information about executed ShellHWService action (start, stop)
            returned: success or failed
            type: string
            sample: "Service was stopped already and need not to be started again"
set_options:
    description: Checks for all passed values of the options which will set anything on the selected disk and it's partition or volume
    returned: always
    type: complex
    contains:
        drive_letter_set:
            description:
              - Shows the drive letter which was selected by the module on basis of the passed drive_letter option value
              - If nothing was passed to the module it will show the drive letter which was selected by the module itself
              - If nothing could be selected because no free drive letter is available it will show this status
            returned: success or failed
            type: string
            sample: "r"
        drive_letter_used:
            description:
              - Documents whether the passed value of option drive_letter (if passed) is in use on the target already
              - If the module selects the value for drive letter it will show "no" expect there is no free drive letter available on the target (then "yes")
            returned: success or failed
            type: string
            sample: "no"
        size_file_system:
            description: Documents whether the passed value for option size is a valid disk size for the passed option value of file_system
            returned: success or failed
            type: string
            sample: "valid_size"
        allocation_unit_size:
            description: Shows whether the selected allocation unit size was adjusted due to file_system option value "refs" (needs 64kb)
            returned: success or failed
            type: string
            sample: "64kb_adjusted_refs"
        integrity_streams:
            description:
              - If integrity_streams option with value "true" was passed to the module it shows whether
              - integrity streams option was disabled again because of non-compliant file_system option value "ntfs"
            returned: success or failed
            type: string
            sample: "deactivated_ntfs"
        large_frs:
            description:
              - If large_frs option with value "true" was passed to the module it shows whether
              - large_frs option was disabled again because of non-compliant file_system option value "refs"
            returned: success or failed
            type: string
            sample: "deactivated_refs"
        short_names:
            description:
              - If short_names option with value "true" was passed to the module it shows whether
              - short_names option was disabled again because of non-compliant file_system option value "refs"
            returned: success or failed
            type: string
            sample: "deactivated_refs"
'''
