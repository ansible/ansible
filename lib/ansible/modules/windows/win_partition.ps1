#!powershell

# Copyright: (c) 2018, Varun Chopra (@chopraaa)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -failifempty $false -default "present" -validateset "absent", "present"
$drive_letter = Get-AnsibleParam -obj $params -name "drive_letter" -type "str" -failifempty $false
$disk_number = Get-AnsibleParam -obj $params -name "disk_number" -type "int" -failifempty $false
$partition_number = Get-AnsibleParam -obj $params -name "partition_number" -type "int" -failifempty $false
$partition_size = Get-AnsibleParam -obj $params -name "partition_size" -type "int" -failifempty $false
$read_only = Get-AnsibleParam -obj $params -name "read_only" -type "bool" -failifempty $false
$active = Get-AnsibleParam -obj $params -name "active" -type "bool" -failifempty $false
$hidden = Get-AnsibleParam -obj $params -name "hidden" -type "bool" -failifempty $false
$offline = Get-AnsibleParam -obj $params -name "offline" -type "bool" -failifempty $false
$mbr_type = Get-AnsibleParam -obj $params -name "mbr_type" -type "str" -failifempty $false -validateset "FAT12", "FAT16", "Extended", "Huge", "IFS", "FAT32"
$gpt_type = Get-AnsibleParam -obj $params -name "gpt_type" -type "str" -failifempty $false -validateset "SystemPartition", "MicrosoftReserved", "BasicData", "MicrosoftRecovery"

$result = @{
    changed = $false
}

$size_is_maximum = $false
$ansible_partition = $false
$ansible_partition_size = $null
$partition_style = $null

$gpt_styles = @{
    SystemPartition = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
    MicrosoftReserved = "e3c9e316-0b5c-4db8-817d-f92df00215ae"
    BasicData = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"
    MicrosoftRecovery = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
}

$mbr_styles = @{
    FAT12 = 1
    FAT16 = 4
    Extended = 5
    Huge = 6
    IFS = 7
    FAT32 = 12
}

# We're allowing postitive and -1 partition sizes; -1 is maximum possible size
if ($partition_size -ne $null) {
    if ($partition_size -lt -1 -or $partition_size -eq 0) {
        Fail-Json -obj $result -message "Please enter positive partition sizes. Use -1 for maximum size."
    }
    elseif ($partition_size -eq -1) {
        $size_is_maximum = $true
    }
    else {
        $ansible_partition_size = [int64] $partition_size * 1GB
    }
}

# If partition_exists, we can change or delete it; otherwise we only need the disk to create a new partition
if ($disk_number -and $partition_number) {
    $ansible_partition = Get-Partition -DiskNumber $disk_number -PartitionNumber $partition_number -ErrorAction SilentlyContinue
}
# Check if drive_letter is either auto-assigned or a character from A-Z
elseif ($drive_letter -and -not ($disk_number -and $partition_number)) {
    if ($drive_letter -eq "auto" -or $drive_letter -match "^[a-zA-Z]$") {
        $ansible_partition = Get-Partition -DriveLetter $drive_letter -ErrorAction SilentlyContinue
    }
    else {
        Fail-Json -obj $result -message "Incorrect usage of drive_letter"
    }
}
elseif ($disk_number) {
    try {
        Get-Disk -Number $disk_number
    } catch {
        Fail-Json -obj $result -message "Specified disk does not exist"
    }
}
else {
    Fail-Json -obj $result -message "You must provide disk_number, partition_number"
}

function New-AnsiblePartition {
    param(
        $DiskNumber,
        $Letter,
        $SizeMax,
        $Size,
        $MbrType,
        $GptType,
        $Style
    )

    $parameters = @{}

    $parameters.Add("DiskNumber", $DiskNumber)

    if ($null -ne $Letter) {
        switch ($Letter) {
            "auto" {
                $parameters.Add("AssignDriveLetter", $True)
            }
            default {
                $parameters.Add("DriveLetter", $Letter)
            }
        }
    }

    switch ($SizeMax) {
        $True {
            $parameters.Add("UseMaximumSize", $True)
        }
        $False {
            $parameters.Add("Size", $Size)
        }
    }

    if ($null -ne $MbrType) {
        $parameters.Add("MbrType", $Style)
    }

    if ($null -ne $GptType) {
        $parameters.Add("GptType", $Style)
    }

    return $parameters
}


function Set-AnsiblePartitionState {
    param(
        $hidden,
        $read_only,
        $active,
        $partition
    )

    $parameters = @{}

    $parameters.Add("DiskNumber", $partition.DiskNumber)
    $parameters.Add("PartitionNumber", $partition.PartitionNumber)

    if ($hidden -NotIn ($null, $partition.IsHidden)) {
        $parameters.Add("IsHidden", $hidden)
    }

    if ($read_only -NotIn ($null, $partition.IsReadOnly)) {
        $parameters.Add("IsReadOnly", $read_only)
    }

    if ($active -NotIn ($null, $partition.IsActive)) {
        $parameters.Add("IsActive", $active)
    }

    return $parameters
}


if ($ansible_partition) {
    if ($state -eq "absent") {
        try {
            Remove-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -Confirm:$false -WhatIf:$check_mode
        } catch {
            Fail-Json -obj $result -message "There was an error removing the partition: $($_.Exception.Message)"
        }
        $result.changed = $true
    }
    else {

        if ($gpt_type -ne $null -or $mbr_type -ne $null) {
            Fail-Json -obj $result -message "gpt_type and mbr_type are not valid parameters for existing partitions"
        }

        if ($partition_size) {
            try {
                $max_supported_size = (Get-PartitionSupportedSize -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber).SizeMax
            } catch {
                Fail-Json -obj $result -message "Unable to get maximum supported partition size: $($_.Exception.Message)"
            }
            if ($size_is_maximum) {
                $ansible_partition_size = $max_supported_size
            }
            if ($ansible_partition_size -ne $ansible_partition.Size -and $ansible_partition_size -le $max_supported_size) {
                if ($ansible_partition.IsReadOnly) {
                    Fail-Json -obj $result -message "Unable to resize partition: Partition is read only"
                } else {
                    try {
                        Resize-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -Size $ansible_partition_size -WhatIf:$check_mode
                    } catch {
                        Fail-Json -obj $result -message "Unable to change partition size: $($_.Exception.Message)"
                    }                    
                    $result.changed = $true
                }
            } elseif ($ansible_partition_size -gt $max_supported_size) {
                Fail-Json -obj $result -message "Specified partition size exceeds size supported by partition"
            }
        }

        if ($drive_letter -NotIn ("auto", $null, $ansible_partition.DriveLetter)) {
            if (-not $check_mode) {
                try {
                    Set-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -NewDriveLetter $drive_letter
                } catch {
                    Fail-Json -obj $result -message "Unable to change drive letter: $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    }
}
else {
    if ($state -eq "present") {
        if ($disk_number -eq $null) {
            Fail-Json -obj $result -message "Missing required parameter: disk_number"
        }
        if ($ansible_partition_size -eq $null -and -not $size_is_maximum){
            Fail-Json -obj $result -message "Missing required parameter: partition_size"
        }
        if (-not $size_is_maximum) {
            try {
                $max_supported_size = (Get-Disk -Number $disk_number).LargestFreeExtent
            } catch {
                Fail-Json -obj $result -message "Unable to get maximum size supported by disk: $($_.Exception.Message)"
            }

            if ($ansible_partition_size -gt $max_supported_size) {
                Fail-Json -obj $result -message "Partition size is not supported by disk. Use partition_size: -1 to get maximum size"
            }
        }

        $supp_part_type = (Get-Disk -Number $disk_number).PartitionStyle
        if ($mbr_type -ne $null) {
            if ($supp_part_type -eq "MBR" -and $mbr_styles.ContainsKey($mbr_type)) {
                $partition_style = $mbr_styles.$mbr_type
            } else {
                Fail-Json -obj $result -message "Incorrect partition style specified"
            }
        }
        if ($gpt_type -ne $null) {
            if ($supp_part_type -eq "GPT" -and $gpt_styles.ContainsKey($gpt_type)) {
                $partition_style = $gpt_styles.$gpt_type
            } else {
                Fail-Json -obj $result -message "Incorrect partition style specified"
            }
        }

        $partition_params = New-AnsiblePartition -DiskNumber $disk_number -Letter $drive_letter -SizeMax $size_is_maximum -Size $ansible_partition_size -MbrType $mbr_type -GptType $gpt_type -Style $partition_style

        if (-not $check_mode) {
            try {
                $ansible_partition = New-Partition @partition_params
            } catch {
                Fail-Json -obj $result -message "Unable to create a new partition: $($_.Exception.Message)"
            }
        }
        $result.changed = $true
    }
}

if ($state -eq "present" -and $ansible_partition) {
    if ($offline -NotIn ($null, $ansible_partition.IsOffline)) {
        if (-not $check_mode) {
            try {
                Set-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -IsOffline $offline
            } catch {
                Fail-Json -obj $result -message "Error setting partition offline: $($_.Exception.Message)"
            }
        }
        $result.changed = $true
    }

    if ($hidden -NotIn ($null, $ansible_partition.IsHidden) -or $read_only -NotIn ($null, $ansible_partition.IsReadOnly) -or $active -NotIn ($null, $ansible_partition.IsActive)) {
        if (-not $check_mode) {
            $partition_state_params = Set-AnsiblePartitionState -hidden $hidden -read_only $read_only -active $active -partition $ansible_partition
            try {
                Set-Partition @partition_state_params
            } catch {
                Fail-Json -obj $result -message "Error changing state of partition: $($_.Exception.Message)"
            }
        }
        $result.changed = $true
    }
}

Exit-Json -obj $result