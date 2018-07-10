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
     its volumes and partitions if existent.
requirements:
    - Windows 8.1 / Windows 2012 (NT 6.2)
author:
    - Marc Tschapek (@marqelme)
notes:
  - In order to understand all the returned properties and values please visit the following site and open the respective MSFT class
    U(https://msdn.microsoft.com/en-us/library/windows/desktop/hh830612.aspx)
'''

EXAMPLES = r'''
- name: Get disk facts
  win_disk_facts:

- name: Output first disk size
  debug:
    var: ansible_facts.disks[0].size

- name: Convert first system disk into various formats
  debug:
    msg: '{{ disksize_gib }} vs {{ disksize_gib_human }}'
  vars:
    # Get first system disk
    disk: '{{ ansible_facts.disks|selectattr("system_disk")|first }}'

    # Show disk size in Gibibytes
    disksize_gib_human: '{{ disk.size|filesizeformat(True) }}'   # returns "223.6 GiB" (human readable)
    disksize_gib: '{{ (disk.size/1024|pow(3))|round|int }} GiB'  # returns "224 GiB" (value in GiB)

    # Show disk size in Gigabytes
    disksize_gb_human: '{{ disk.size|filesizeformat }}'        # returns "240.1 GB" (human readable)
    disksize_gb: '{{ (disk.size/1000|pow(3))|round|int }} GB'  # returns "240 GB" (value in GB)

- name: Output second disk serial number
  debug:
    var: ansible_facts.disks[0].serial_number
'''

RETURN = r'''
ansible_facts:
    description: Dictionary containing all the detailed information about the disks of the target.
    returned: always
    type: complex
    contains:
        ansible_disks:
            description: Detailed information about one particular disk.
            returned: if disks were found
            type: list
            contains:
                number:
                    description: Disk number of the particular disk.
                    returned: always
                    type: int
                    sample: 0
                size:
                    description: Size in bytes of the particular disk.
                    returned: always
                    type: int
                    sample: 227727638528
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
                    type: int
                    sample: 4
                operational_status:
                    description: Operational status of the particular disk.
                    returned: always
                    type: string
                    sample: "Online"
                sector_size:
                    description: Sector size in bytes of the particular disk.
                    returned: always
                    type: int
                    sample: 4096
                read_only:
                    description: Read only status of the particular disk.
                    returned: always
                    type: bool
                    sample: True
                bootable:
                    description: Information whether the particular disk is a bootable disk.
                    returned: always
                    type: bool
                    sample: False
                system_disk:
                    description: Information whether the particular disk is a system disk.
                    returned: always
                    type: bool
                    sample: True
                clustered:
                    description: Information whether the particular disk is clustered (part of a failover cluster).
                    returned: always
                    type: bool
                    sample: False
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
                partitions:
                    description: Detailed information about one particular partition on the specified disk.
                    returned: if existent
                    type: list
                    contains:
                        number:
                            description: Number of the particular partition.
                            returned: always
                            type: int
                            sample: 1
                        size:
                            description:
                              - Size in bytes of the particular partition.
                            returned: always
                            type: int
                            sample: 838860800
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
                            type: bool
                            sample: True
                        mbr_type:
                            description: mbr type of the particular partition.
                            returned: if partition_style property of the particular disk has value "MBR"
                            type: int
                            sample: 7
                        active:
                            description: Information whether the particular partition is an active partition or not.
                            returned: if partition_style property of the particular disk has value "MBR"
                            type: bool
                            sample: True
                        drive_letter:
                            description: Drive letter of the particular partition.
                            returned: if existent
                            type: string
                            sample: "C"
                        transition_state:
                            description: Transition state of the particular partition.
                            returned: always
                            type: int
                            sample: 1
                        offset:
                            description: Offset of the particular partition.
                            returned: always
                            type: int
                            sample: 368050176
                        hidden:
                            description: Information whether the particular partition is hidden or not.
                            returned: always
                            type: bool
                            sample: True
                        shadow_copy:
                            description: Information whether the particular partition is a shadow copy of another partition.
                            returned: always
                            type: bool
                            sample: False
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
                        volumes:
                            description: Detailed information about one particular volume on the specified partition.
                            returned: if existent
                            type: list
                            contains:
                                size:
                                    description:
                                      - Size in bytes of the particular volume.
                                    returned: always
                                    type: int
                                    sample: 838856704
                                size_remaining:
                                    description:
                                      - Remaining size in bytes of the particular volume.
                                    returned: always
                                    type: int
                                    sample: 395620352
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
                                    description: Allocation unit size in bytes of the particular volume.
                                    returned: always
                                    type: int
                                    sample: 4096
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
                        size:
                            description:
                              - Size in bytes of the particular physical disk.
                            returned: always
                            type: int
                            sample: 240057409536
                        allocated_size:
                            description:
                              - Allocated size in bytes of the particular physical disk.
                            returned: always
                            type: int
                            sample: 240057409536
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
                        bus_type:
                            description: Bus type of the particular physical disk.
                            returned: always
                            type: string
                            sample: "SCSI"
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
                                    type: int
                                    sample: 5
                                value:
                                    description: List of supported usage types.
                                    returned: always
                                    type: string
                                    sample: "Auto-Select, Hot Spare"
                        spindle_speed:
                            description: Spindle speed in rpm of the particular physical disk.
                            returned: always
                            type: int
                            sample: 4294967295
                        physical_location:
                            description: Physical location of the particular physical disk.
                            returned: always
                            type: string
                            sample: "Integrated : Adapter 3 : Port 0 : Target 0 : LUN 0"
                        manufacturer:
                            description: Manufacturer of the particular physical disk.
                            returned: always
                            type: string
                            sample: "SUSE"
                        model:
                            description: Model of the particular physical disk.
                            returned: always
                            type: string
                            sample: "Xen Block"
                        can_pool:
                            description: Information whether the particular physical disk can be added to a storage pool.
                            returned: always
                            type: bool
                            sample: False
                        cannot_pool_reason:
                            description: Information why the particular physical disk can not be added to a storage pool.
                            returned: if can_pool property has value false
                            type: string
                            sample: "Insufficient Capacity"
                        indication_enabled:
                            description: Information whether indication is enabled for the particular physical disk.
                            returned: always
                            type: bool
                            sample: True
                        partial:
                            description: Information whether the particular physical disk is partial.
                            returned: always
                            type: bool
                            sample: False
                        serial_number:
                            description: Serial number of the particular physical disk.
                            returned: always
                            type: string
                            sample: "b62beac80c3645e5877f"
                        object_id:
                            description: Object ID of the particular physical disk.
                            returned: always
                            type: string
                            sample: '{1}\\\\HOST\\root/Microsoft/Windows/Storage/Providers_v2\\SPACES_PhysicalDisk.ObjectId=\"{<object_id>}:PD:{<pd>}\"'
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
                        size:
                            description:
                              - Size in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 240057409536
                        allocated_size:
                            description:
                              - Allocated size in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 240057409536
                        footprint_on_pool:
                            description:
                              - Footprint on pool in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 240057409536
                        name:
                            description: Name of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "vDisk1"
                        friendly_name:
                            description: Friendly name of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Prod2 Virtual Disk"
                        operational_status:
                            description: Operational status of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "OK"
                        health_status:
                            description: Health status of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Healthy"
                        provisioning_type:
                            description: Provisioning type of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Thin"
                        allocation_unit_size:
                            description: Allocation unit size in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 4096
                        media_type:
                            description: Media type of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Unspecified"
                        parity_layout:
                            description: Parity layout of the particular virtual disk.
                            returned: if existent
                            type: int
                            sample: 1
                        access:
                            description: Access of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Read/Write"
                        detached_reason:
                            description: Detached reason of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "None"
                        write_cache_size:
                            description: Write cache size in byte of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 100
                        fault_domain_awareness:
                            description: Fault domain awareness of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "PhysicalDisk"
                        inter_leave:
                            description:
                              - Inter leave in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 102400
                        deduplication_enabled:
                            description: Information whether deduplication is enabled for the particular virtual disk.
                            returned: always
                            type: bool
                            sample: True
                        enclosure_aware:
                            description: Information whether the particular virtual disk is enclosure aware.
                            returned: always
                            type: bool
                            sample: False
                        manual_attach:
                            description: Information whether the particular virtual disk is manual attached.
                            returned: always
                            type: bool
                            sample: True
                        snapshot:
                            description: Information whether the particular virtual disk is a snapshot.
                            returned: always
                            type: bool
                            sample: False
                        tiered:
                            description: Information whether the particular virtual disk is tiered.
                            returned: always
                            type: bool
                            sample: True
                        physical_sector_size:
                            description: Physical sector size in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 4096
                        logical_sector_size:
                            description: Logical sector size in byte of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 512
                        available_copies:
                            description: Number of the available copies of the particular virtual disk.
                            returned: if existent
                            type: int
                            sample: 1
                        columns:
                            description: Number of the columns of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 2
                        groups:
                            description: Number of the groups of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 1
                        physical_disk_redundancy:
                            description: Type of the physical disk redundancy of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 1
                        read_cache_size:
                            description: Read cache size in byte of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 0
                        request_no_spof:
                            description: Information whether the particular virtual disk requests no single point of failure.
                            returned: always
                            type: bool
                            sample: True
                        resiliency_setting_name:
                            description: Type of the physical disk redundancy of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 1
                        object_id:
                            description: Object ID of the particular virtual disk.
                            returned: always
                            type: string
                            sample: '{1}\\\\HOST\\root/Microsoft/Windows/Storage/Providers_v2\\SPACES_VirtualDisk.ObjectId=\"{<object_id>}:VD:{<vd>}\"'
                        unique_id:
                            description: Unique ID of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "260542E4C6B01D47A8FA7630FD90FFDE"
                        unique_id_format:
                            description: Unique ID format of the particular virtual disk.
                            returned: always
                            type: string
                            sample: "Vendor Specific"
'''
