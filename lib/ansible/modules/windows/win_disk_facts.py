#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_disk_facts
version_added: '2.5'
short_description: Show the attached disks and disk information of the target host
description:
   - With the module you can retrieve and output detailed information about the attached disks of the target and
     it's volumes and partitions if existent.
requirements:
    - Windows 8.1 / Windows 2012R2 (NT 6.3) or newer
author:
    - Marc Tschapek (@marqelme)
notes:
  - You can use this module in combination with the win_disk_management module in order to retrieve the disks status
    on the target.
  - In order to understand all the returned properties and values please visit the following site and open the respective MSFT class
    https://msdn.microsoft.com/en-us/library/windows/desktop/hh830612(v=vs.85).aspx
'''

EXAMPLES = r'''
- name: get disk facts
  win_disk_facts:
- name: output first disk size
  debug:
    var: ansible_facts.ansible_disk.disk_0.size

- name: get disk facts
  win_disk_facts:
- name: output second disk serial number
  debug:
    var: ansible_facts.ansible_disk.disk_1.serial_number
'''

RETURN = r'''
changed:
    description: Whether anything was changed.
    returned: always
    type: boolean
    sample: true
msg:
    description: Possible error message on failure.
    returned: failed
    type: string
    sample: "No disks could be found on the target"
ansible_facts:
    description: Dictionary containing all the detailed information about the disks of the target.
    returned: always
    type: complex
    contains:
        ansible_disk:
            description: Detailed information about found disks on the target.
            returned: always
            type: complex
            contains:
                total_disks_found:
                    description: Count of found disks on the target.
                    returned: success or failed
                    type: string
                    sample: "3"
                disk_identifier:
                    description: 
                      - Detailed information about one particular disk.
                      - The identifier is displayed as a digit in order to structure the output but is not the actual number of the particular disk.
                      - Please see the containing return property "number" to get the actual disk number of the particular disk.
                    returned: success or failed
                    type: complex
                    contains:
                        number:
                            description: Disk number of the particular disk.
                            returned: always
                            type: string
                            sample: "0"
                        size:
                            description: Size in gb of the particular disk.
                            returned: always
                            type: string
                            sample: "100gb"
                        bus_type:
                            description: Bus type of the particular disk.
                            returned: always
                            type: string
                            sample: "SCSI"
                        friendly_name:
                            description: Friendly name of the particular disk.
                            returned: always
                            type: string
                            sample: "Red Hat VirtIO SCSI Disk Device"
                        partition_style:
                            description: Partition style of the particular disk.
                            returned: always
                            type: string
                            sample: "MBR"
                        partition_count:
                            description: Number of partitions on the particular disk.
                            returned: always
                            type: string
                            sample: "4"
                        operational_status:
                            description: Operational status of the particular disk.
                            returned: always
                            type: string
                            sample: "Online"
                        sector_size:
                            description: Sector size of the particular disk.
                            returned: always
                            type: string
                            sample: "512byte"
                        read_only:
                            description: Read only status of the particular disk.
                            returned: always
                            type: string
                            sample: "true"
                        bootable:
                            description: Information whether the particular disk is a bootable disk.
                            returned: always
                            type: string
                            sample: "false"
                        system_disk:
                            description: Information whether the particular disk is a system disk.
                            returned: always
                            type: string
                            sample: "true"
                        clustered:
                            description: Information whether the particular disk is clustered (part of a failover cluster).
                            returned: always
                            type: string
                            sample: "false"
                        manufacturer:
                            description: Manufacturer of the particular disk.
                            returned: always
                            type: string
                            sample: "Red Hat"
                        model:
                            description: Model specification of the particular disk.
                            returned: always
                            type: string
                            sample: "VirtIO"
                        firmware_version:
                            description: Firmware version of the particular disk.
                            returned: always
                            type: string
                            sample: "0001"
                        location:
                            description: Location of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "PCIROOT(0)#PCI(0400)#SCSI(P00T00L00)"
                        serial_number:
                            description: Serial number of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "b62beac80c3645e5877f"
                        unique_id:
                            description: Unique ID of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "3141463431303031"
                        guid:
                            description: GUID of the particular disk on the target.
                            returned: if existent
                            type: string
                            sample: "{efa5f928-57b9-47fc-ae3e-902e85fbe77f}"
                        path:
                            description: Path of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "\\\\?\\scsi#disk&ven_red_hat&prod_virtio#4&23208fd0&1&000000#{<id>}"
                        partition_identifier:
                            description: 
                              - Detailed information about one particular partition on the specified disk.
                              - The identifier is displayed as a digit in order to structure the output but is not the actual number of the particular partition.
                              - Please see the containing return property "number" to get the actual partition number.
                            returned: if existent
                            type: complex
                            contains:
                                number:
                                    description: Number of the particular partition.
                                    returned: always
                                    type: string
                                    sample: "1"
                                size:
                                    description: 
                                      - Size in gb of the particular partition.
                                      - Accurate to three decimal places.
                                    returned: always
                                    type: string
                                    sample: "0.031gb"
                                type:
                                    description: Type of the particular partition.
                                    returned: always
                                    type: string
                                    sample: "IFS"
                                gpt_type:
                                    description: gpt type of the particular partition.
                                    returned: if partition_style property of the particular disk has value "GPT"
                                    type: string
                                    sample: "{e3c9e316-0b5c-4db8-817d-f92df00215ae}"
                                no_default_driveletter:
                                    description: Information whether the particular partition has a default drive letter or not.
                                    returned: if partition_style property of the particular disk has value "GPT"
                                    type: string
                                    sample: "true"
                                mbr_type:
                                    description: mbr type of the particular partition.
                                    returned: f partition_style property of the particular disk has value "MBR"
                                    type: string
                                    sample: "7"
                                active:
                                    description: Information whether the particular partition is an active partition or not.
                                    returned: f partition_style property of the particular disk has value "MBR"
                                    type: string
                                    sample: "true"
                                drive_letter:
                                    description: Drive letter of the particular partition.
                                    returned: if existent
                                    type: string
                                    sample: "C"
                                transition_state:
                                    description: Transition state of the particular partition.
                                    returned: always
                                    type: string
                                    sample: "1"
                                offset:
                                    description: Offset of the particular partition.
                                    returned: always
                                    type: string
                                    sample: "368050176"
                                hidden:
                                    description: Information whether the particular partition is hidden or not.
                                    returned: always
                                    type: string
                                    sample: "true"
                                shadow_copy:
                                    description: Information whether the particular partition is a shadow copy of another partition.
                                    returned: always
                                    type: string
                                    sample: "false"
                                guid:
                                    description: GUID of the particular partition.
                                    returned: if existent
                                    type: string
                                    sample: "{302e475c-6e64-4674-a8e2-2f1c7018bf97}"
                                access_paths:
                                    description: Access paths of the particular partition.
                                    returned: if existent
                                    type: string
                                    sample: "\\\\?\\Volume{85bdc4a8-f8eb-11e6-80fa-806e6f6e6963}\\"
                                volume_identifier:
                                    description: 
                                      - Detailed information about one particular volume on the specified partition.
                                      - Please note that volumes have no "number" property and the identifier is displayed as a digit in order to structure the output.
                                    returned: if existent
                                    type: complex
                                    contains:
                                        size:
                                            description:
                                              - Size in gb of the particular volume.
                                              - Accurate to three decimal places.
                                            returned: always
                                            type: string
                                            sample: "0,342gb"
                                        size_remaining:
                                            description:
                                              - Remaining size in gb of the particular volume.
                                              - Accurate to three decimal places.
                                            returned: always
                                            type: string
                                            sample: "0,146gb"
                                        type:
                                            description: File system type of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "NTFS"
                                        label:
                                            description: File system label of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "System Reserved"
                                        health_status:
                                            description: Health status of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "Healthy"
                                        drive_type:
                                            description: Drive type of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "Fixed"
                                        allocation_unit_size:
                                            description: Allocation unit size of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "64kb"
                                        object_id:
                                            description: Object ID of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "\\\\?\\Volume{85bdc4a9-f8eb-11e6-80fa-806e6f6e6963}\\"
                                        path:
                                            description: Path of the particular volume.
                                            returned: always
                                            type: string
                                            sample: "\\\\?\\Volume{85bdc4a9-f8eb-11e6-80fa-806e6f6e6963}\\"
                        physical_disk:
                            description: Detailed information about physical disk properties of the particular disk.
                            returned: if existent
                            type: complex
                            contains:
                                media_type:
                                    description: Media type of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "UnSpecified"
                                device_id:
                                    description: Device ID of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "0"
                                friendly_name:
                                    description: Friendly name of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "PhysicalDisk0"
                                operational_status:
                                    description: Operational status of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "OK"
                                health_status:
                                    description: Health status of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "Healthy"
                                usage_type:
                                    description: Usage type of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "Auto-Select"
                                supported_usages:
                                    description: Supported usage types of the particular physical disk.
                                    returned: always
                                    type: complex
                                    contains:
                                        Count:
                                            description: Count of supported usage types.
                                            returned: always
                                            type: string
                                            sample: "5"
                                        value:
                                            description: List of supported usage types.
                                            returned: always
                                            type: string
                                            sample: "Auto-Select, Hot Spare"
                                spindle_speed:
                                    description: Spindle speed in rpm of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "4294967295rpm"
                                can_pool:
                                    description: Information whether the particular physical disk can be added to a storage pool.
                                    returned: always
                                    type: string
                                    sample: "false"
                                cannot_pool_reason:
                                    description: Information why the particular physical disk can't be added to a storage pool.
                                    returned: if can_pool property has value false
                                    type: string
                                    sample: "Insufficient Capacity"
                                object_id:
                                    description: Object ID of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "{1}\\\\HOST\\root/Microsoft/Windows/Storage/Providers_v2\\SPACES_PhysicalDisk.ObjectId=\"{<object_id>}:PD:{<pd>}\"
                                unique_id:
                                    description: Unique ID of the particular physical disk.
                                    returned: always
                                    type: string
                                    sample: "3141463431303031"
                        virtual_disk:
                            description: Detailed information about virtual disk properties of the particular disk.
                            returned: if existent
                            type: complex
                            contains:
                                friendly_name:
                                    description: Friendly name of the particular virtual disk.
                                    returned: always
                                    type: string
                                    sample: "Prod2 Virtual Disk"
'''
