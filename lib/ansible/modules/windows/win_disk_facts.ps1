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
        ansible_disk = @{
        } 
    }
}

# Search disks
try {
    $disk = Get-Disk
} catch {
    Fail-Json -obj $result -message "Failed to search the disks on the target: $($_.Exception.Message)"
}
if ($disk) {
    [string]$diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
    $result.ansible_facts.ansible_disk.total_disks_found = $diskcount
    $i = 0
    foreach ($disks in $disk) {
        $result.ansible_facts.ansible_disk["disk_$($i)"] += @{}
        $pdisk = Get-PhysicalDisk | Where-Object {
                                                            $_.SerialNumber -eq $disks.SerialNumber
                                                          }
        if ($pdisk) {
            $result.ansible_facts.ansible_disk["disk_$($i)"]["physical_disk)"] += @{}
            #$result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].media_type = $pdisk.MediaType
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].device_id = $pdisk.DeviceId
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].friendly_name = $pdisk.FriendlyName
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].operational_status = $pdisk.OperationalStatus
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].health_status = $pdisk.HealthStatus
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].usage = $pdisk.Usage
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].supported_usages = $pdisk.SupportedUsages
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].spindle_speed = $pdisk.SpindleSpeed
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].can_pool = $pdisk.CanPool
            if ($pdisk.CanPool) {
                $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].cannot_pool_reason = $pdisk.CannotPoolReason
            }   
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].object_id = $pdisk.ObjectId
            $result.ansible_facts.ansible_disk."disk_$($i)"["physical_disk)"].unique_id = $pdisk.UniqueId
        }
        $result.ansible_facts.ansible_disk."disk_$($i)".number = $disks.Number
        $result.ansible_facts.ansible_disk."disk_$($i)".size = "$($Size = $disks.Size / 1GB)$($Size)gb"
        $result.ansible_facts.ansible_disk."disk_$($i)".bus_type = $disks.BusType
        $result.ansible_facts.ansible_disk."disk_$($i)".friendly_name = $disks.FriendlyName
        $result.ansible_facts.ansible_disk."disk_$($i)".partition_style = $disks.PartitionStyle
        $result.ansible_facts.ansible_disk."disk_$($i)".partition_count = $disks.NumberOfPartitions
        $result.ansible_facts.ansible_disk."disk_$($i)".operational_status = $disks.OperationalStatus
        $result.ansible_facts.ansible_disk."disk_$($i)".sector_size = "$($disks.PhysicalSectorSize)byte"
        $result.ansible_facts.ansible_disk."disk_$($i)".read_only = $disks.IsReadOnly
        $result.ansible_facts.ansible_disk."disk_$($i)".bootable = $disks.IsBoot
        $result.ansible_facts.ansible_disk."disk_$($i)".system_disk = $disks.IsSystem
        $result.ansible_facts.ansible_disk."disk_$($i)".clustered = $disks.IsClustered
        $result.ansible_facts.ansible_disk."disk_$($i)".manufacturer = $disks.Manufacturer
        $result.ansible_facts.ansible_disk."disk_$($i)".model = $disks.Model
        $result.ansible_facts.ansible_disk."disk_$($i)".firmware_version = $disks.FirmwareVersion
        $result.ansible_facts.ansible_disk."disk_$($i)".location = $disks.Location
        $result.ansible_facts.ansible_disk."disk_$($i)".serial_number = $disks.SerialNumber
        $result.ansible_facts.ansible_disk."disk_$($i)".unique_id = $disks.UniqueId
        $result.ansible_facts.ansible_disk."disk_$($i)".guid = "$([string]$disks.Guid)"
        $result.ansible_facts.ansible_disk."disk_$($i)".path = $disks.Path
        $part = Get-Partition -DiskNumber $i -ErrorAction SilentlyContinue
        if ($part) {
            $j = 0
            foreach ($parts in $part) {
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"] += @{}
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].type = $parts.Type
                if ($disks.PartitionStyle -eq "GPT") {
                    $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].gpt_type = $parts.GptType
                    $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].no_default_driveletter = $parts.NoDefaultDriveLetter
                } elseif ($disks.PartitionStyle -eq "MBR") {
                    $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].mbr_type = $parts.MbrType
                    $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].active = $parts.IsActive
                }
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].number = $parts.PartitionNumber
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].size = $parts.Size
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].drive_letter = "$([string]$parts.DriveLetter)"
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].transition_state = $parts.TransitionState
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].offset = $parts.Offset             
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].hidden = $parts.IsHidden
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].shadow_copy = $parts.IsShadowCopy
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].guid = "$([string]$parts.Guid)"
                $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"].access_paths = "$([string]$parts.AccessPaths)"
                $vol = Get-Volume -Partition $parts -ErrorAction SilentlyContinue
                if ($vol) {
                    $k = 0
                    foreach ($vols in $vol) {
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"] += @{}
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].size = "$($volSize = $vols.Size / 1GB)$($volSize)gb"
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].size_remaining = "$($volSizeRe = $vols.SizeRemaining / 1GB)$($volSizeRe)gb"
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].type = $vols.FileSystem
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].label = $vols.FileSystemLabel
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].health_status = $vols.HealthStatus
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].drive_type = $vols.DriveType
                        if ([System.Environment]::OSVersion.Version.Major -ge 10) {
                            $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].allocation_unit_size = "$($vols.AllocationUnitSize)byte"
                        } else {
                            $volsPath = ($vols.Path.TrimStart("\\?\")).TrimEnd("\")
                            $BlockSize = (Get-CimInstance -Query "SELECT BlockSize FROM Win32_Volume WHERE DeviceID like '%$volsPath%'" -ErrorAction SilentlyContinue | Select-Object BlockSize).BlockSize
                            $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].allocation_unit_size = "$($BlockSize / 1KB)kb"
                        }
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].object_id = $vols.ObjectId
                        $result.ansible_facts.ansible_disk["disk_$($i)"]["partition_$($j)"]["volume_$($k)"].path = $vols.Path
                        $k++
                    }
                }
                $j++
            }
        }
        $i++
    }
} else {
        $result.ansible_facts.ansible_disk.total_disks_found = "0"
        Fail-Json -obj $result -message "No disks could be found on the target"
}

# Return result
Exit-Json -obj $result
