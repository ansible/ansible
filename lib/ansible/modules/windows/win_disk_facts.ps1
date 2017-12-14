#!powershell

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Create a new result object
$result = @{
    changed = $false
    ansible_facts = @{
        ansible_disk = @(
        )
    }
}

# Search disks
if (Get-Command 'Get-Disk') {
    try {
        $disks = Get-Disk
    } catch {
        Fail-Json -obj $result -message "Failed to search the disks on the target: $($_.Exception.Message)"
    }
    if ($disks) {
        [int32]$diskcount = $disks | Measure-Object | Select-Object  -ExpandProperty Count
        $result.ansible_facts.ansible_disk += @{total_disks_found = $diskcount}
        foreach ($disk in $disks) {
            $disk_results = @{}
            $pdisk = Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object {
                $_.DeviceId -eq $disk.Number
            }
            if ($pdisk) {
                $disk_results["physical_disk"] += @{
                    #media_type = $pdisk.MediaType
                    size = "$($pSize = "{0:N3}" -f ($pdisk.Size / 1GB))$($pSize)gb"
                    allocated_size = "$($pAllocSize = "{0:N3}" -f ($pdisk.AllocatedSize / 1GB))$($pAllocSize)gb"
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
                    indication_enabled = "$([string]$pdisk.IsIndicationEnabled)"
                    partial = $pdisk.IsPartial
                    serial_number = $pdisk.SerialNumber
                    object_id = $pdisk.ObjectId
                    unique_id = $pdisk.UniqueId
                }
                if (-not $pdisk.CanPool) {
                    $disk_results.physical_disk.cannot_pool_reason = $pdisk.CannotPoolReason
                }   
                $vdisk = Get-VirtualDisk -PhysicalDisk $pdisk -ErrorAction SilentlyContinue
                if ($vdisk) {
                    $disk_results["virtual_disk"] += @{
                        size = "$($vDSize = "{0:N3}" -f ($vdisk.Size / 1GB))$($vDSize)gb"
                        allocated_size = "$($vDAllocSize = "{0:N3}" -f ($vdisk.AllocatedSize / 1GB))$($vDAllocSize)gb"
                        footprint_on_pool = "$($vDPrint = "{0:N3}" -f ($vdisk.FootprintOnPool / 1GB))$($vDPrint)gb"
                        name = "$([string]$vdisk.name)"
                        friendly_name = $vdisk.FriendlyName
                        operational_status = $vdisk.OperationalStatus
                        health_status = $vdisk.HealthStatus
                        provisioning_type = $vdisk.ProvisioningType
                        allocation_unit_size = "$($vdisk.AllocationUnitSize / 1KB)kb"
                        media_type = $vdisk.MediaType
                        parity_layout = "$([string]$vdisk.ParityLayout)"
                        access = $vdisk.Access
                        detached_reason = $vdisk.DetachedReason
                        write_cache_size = "$($vdisk.WriteCacheSize)byte"
                        fault_domain_awareness = $vdisk.FaultDomainAwareness
                        inter_leave = "$($vDLeave = "{0:N3}" -f ($vdisk.InterLeave / 1KB))$($vDLeave)kb"
                        deduplication_enabled = $vdisk.IsDeduplicationEnabled
                        enclosure_aware = $vdisk.IsEnclosureAware
                        manual_attach = $vdisk.IsManualAttach
                        snapshot = $vdisk.IsSnapshot
                        tiered = $vdisk.IsTiered
                        physical_sector_size = "$($vdisk.PhysicalSectorSize / 1KB)kb"
                        logical_sector_size = "$($vdisk.LogicalSectorSize)byte"
                        available_copies = "$([string]$vdisk.NumberOfAvailableCopies)"
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
            $disk_results.number = $disk.Number
            $disk_results.size = "$($disk.Size / 1GB)gb"
            $disk_results.bus_type = $disk.BusType
            $disk_results.friendly_name = $disk.FriendlyName
            $disk_results.partition_style = $disk.PartitionStyle
            $disk_results.partition_count = $disk.NumberOfPartitions
            $disk_results.operational_status = $disk.OperationalStatus
            $disk_results.sector_size = "$($disk.PhysicalSectorSize)byte"
            $disk_results.read_only = $disk.IsReadOnly
            $disk_results.bootable = $disk.IsBoot
            $disk_results.system_disk = $disk.IsSystem
            $disk_results.clustered = $disk.IsClustered
            $disk_results.manufacturer = $disk.Manufacturer
            $disk_results.model = $disk.Model
            $disk_results.firmware_version = $disk.FirmwareVersion
            $disk_results.location = $disk.Location
            $disk_results.serial_number = $disk.SerialNumber
            $disk_results.unique_id = $disk.UniqueId
            $disk_results.guid = "$([string]$disk.Guid)"
            $disk_results.path = $disk.Path
            $parts = Get-Partition -DiskNumber $($disk.Number) -ErrorAction SilentlyContinue
            if ($parts) {
                $disk_results["partitions"]  += @()
                foreach ($part in $parts) {
                    $partition_results  = @{
                        number = $part.PartitionNumber
                        size = "$($pSize = "{0:N3}" -f ($part.Size /1GB))$($pSize)gb"
                        type = $part.Type
                        drive_letter = "$([string]$part.DriveLetter)"
                        transition_state = $part.TransitionState
                        offset = $part.Offset             
                        hidden = $part.IsHidden
                        shadow_copy = $part.IsShadowCopy
                        guid = "$([string]$part.Guid)"
                        access_paths = "$([string]$part.AccessPaths)"
                    }
                    if ($disks.PartitionStyle -eq "GPT") {
                        $partition_results.gpt_type = $part.GptType
                        $partition_results.no_default_driveletter = $part.NoDefaultDriveLetter
                    } elseif ($disks.PartitionStyle -eq "MBR") {
                        $partition_results.mbr_type = $part.MbrType
                        $partition_results.active = $part.IsActive
                    }
                    $vols = Get-Volume -Partition $part -ErrorAction SilentlyContinue
                    if ($vols) {
                        $partition_results["volumes"]  += @()
                        foreach ($vol in $vols) {
                            $volume_results  = @{
                                size = "$($vSize = "{0:N3}" -f ($vol.Size / 1GB))$($vSize)gb"
                                size_remaining = "$($vSizeRe = "{0:N3}" -f ($vol.SizeRemaining / 1GB))$($vSizeRe)gb"
                                type = $vol.FileSystem
                                label = $vol.FileSystemLabel
                                health_status = $vol.HealthStatus
                                drive_type = $vol.DriveType
                                object_id = $vol.ObjectId
                                path = $vol.Path
                            }
                            if ([System.Environment]::OSVersion.Version.Major -ge 10) {
                                $volume_results.allocation_unit_size = "$($vol.AllocationUnitSize /1KB)kb"
                            } else {
                                $volPath = ($vol.Path.TrimStart("\\?\")).TrimEnd("\")
                                $BlockSize = (Get-CimInstance -Query "SELECT BlockSize FROM Win32_Volume WHERE DeviceID like '%$volPath%'" -ErrorAction SilentlyContinue | Select-Object BlockSize).BlockSize
                                $volume_results.allocation_unit_size = "$($BlockSize / 1KB)kb"
                            }
                            $partition_results.volumes  += $volume_results
                        }
                    }
                $disk_results.partitions += $partition_results
                }
            }
            $result.ansible_facts.ansible_disk += $disk_results
        }
    } else {
            $result.ansible_facts.ansible_disk.total_disks_found = "0"
            Fail-Json -obj $result -message "No disks could be found on the target"
    }
} else {
    Fail-Json -obj $result -message "The required PowerShell Cmdlets of module Storage (e.g. Get-Disk) are not available in your PowerShell version $($host.Version.Major).$($host.Version.Minor)"
}

# Return result
Exit-Json -obj $result
