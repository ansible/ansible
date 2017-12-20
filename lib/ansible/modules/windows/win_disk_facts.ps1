#!powershell

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -OSVersion 6.2
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Create a new result object
$result = @{
    changed = $false
    ansible_facts = @{
        total_disks = 0
        disks = @()
    }
}

# Functions 
function Test-Admin {
        $CurrentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
        $IsAdmin = $CurrentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

        return $IsAdmin
}

# Check admin rights
if (-not (Test-Admin)) {
    $result.Remove("total_disks")
    $result.Remove("disks")
    Fail-Json -obj $result -message "Cmdlet was not started with elevated rights"
}

# Search disks
try {
    $disks = Get-Disk
} catch {
    Fail-Json -obj $result -message "Failed to search the disks on the target: $($_.Exception.Message)"
}
[int32]$diskcount = $disks | Measure-Object | Select-Object  -ExpandProperty Count
$result.ansible_facts.total_disks = $diskcount
foreach ($disk in $disks) {
    $disk_info = @{}
    $pdisk = Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object {
        $_.DeviceId -eq $disk.Number
    }
    if ($pdisk) {
        $disk_info["physical_disk"] += @{
            size = "$($pSize = "{0:N3}" -f ($pdisk.Size / 1GB))$($pSize)GiB"
            allocated_size = "$($pAllocSize = "{0:N3}" -f ($pdisk.AllocatedSize / 1GB))$($pAllocSize)GiB"
            device_id = $pdisk.DeviceId
            friendly_name = $pdisk.FriendlyName
            operational_status = $pdisk.OperationalStatus
            health_status = $pdisk.HealthStatus
            bus_type = $pdisk.BusType
            usage_type = $pdisk.Usage
            supported_usages = $pdisk.SupportedUsages
            spindle_speed = "$($pdisk.SpindleSpeed)rpm"
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
                size = "$($vDSize = "{0:N3}" -f ($vdisk.Size / 1GB))$($vDSize)GiB"
                allocated_size = "$($vDAllocSize = "{0:N3}" -f ($vdisk.AllocatedSize / 1GB))$($vDAllocSize)GiB"
                footprint_on_pool = "$($vDPrint = "{0:N3}" -f ($vdisk.FootprintOnPool / 1GB))$($vDPrint)GiB"
                name = $vdisk.name
                friendly_name = $vdisk.FriendlyName
                operational_status = $vdisk.OperationalStatus
                health_status = $vdisk.HealthStatus
                provisioning_type = $vdisk.ProvisioningType
                allocation_unit_size = "$($vdisk.AllocationUnitSize / 1KB)KiB"
                media_type = $vdisk.MediaType
                parity_layout = $vdisk.ParityLayout
                access = $vdisk.Access
                detached_reason = $vdisk.DetachedReason
                write_cache_size = "$($vdisk.WriteCacheSize)s/byte/bytes/"
                fault_domain_awareness = $vdisk.FaultDomainAwareness
                inter_leave = "$($vDLeave = "{0:N3}" -f ($vdisk.InterLeave / 1KB))$($vDLeave)KiB"
                deduplication_enabled = $vdisk.IsDeduplicationEnabled
                enclosure_aware = $vdisk.IsEnclosureAware
                manual_attach = $vdisk.IsManualAttach
                snapshot = $vdisk.IsSnapshot
                tiered = $vdisk.IsTiered
                physical_sector_size = "$($vdisk.PhysicalSectorSize / 1KB)KiB"
                logical_sector_size = "$($vdisk.LogicalSectorSize)s/byte/bytes/"
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
    $disk_info.number = $disk.Number
    $disk_info.size = "$($disk.Size / 1GB)GiB"
    $disk_info.bus_type = $disk.BusType
    $disk_info.friendly_name = $disk.FriendlyName
    $disk_info.partition_style = $disk.PartitionStyle
    $disk_info.partition_count = $disk.NumberOfPartitions
    $disk_info.operational_status = $disk.OperationalStatus
    $disk_info.sector_size = "$($disk.PhysicalSectorSize)s/byte/bytes/"
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
                size = "$($pSize = "{0:N3}" -f ($part.Size /1GB))$($pSize)GiB"
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
                        size = "$($vSize = "{0:N3}" -f ($vol.Size / 1GB))$($vSize)GiB"
                        size_remaining = "$($vSizeRe = "{0:N3}" -f ($vol.SizeRemaining / 1GB))$($vSizeRe)GiB"
                        type = $vol.FileSystem
                        label = $vol.FileSystemLabel
                        health_status = $vol.HealthStatus
                        drive_type = $vol.DriveType
                        object_id = $vol.ObjectId
                        path = $vol.Path
                    }
                    if ([System.Environment]::OSVersion.Version.Major -ge 10) {
                        $volume_info.allocation_unit_size = "$($vol.AllocationUnitSize /1KB)KiB"
                    } else {
                        $volPath = ($vol.Path.TrimStart("\\?\")).TrimEnd("\")
                        $BlockSize = (Get-CimInstance -Query "SELECT BlockSize FROM Win32_Volume WHERE DeviceID like '%$volPath%'" -ErrorAction SilentlyContinue | Select-Object BlockSize).BlockSize
                        $volume_info.allocation_unit_size = "$($BlockSize / 1KB)KiB"
                    }
                    $partition_info.volumes  += $volume_info
                }
            }
        $disk_info.partitions += $partition_info
        }
    }
    $result.ansible_facts.disks += $disk_info
}

# Return result
Exit-Json -obj $result
