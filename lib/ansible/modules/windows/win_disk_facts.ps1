#!powershell

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -OSVersion 6.2

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Functions
function Test-Admin {
    $CurrentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    $IsAdmin = $CurrentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

    return $IsAdmin
}

# Check admin rights
if (-not (Test-Admin)) {
    Fail-Json -obj @{} -message "Module was not started with elevated rights"
}

# Create a new result object
$result = @{
    changed = $false
    ansible_facts = @{
        ansible_disks = @()
    }
}

# Search disks
try {
    $disks = Get-Disk
} catch {
    Fail-Json -obj $result -message "Failed to search the disks on the target: $($_.Exception.Message)"
}
foreach ($disk in $disks) {
    $disk_info = @{}
    $pdisk = Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object {
        $_.DeviceId -eq $disk.Number
    }
    if ($pdisk) {
        $disk_info["physical_disk"] += @{
            size = $pdisk.Size
            allocated_size = $pdisk.AllocatedSize
            device_id = $pdisk.DeviceId
            friendly_name = $pdisk.FriendlyName
            operational_status = $pdisk.OperationalStatus
            health_status = $pdisk.HealthStatus
            bus_type = $pdisk.BusType
            usage_type = $pdisk.Usage
            supported_usages = $pdisk.SupportedUsages
            spindle_speed = $pdisk.SpindleSpeed
            firmware_version = $pdisk.FirmwareVersion
            physical_location = $pdisk.PhysicalLocation
            manufacturer = $pdisk.Manufacturer
            model = $pdisk.Model
            can_pool = $pdisk.CanPool
            indication_enabled = $pdisk.IsIndicationEnabled
            partial = $pdisk.IsPartial
            serial_number = $pdisk.SerialNumber
            object_id = $pdisk.ObjectId
            unique_id = $pdisk.UniqueId
        }
        if ([single]"$([System.Environment]::OSVersion.Version.Major).$([System.Environment]::OSVersion.Version.Minor)" -ge 6.3) {
            $disk_info.physical_disk.media_type = $pdisk.MediaType
        }
        if (-not $pdisk.CanPool) {
            $disk_info.physical_disk.cannot_pool_reason = $pdisk.CannotPoolReason
        }
        $vdisk = Get-VirtualDisk -PhysicalDisk $pdisk -ErrorAction SilentlyContinue
        if ($vdisk) {
            $disk_info["virtual_disk"] += @{
                size = $vdisk.Size
                allocated_size = $vdisk.AllocatedSize
                footprint_on_pool = $vdisk.FootprintOnPool
                name = $vdisk.name
                friendly_name = $vdisk.FriendlyName
                operational_status = $vdisk.OperationalStatus
                health_status = $vdisk.HealthStatus
                provisioning_type = $vdisk.ProvisioningType
                allocation_unit_size = $vdisk.AllocationUnitSize
                media_type = $vdisk.MediaType
                parity_layout = $vdisk.ParityLayout
                access = $vdisk.Access
                detached_reason = $vdisk.DetachedReason
                write_cache_size = $vdisk.WriteCacheSize
                fault_domain_awareness = $vdisk.FaultDomainAwareness
                inter_leave = $vdisk.InterLeave
                deduplication_enabled = $vdisk.IsDeduplicationEnabled
                enclosure_aware = $vdisk.IsEnclosureAware
                manual_attach = $vdisk.IsManualAttach
                snapshot = $vdisk.IsSnapshot
                tiered = $vdisk.IsTiered
                physical_sector_size = $vdisk.PhysicalSectorSize
                logical_sector_size = $vdisk.LogicalSectorSize
                available_copies = $vdisk.NumberOfAvailableCopies
                columns = $vdisk.NumberOfColumns
                groups = $vdisk.NumberOfGroups
                physical_disk_redundancy = $vdisk.PhysicalDiskRedundancy
                read_cache_size = $vdisk.ReadCacheSize
                request_no_spof = $vdisk.RequestNoSinglePointOfFailure
                resiliency_setting_name = $vdisk.ResiliencySettingName
                object_id = $vdisk.ObjectId
                unique_id_format = $vdisk.UniqueIdFormat
                unique_id = $vdisk.UniqueId
            }
        }
    }
    $win32_disk_drive = Get-CimInstance -ClassName Win32_DiskDrive -ErrorAction SilentlyContinue | Where-Object {
        if ($_.SerialNumber) {
            $_.SerialNumber -eq $disk.SerialNumber
        } elseif ($disk.UniqueIdFormat -eq 'Vendor Specific') {
            $_.PNPDeviceID -eq $disk.UniqueId.split(':')[0]
        }
    }
    if ($win32_disk_drive) {
        $disk_info["win32_disk_drive"] += @{
            availability=$win32_disk_drive.Availability
            bytes_per_sector=$win32_disk_drive.BytesPerSector
            capabilities=$win32_disk_drive.Capabilities
            capability_descriptions=$win32_disk_drive.CapabilityDescriptions
            caption=$win32_disk_drive.Caption
            compression_method=$win32_disk_drive.CompressionMethod
            config_manager_error_code=$win32_disk_drive.ConfigManagerErrorCode
            config_manager_user_config=$win32_disk_drive.ConfigManagerUserConfig
            creation_class_name=$win32_disk_drive.CreationClassName
            default_block_size=$win32_disk_drive.DefaultBlockSize
            description=$win32_disk_drive.Description
            device_id=$win32_disk_drive.DeviceID
            error_cleared=$win32_disk_drive.ErrorCleared
            error_description=$win32_disk_drive.ErrorDescription
            error_methodology=$win32_disk_drive.ErrorMethodology
            firmware_revision=$win32_disk_drive.FirmwareRevision
            index=$win32_disk_drive.Index
            install_date=$win32_disk_drive.InstallDate
            interface_type=$win32_disk_drive.InterfaceType
            last_error_code=$win32_disk_drive.LastErrorCode
            manufacturer=$win32_disk_drive.Manufacturer
            max_block_size=$win32_disk_drive.MaxBlockSize
            max_media_size=$win32_disk_drive.MaxMediaSize
            media_loaded=$win32_disk_drive.MediaLoaded
            media_type=$win32_disk_drive.MediaType
            min_block_size=$win32_disk_drive.MinBlockSize
            model=$win32_disk_drive.Model
            name=$win32_disk_drive.Name
            needs_cleaning=$win32_disk_drive.NeedsCleaning
            number_of_media_supported=$win32_disk_drive.NumberOfMediaSupported
            partitions=$win32_disk_drive.Partitions
            pnp_device_id=$win32_disk_drive.PNPDeviceID
            power_management_capabilities=$win32_disk_drive.PowerManagementCapabilities
            power_management_supported=$win32_disk_drive.PowerManagementSupported
            scsi_bus=$win32_disk_drive.SCSIBus
            scsi_logical_unit=$win32_disk_drive.SCSILogicalUnit
            scsi_port=$win32_disk_drive.SCSIPort
            scsi_target_id=$win32_disk_drive.SCSITargetId
            sectors_per_track=$win32_disk_drive.SectorsPerTrack
            serial_number=$win32_disk_drive.SerialNumber
            signature=$win32_disk_drive.Signature
            size=$win32_disk_drive.Size
            status=$win32_disk_drive.status
            status_info=$win32_disk_drive.StatusInfo
            system_creation_class_name=$win32_disk_drive.SystemCreationClassName
            system_name=$win32_disk_drive.SystemName
            total_cylinders=$win32_disk_drive.TotalCylinders
            total_heads=$win32_disk_drive.TotalHeads
            total_sectors=$win32_disk_drive.TotalSectors
            total_tracks=$win32_disk_drive.TotalTracks
            tracks_per_cylinder=$win32_disk_drive.TracksPerCylinder
        }
    }
    $disk_info.number = $disk.Number
    $disk_info.size = $disk.Size
    $disk_info.bus_type = $disk.BusType
    $disk_info.friendly_name = $disk.FriendlyName
    $disk_info.partition_style = $disk.PartitionStyle
    $disk_info.partition_count = $disk.NumberOfPartitions
    $disk_info.operational_status = $disk.OperationalStatus
    $disk_info.sector_size = $disk.PhysicalSectorSize
    $disk_info.read_only = $disk.IsReadOnly
    $disk_info.bootable = $disk.IsBoot
    $disk_info.system_disk = $disk.IsSystem
    $disk_info.clustered = $disk.IsClustered
    $disk_info.manufacturer = $disk.Manufacturer
    $disk_info.model = $disk.Model
    $disk_info.firmware_version = $disk.FirmwareVersion
    $disk_info.location = $disk.Location
    $disk_info.serial_number = $disk.SerialNumber
    $disk_info.unique_id = $disk.UniqueId
    $disk_info.guid = $disk.Guid
    $disk_info.path = $disk.Path
    $parts = Get-Partition -DiskNumber $($disk.Number) -ErrorAction SilentlyContinue
    if ($parts) {
        $disk_info["partitions"]  += @()
        foreach ($part in $parts) {
            $partition_info  = @{
                number = $part.PartitionNumber
                size = $part.Size
                type = $part.Type
                drive_letter = $part.DriveLetter
                transition_state = $part.TransitionState
                offset = $part.Offset
                hidden = $part.IsHidden
                shadow_copy = $part.IsShadowCopy
                guid = $part.Guid
                access_paths = $part.AccessPaths
            }
            if ($disks.PartitionStyle -eq "GPT") {
                $partition_info.gpt_type = $part.GptType
                $partition_info.no_default_driveletter = $part.NoDefaultDriveLetter
            } elseif ($disks.PartitionStyle -eq "MBR") {
                $partition_info.mbr_type = $part.MbrType
                $partition_info.active = $part.IsActive
            }
            $vols = Get-Volume -Partition $part -ErrorAction SilentlyContinue
            if ($vols) {
                $partition_info["volumes"]  += @()
                foreach ($vol in $vols) {
                    $volume_info  = @{
                        size = $vol.Size
                        size_remaining = $vol.SizeRemaining
                        type = $vol.FileSystem
                        label = $vol.FileSystemLabel
                        health_status = $vol.HealthStatus
                        drive_type = $vol.DriveType
                        object_id = $vol.ObjectId
                        path = $vol.Path
                    }
                    if ([System.Environment]::OSVersion.Version.Major -ge 10) {
                        $volume_info.allocation_unit_size = $vol.AllocationUnitSize
                    } else {
                        $volPath = ($vol.Path.TrimStart("\\?\")).TrimEnd("\")
                        $BlockSize = (Get-CimInstance -Query "SELECT BlockSize FROM Win32_Volume WHERE DeviceID like '%$volPath%'" -ErrorAction SilentlyContinue | Select-Object BlockSize).BlockSize
                        $volume_info.allocation_unit_size = $BlockSize
                    }
                    $partition_info.volumes  += $volume_info
                }
            }
        $disk_info.partitions += $partition_info
        }
    }
    $result.ansible_facts.ansible_disks += $disk_info
}

# Sort by disk number property
$result.ansible_facts.ansible_disks = @() + ($result.ansible_facts.ansible_disks | Sort-Object -Property {$_.Number})

# Return result
Exit-Json -obj $result
