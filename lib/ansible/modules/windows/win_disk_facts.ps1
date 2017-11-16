#!powershell
# This file is part of Ansible

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
        $result.ansible_facts.ansible_disk."disk_$($i)".number = "$([string]$disks.Number)"
        $result.ansible_facts.ansible_disk."disk_$($i)".size = "$($Size = $disks.Size / 1GB)$($Size)gb"
        $result.ansible_facts.ansible_disk."disk_$($i)".partition_style = "$([string]$DPartStyle = $disks.PartitionStyle)$DPartStyle"
        $result.ansible_facts.ansible_disk."disk_$($i)".partition_count = "$([string]$disks.NumberOfPartitions)"
        $result.ansible_facts.ansible_disk."disk_$($i)".operational_status = "$([string]$DOperSt = $disks.OperationalStatus)$DOperSt"
        $result.ansible_facts.ansible_disk."disk_$($i)".sector_size = "$([string]$disks.PhysicalSectorSize)byte"
        $result.ansible_facts.ansible_disk."disk_$($i)".read_only = "$([string]$DROState = $disks.IsReadOnly)$DROState"
        $result.ansible_facts.ansible_disk."disk_$($i)".boot_disk = "$([string]$BootState = $disks.IsBoot)$BootState"
        $result.ansible_facts.ansible_disk."disk_$($i)".system_disk = "$([string]$SystemState = $disks.IsSystem)$SystemState"
        $result.ansible_facts.ansible_disk."disk_$($i)".scale_out = "$([string]$ScaleOutState = $disks.IsScaleOut)$ScaleOutState"
        $result.ansible_facts.ansible_disk."disk_$($i)".highly_available = "$([string]$HiglyAvailState = $disks.IsHighlyAvailable)$HiglyAvailState"
        $result.ansible_facts.ansible_disk."disk_$($i)".clustered = "$([string]$ClusteredState = $disks.IsClustered)$ClusteredState"
        $result.ansible_facts.ansible_disk."disk_$($i)".model = "$([string]$disks.Model)"
        $result.ansible_facts.ansible_disk."disk_$($i)".firmware_version = "$([string]$disks.FirmwareVersion)"
        $result.ansible_facts.ansible_disk."disk_$($i)".location = "$([string]$disks.Location)"
        $result.ansible_facts.ansible_disk."disk_$($i)".serial_number = "$([string]$disks.SerialNumber)"
        $result.ansible_facts.ansible_disk."disk_$($i)".unique_id = "$([string]$disks.UniqueId)"    
        $result.ansible_facts.ansible_disk."disk_$($i)".guid = "$([string]$disks.Guid)"


        
        $i++
    }
} else {
        $result.ansible_facts.ansible_disk.total_disks_found = "0"
        Fail-Json -obj $result -message "No disks could be found on the target"
}

# Return result
Exit-Json -obj $result
