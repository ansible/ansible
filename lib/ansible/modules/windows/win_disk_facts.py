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
notes:
  - In order to understand all the returned properties and values please visit the following site and open the respective MSFT class
    U(https://msdn.microsoft.com/en-us/library/windows/desktop/hh830612.aspx)
author:
  - Marc Tschapek (@marqelme)
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
    disksize_gib_human: '{{ disk.size|filesizeformat(true) }}'   # returns "223.6 GiB" (human readable)
    disksize_gib: '{{ (disk.size/1024|pow(3))|round|int }} GiB'  # returns "224 GiB" (value in GiB)

    # Show disk size in Gigabytes
    disksize_gb_human: '{{ disk.size|filesizeformat }}'        # returns "240.1 GB" (human readable)
    disksize_gb: '{{ (disk.size/1000|pow(3))|round|int }} GB'  # returns "240 GB" (value in GB)

- name: Output second disk serial number
  debug:
    var: ansible_facts.disks[1].serial_number
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
                    type: str
                    sample: "SCSI"
                friendly_name:
                    description: Friendly name of the particular disk.
                    returned: always
                    type: str
                    sample: "Red Hat VirtIO SCSI Disk Device"
                partition_style:
                    description: Partition style of the particular disk.
                    returned: always
                    type: str
                    sample: "MBR"
                partition_count:
                    description: Number of partitions on the particular disk.
                    returned: always
                    type: int
                    sample: 4
                operational_status:
                    description: Operational status of the particular disk.
                    returned: always
                    type: str
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
                    sample: true
                bootable:
                    description: Information whether the particular disk is a bootable disk.
                    returned: always
                    type: bool
                    sample: false
                system_disk:
                    description: Information whether the particular disk is a system disk.
                    returned: always
                    type: bool
                    sample: true
                clustered:
                    description: Information whether the particular disk is clustered (part of a failover cluster).
                    returned: always
                    type: bool
                    sample: false
                manufacturer:
                    description: Manufacturer of the particular disk.
                    returned: always
                    type: str
                    sample: "Red Hat"
                model:
                    description: Model specification of the particular disk.
                    returned: always
                    type: str
                    sample: "VirtIO"
                firmware_version:
                    description: Firmware version of the particular disk.
                    returned: always
                    type: str
                    sample: "0001"
                location:
                    description: Location of the particular disk on the target.
                    returned: always
                    type: str
                    sample: "PCIROOT(0)#PCI(0400)#SCSI(P00T00L00)"
                serial_number:
                    description: Serial number of the particular disk on the target.
                    returned: always
                    type: str
                    sample: "b62beac80c3645e5877f"
                unique_id:
                    description: Unique ID of the particular disk on the target.
                    returned: always
                    type: str
                    sample: "3141463431303031"
                guid:
                    description: GUID of the particular disk on the target.
                    returned: if existent
                    type: str
                    sample: "{efa5f928-57b9-47fc-ae3e-902e85fbe77f}"
                path:
                    description: Path of the particular disk on the target.
                    returned: always
                    type: str
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
                            type: str
                            sample: "IFS"
                        gpt_type:
                            description: gpt type of the particular partition.
                            returned: if partition_style property of the particular disk has value "GPT"
                            type: str
                            sample: "{e3c9e316-0b5c-4db8-817d-f92df00215ae}"
                        no_default_driveletter:
                            description: Information whether the particular partition has a default drive letter or not.
                            returned: if partition_style property of the particular disk has value "GPT"
                            type: bool
                            sample: true
                        mbr_type:
                            description: mbr type of the particular partition.
                            returned: if partition_style property of the particular disk has value "MBR"
                            type: int
                            sample: 7
                        active:
                            description: Information whether the particular partition is an active partition or not.
                            returned: if partition_style property of the particular disk has value "MBR"
                            type: bool
                            sample: true
                        drive_letter:
                            description: Drive letter of the particular partition.
                            returned: if existent
                            type: str
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
                            sample: true
                        shadow_copy:
                            description: Information whether the particular partition is a shadow copy of another partition.
                            returned: always
                            type: bool
                            sample: false
                        guid:
                            description: GUID of the particular partition.
                            returned: if existent
                            type: str
                            sample: "{302e475c-6e64-4674-a8e2-2f1c7018bf97}"
                        access_paths:
                            description: Access paths of the particular partition.
                            returned: if existent
                            type: str
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
                                    type: str
                                    sample: "NTFS"
                                label:
                                    description: File system label of the particular volume.
                                    returned: always
                                    type: str
                                    sample: "System Reserved"
                                health_status:
                                    description: Health status of the particular volume.
                                    returned: always
                                    type: str
                                    sample: "Healthy"
                                drive_type:
                                    description: Drive type of the particular volume.
                                    returned: always
                                    type: str
                                    sample: "Fixed"
                                allocation_unit_size:
                                    description: Allocation unit size in bytes of the particular volume.
                                    returned: always
                                    type: int
                                    sample: 4096
                                object_id:
                                    description: Object ID of the particular volume.
                                    returned: always
                                    type: str
                                    sample: "\\\\?\\Volume{85bdc4a9-f8eb-11e6-80fa-806e6f6e6963}\\"
                                path:
                                    description: Path of the particular volume.
                                    returned: always
                                    type: str
                                    sample: "\\\\?\\Volume{85bdc4a9-f8eb-11e6-80fa-806e6f6e6963}\\"
                physical_disk:
                    description: Detailed information about physical disk properties of the particular disk.
                    returned: if existent
                    type: complex
                    contains:
                        media_type:
                            description: Media type of the particular physical disk.
                            returned: always
                            type: str
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
                            type: str
                            sample: "0"
                        friendly_name:
                            description: Friendly name of the particular physical disk.
                            returned: always
                            type: str
                            sample: "PhysicalDisk0"
                        operational_status:
                            description: Operational status of the particular physical disk.
                            returned: always
                            type: str
                            sample: "OK"
                        health_status:
                            description: Health status of the particular physical disk.
                            returned: always
                            type: str
                            sample: "Healthy"
                        bus_type:
                            description: Bus type of the particular physical disk.
                            returned: always
                            type: str
                            sample: "SCSI"
                        usage_type:
                            description: Usage type of the particular physical disk.
                            returned: always
                            type: str
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
                                    type: str
                                    sample: "Auto-Select, Hot Spare"
                        spindle_speed:
                            description: Spindle speed in rpm of the particular physical disk.
                            returned: always
                            type: int
                            sample: 4294967295
                        physical_location:
                            description: Physical location of the particular physical disk.
                            returned: always
                            type: str
                            sample: "Integrated : Adapter 3 : Port 0 : Target 0 : LUN 0"
                        manufacturer:
                            description: Manufacturer of the particular physical disk.
                            returned: always
                            type: str
                            sample: "SUSE"
                        model:
                            description: Model of the particular physical disk.
                            returned: always
                            type: str
                            sample: "Xen Block"
                        can_pool:
                            description: Information whether the particular physical disk can be added to a storage pool.
                            returned: always
                            type: bool
                            sample: false
                        cannot_pool_reason:
                            description: Information why the particular physical disk can not be added to a storage pool.
                            returned: if can_pool property has value false
                            type: str
                            sample: "Insufficient Capacity"
                        indication_enabled:
                            description: Information whether indication is enabled for the particular physical disk.
                            returned: always
                            type: bool
                            sample: true
                        partial:
                            description: Information whether the particular physical disk is partial.
                            returned: always
                            type: bool
                            sample: false
                        serial_number:
                            description: Serial number of the particular physical disk.
                            returned: always
                            type: str
                            sample: "b62beac80c3645e5877f"
                        object_id:
                            description: Object ID of the particular physical disk.
                            returned: always
                            type: str
                            sample: '{1}\\\\HOST\\root/Microsoft/Windows/Storage/Providers_v2\\SPACES_PhysicalDisk.ObjectId=\"{<object_id>}:PD:{<pd>}\"'
                        unique_id:
                            description: Unique ID of the particular physical disk.
                            returned: always
                            type: str
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
                            type: str
                            sample: "vDisk1"
                        friendly_name:
                            description: Friendly name of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Prod2 Virtual Disk"
                        operational_status:
                            description: Operational status of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "OK"
                        health_status:
                            description: Health status of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Healthy"
                        provisioning_type:
                            description: Provisioning type of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Thin"
                        allocation_unit_size:
                            description: Allocation unit size in bytes of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 4096
                        media_type:
                            description: Media type of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Unspecified"
                        parity_layout:
                            description: Parity layout of the particular virtual disk.
                            returned: if existent
                            type: int
                            sample: 1
                        access:
                            description: Access of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Read/Write"
                        detached_reason:
                            description: Detached reason of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "None"
                        write_cache_size:
                            description: Write cache size in byte of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 100
                        fault_domain_awareness:
                            description: Fault domain awareness of the particular virtual disk.
                            returned: always
                            type: str
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
                            sample: true
                        enclosure_aware:
                            description: Information whether the particular virtual disk is enclosure aware.
                            returned: always
                            type: bool
                            sample: false
                        manual_attach:
                            description: Information whether the particular virtual disk is manual attached.
                            returned: always
                            type: bool
                            sample: true
                        snapshot:
                            description: Information whether the particular virtual disk is a snapshot.
                            returned: always
                            type: bool
                            sample: false
                        tiered:
                            description: Information whether the particular virtual disk is tiered.
                            returned: always
                            type: bool
                            sample: true
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
                            sample: true
                        resiliency_setting_name:
                            description: Type of the physical disk redundancy of the particular virtual disk.
                            returned: always
                            type: int
                            sample: 1
                        object_id:
                            description: Object ID of the particular virtual disk.
                            returned: always
                            type: str
                            sample: '{1}\\\\HOST\\root/Microsoft/Windows/Storage/Providers_v2\\SPACES_VirtualDisk.ObjectId=\"{<object_id>}:VD:{<vd>}\"'
                        unique_id:
                            description: Unique ID of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "260542E4C6B01D47A8FA7630FD90FFDE"
                        unique_id_format:
                            description: Unique ID format of the particular virtual disk.
                            returned: always
                            type: str
                            sample: "Vendor Specific"
                win32_disk_drive:
                    description: Representation of the Win32_DiskDrive class.
                    returned: if existent
                    type: complex
                    contains:
                        availability:
                            description: Availability and status of the device.
                            returned: always
                            type: int
                        bytes_per_sector:
                            description: Number of bytes in each sector for the physical disk drive.
                            returned: always
                            type: int
                            sample: 512
                        capabilities:
                            description:
                            - Array of capabilities of the media access device.
                            - For example, the device may support random access (3), removable media (7), and automatic cleaning (9).
                            returned: always
                            type: list
                            sample:
                                - 3
                                - 4
                        capability_descriptions:
                            description:
                            - List of more detailed explanations for any of the access device features indicated in the Capabilities array.
                            - Note, each entry of this array is related to the entry in the Capabilities array that is located at the same index.
                            returned: always
                            type: list
                            sample:
                                - Random Access
                                - Supports Writing
                        caption:
                            description: Short description of the object.
                            returned: always
                            type: str
                            sample: VMware Virtual disk SCSI Disk Device
                        compression_method:
                            description: Algorithm or tool used by the device to support compression.
                            returned: always
                            type: str
                            sample: Compressed
                        config_manager_error_code:
                            description: Windows Configuration Manager error code.
                            returned: always
                            type: int
                            sample: 0
                        config_manager_user_config:
                            description: If True, the device is using a user-defined configuration.
                            returned: always
                            type: bool
                            sample: true
                        creation_class_name:
                            description:
                            - Name of the first concrete class to appear in the inheritance chain used in the creation of an instance.
                            - When used with the other key properties of the class, the property allows all instances of this class
                            - and its subclasses to be uniquely identified.
                            returned: always
                            type: str
                            sample: Win32_DiskDrive
                        default_block_size:
                            description: Default block size, in bytes, for this device.
                            returned: always
                            type: int
                            sample: 512
                        description:
                            description: Description of the object.
                            returned: always
                            type: str
                            sample: Disk drive
                        device_id:
                            description: Unique identifier of the disk drive with other devices on the system.
                            returned: always
                            type: str
                            sample: "\\\\.\\PHYSICALDRIVE0"
                        error_cleared:
                            description: If True, the error reported in LastErrorCode is now cleared.
                            returned: always
                            type: bool
                            sample: true
                        error_description:
                            description:
                            - More information about the error recorded in LastErrorCode,
                            - and information on any corrective actions that may be taken.
                            returned: always
                            type: str
                        error_methodology:
                            description: Type of error detection and correction supported by this device.
                            returned: always
                            type: str
                        firmware_revision:
                            description: Revision for the disk drive firmware that is assigned by the manufacturer.
                            returned: always
                            type: str
                            sample: 1.0
                        index:
                            description:
                            - Physical drive number of the given drive.
                            - This property is filled by the STORAGE_DEVICE_NUMBER structure returned from the IOCTL_STORAGE_GET_DEVICE_NUMBER control code
                            - A value of 0xffffffff indicates that the given drive does not map to a physical drive.
                            returned: always
                            type: int
                            sample: 0
                        install_date:
                            description: Date and time the object was installed. This property does not need a value to indicate that the object is installed.
                            returned: always
                            type: str
                        interface_type:
                            description: Interface type of physical disk drive.
                            returned: always
                            type: str
                            sample: SCSI
                        last_error_code:
                            description: Last error code reported by the logical device.
                            returned: always
                            type: int
                        manufacturer:
                            description: Name of the disk drive manufacturer.
                            returned: always
                            type: str
                            sample: Seagate
                        max_block_size:
                            description: Maximum block size, in bytes, for media accessed by this device.
                            returned: always
                            type: int
                        max_media_size:
                            description: Maximum media size, in kilobytes, of media supported by this device.
                            returned: always
                            type: int
                        media_loaded:
                            description:
                            - If True, the media for a disk drive is loaded, which means that the device has a readable file system and is accessible.
                            - For fixed disk drives, this property will always be TRUE.
                            returned: always
                            type: bool
                            sample: true
                        media_type:
                            description: Type of media used or accessed by this device.
                            returned: always
                            type: str
                            sample: Fixed hard disk media
                        min_block_size:
                            description: Minimum block size, in bytes, for media accessed by this device.
                            returned: always
                            type: int
                        model:
                            description: Manufacturer's model number of the disk drive.
                            returned: always
                            type: str
                            sample: ST32171W
                        name:
                            description: Label by which the object is known. When subclassed, the property can be overridden to be a key property.
                            returned: always
                            type: str
                            sample: \\\\.\\PHYSICALDRIVE0
                        needs_cleaning:
                            description:
                            - If True, the media access device needs cleaning.
                            - Whether manual or automatic cleaning is possible is indicated in the Capabilities property.
                            returned: always
                            type: bool
                        number_of_media_supported:
                            description:
                            - Maximum number of media which can be supported or inserted
                            - (when the media access device supports multiple individual media).
                            returned: always
                            type: int
                        partitions:
                            description: Number of partitions on this physical disk drive that are recognized by the operating system.
                            returned: always
                            type: int
                            sample: 3
                        pnp_device_id:
                            description: Windows Plug and Play device identifier of the logical device.
                            returned: always
                            type: str
                            sample: "SCSI\\DISK&VEN_VMWARE&PROD_VIRTUAL_DISK\\5&1982005&0&000000"
                        power_management_capabilities:
                            description: Array of the specific power-related capabilities of a logical device.
                            returned: always
                            type: list
                        power_management_supported:
                            description:
                            - If True, the device can be power-managed (can be put into suspend mode, and so on).
                            - The property does not indicate that power management features are currently enabled,
                            - only that the logical device is capable of power management.
                            returned: always
                            type: bool
                        scsi_bus:
                            description: SCSI bus number of the disk drive.
                            returned: always
                            type: int
                            sample: 0
                        scsi_logical_unit:
                            description: SCSI logical unit number (LUN) of the disk drive.
                            returned: always
                            type: int
                            sample: 0
                        scsi_port:
                            description: SCSI port number of the disk drive.
                            returned: always
                            type: int
                            sample: 0
                        scsi_target_id:
                            description: SCSI identifier number of the disk drive.
                            returned: always
                            type: int
                            sample: 0
                        sectors_per_track:
                            description: Number of sectors in each track for this physical disk drive.
                            returned: always
                            type: int
                            sample: 63
                        serial_number:
                            description: Number allocated by the manufacturer to identify the physical media.
                            returned: always
                            type: str
                            sample: 6000c298f34101b38cb2b2508926b9de
                        signature:
                            description: Disk identification. This property can be used to identify a shared resource.
                            returned: always
                            type: int
                        size:
                            description:
                            - Size of the disk drive. It is calculated by multiplying the total number of cylinders, tracks in each cylinder,
                            - sectors in each track, and bytes in each sector.
                            returned: always
                            type: int
                            sample: 53686402560
                        status:
                            description:
                            - Current status of the object. Various operational and nonoperational statuses can be defined.
                            - 'Operational statuses include: "OK", "Degraded", and "Pred Fail"'
                            - (an element, such as a SMART-enabled hard disk drive, may be functioning properly but predicting a failure in the near future).
                            - 'Nonoperational statuses include: "Error", "Starting", "Stopping", and "Service".'
                            - '"Service", could apply during mirror-resilvering of a disk, reload of a user permissions list, or other administrative work.'
                            - Not all such work is online, yet the managed element is neither "OK" nor in one of the other states.
                            returned: always
                            type: str
                            sample: OK
                        status_info:
                            description:
                            - State of the logical device. If this property does not apply to the logical device, the value 5 (Not Applicable) should be used.
                            returned: always
                            type: int
                        system_creation_class_name:
                            description: Value of the scoping computer's CreationClassName property.
                            returned: always
                            type: str
                            sample: Win32_ComputerSystem
                        system_name:
                            description: Name of the scoping system.
                            returned: always
                            type: str
                            sample: WILMAR-TEST-123
                        total_cylinders:
                            description:
                            - Total number of cylinders on the physical disk drive.
                            - 'Note: the value for this property is obtained through extended functions of BIOS interrupt 13h.'
                            - The value may be inaccurate if the drive uses a translation scheme to support high-capacity disk sizes.
                            - Consult the manufacturer for accurate drive specifications.
                            returned: always
                            type: int
                            sample: 6527
                        total_heads:
                            description:
                            - Total number of heads on the disk drive.
                            - 'Note: the value for this property is obtained through extended functions of BIOS interrupt 13h.'
                            - The value may be inaccurate if the drive uses a translation scheme to support high-capacity disk sizes.
                            - Consult the manufacturer for accurate drive specifications.
                            returned: always
                            type: int
                            sample: 255
                        total_sectors:
                            description:
                            - Total number of sectors on the physical disk drive.
                            - 'Note: the value for this property is obtained through extended functions of BIOS interrupt 13h.'
                            - The value may be inaccurate if the drive uses a translation scheme to support high-capacity disk sizes.
                            - Consult the manufacturer for accurate drive specifications.
                            returned: always
                            type: int
                            sample: 104856255
                        total_tracks:
                            description:
                            - Total number of tracks on the physical disk drive.
                            - 'Note: the value for this property is obtained through extended functions of BIOS interrupt 13h.'
                            - The value may be inaccurate if the drive uses a translation scheme to support high-capacity disk sizes.
                            - Consult the manufacturer for accurate drive specifications.
                            returned: always
                            type: int
                            sample: 1664385
                        tracks_per_cylinder:
                            description:
                            - Number of tracks in each cylinder on the physical disk drive.
                            - 'Note: the value for this property is obtained through extended functions of BIOS interrupt 13h.'
                            - The value may be inaccurate if the drive uses a translation scheme to support high-capacity disk sizes.
                            - Consult the manufacturer for accurate drive specifications.
                            returned: always
                            type: int
                            sample: 255
'''
