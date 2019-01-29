#!powershell

# Copyright: (c) 2018, Varun Chopra (@chopraaa) <v@chopraaa.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.2

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"

$spec = @{
    options = @{
        state = @{ type = "str"; choices = "absent", "present"; default = "present" }
        drive_letter = @{ type = "str" }
        disk_number = @{ type = "int" }
        partition_number = @{ type = "int" }
        partition_size = @{ type = "str" }
        read_only = @{ type = "bool" }
        active = @{ type = "bool" }
        hidden = @{ type = "bool" }
        offline = @{ type = "bool" }
        mbr_type = @{ type = "str"; choices = "fat12", "fat16", "extended", "huge", "ifs", "fat32" }
        gpt_type = @{ type = "str"; choices = "system_partition", "microsoft_reserved", "basic_data", "microsoft_recovery" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$state = $module.Params.state
$drive_letter = $module.Params.drive_letter
$disk_number = $module.Params.disk_number
$partition_number = $module.Params.partition_number
$partition_size = $module.Params.partition_size
$read_only = $module.Params.read_only
$active = $module.Params.active
$hidden = $module.Params.hidden
$offline = $module.Params.offline
$mbr_type = $module.Params.mbr_type
$gpt_type = $module.Params.gpt_type

$size_is_maximum = $false
$ansible_partition = $false
$ansible_partition_size = $null
$partition_style = $null

$gpt_styles = @{
    system_partition = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
    microsoft_reserved = "e3c9e316-0b5c-4db8-817d-f92df00215ae"
    basic_data = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"
    microsoft_recovery = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
}

$mbr_styles = @{
    fat12 = 1
    fat16 = 4
    extended = 5
    huge = 6
    ifs = 7
    fat32 = 12
}

function Convert-SizeToBytes {
    param(
        $Size,
        $Units
    )

    switch ($Units) {
        "B"   { return $Size }
        "KB"  { return 1000 * $Size }
        "KiB" { return 1024 * $Size }
        "MB"  { return [Math]::Pow(1000, 2) * $Size }
        "MiB" { return [Math]::Pow(1024, 2) * $Size }
        "GB"  { return [Math]::Pow(1000, 3) * $Size }
        "GiB" { return [Math]::Pow(1024, 3) * $Size }
        "TB"  { return [Math]::Pow(1000, 4) * $Size }
        "TiB" { return [Math]::Pow(1024, 4) * $Size }
    }
}

if ($null -ne $partition_size) {
    if ($partition_size -eq -1) {
        $size_is_maximum = $true
    }
    elseif ($partition_size -match '^(?<Size>[0-9]+)[ ]*(?<Units>b|kb|kib|mb|mib|gb|gib|tb|tib)$') {
        $ansible_partition_size = Convert-SizeToBytes -Size $Matches.Size -Units $Matches.Units
    }
    else {
        $module.FailJson("Invalid partition size. B, KB, KiB, MB, MiB, GB, GiB, TB, TiB are valid partition size units")
    }
}

# If partition_exists, we can change or delete it; otherwise we only need the disk to create a new partition
if ($null -ne $disk_number -and $null -ne $partition_number) {
    $ansible_partition = Get-Partition -DiskNumber $disk_number -PartitionNumber $partition_number -ErrorAction SilentlyContinue
}
# Check if drive_letter is either auto-assigned or a character from A-Z
elseif ($drive_letter -and -not ($disk_number -and $partition_number)) {
    if ($drive_letter -eq "auto" -or $drive_letter -match "^[a-zA-Z]$") {
        $ansible_partition = Get-Partition -DriveLetter $drive_letter -ErrorAction SilentlyContinue
    }
    else {
        $module.FailJson("Incorrect usage of drive_letter: specify a drive letter from A-Z or use 'auto' to automatically assign a drive letter")
    }
}
elseif ($disk_number) {
    try {
        Get-Disk -Number $disk_number | Out-Null
    } catch {
        $module.FailJson("Specified disk does not exist")
    }
}
else {
    $module.FailJson("You must provide disk_number, partition_number")
}

# Partition can't have two partition styles
if ($null -ne $gpt_type -and $null -ne $mbr_type) {
    $module.FailJson("Cannot specify both GPT and MBR partition styles. Check which partition style is supported by the disk")
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

    $parameters = @{
        DiskNumber = $DiskNumber
    }

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

    try {
        $new_partition = New-Partition @parameters
    } catch {
        $module.FailJson("Unable to create a new partition: $($_.Exception.Message)", $_)
    }

    return $new_partition
}


function Set-AnsiblePartitionState {
    param(
        $hidden,
        $read_only,
        $active,
        $partition
    )

    $parameters = @{
        DiskNumber = $partition.DiskNumber
        PartitionNumber = $partition.PartitionNumber
    }

    if ($hidden -NotIn ($null, $partition.IsHidden)) {
        $parameters.Add("IsHidden", $hidden)
    }

    if ($read_only -NotIn ($null, $partition.IsReadOnly)) {
        $parameters.Add("IsReadOnly", $read_only)
    }

    if ($active -NotIn ($null, $partition.IsActive)) {
        $parameters.Add("IsActive", $active)
    }

    try {
        Set-Partition @parameters
    } catch {
        $module.FailJson("Error changing state of partition: $($_.Exception.Message)", $_)
    }
}


if ($ansible_partition) {
    if ($state -eq "absent") {
        try {
            Remove-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -Confirm:$false -WhatIf:$module.CheckMode
        } catch {
            $module.FailJson("There was an error removing the partition: $($_.Exception.Message)", $_)
        }
        $module.Result.changed = $true
    }
    else {

        if ($null -ne $gpt_type -and $gpt_styles.$gpt_type -ne $partition.GptType) {
            $module.FailJson("gpt_type is not a valid parameter for existing partitions")
        }
        if ($null -ne $mbr_type -and $mbr_styles.$mbr_type -ne $partition.MbrType) {
            $module.FailJson("mbr_type is not a valid parameter for existing partitions")
        }

        if ($partition_size) {
            try {
                $max_supported_size = (Get-PartitionSupportedSize -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber).SizeMax
            } catch {
                $module.FailJson("Unable to get maximum supported partition size: $($_.Exception.Message)", $_)
            }
            if ($size_is_maximum) {
                $ansible_partition_size = $max_supported_size
            }
            if ($ansible_partition_size -ne $ansible_partition.Size -and $ansible_partition_size -le $max_supported_size) {
                if ($ansible_partition.IsReadOnly) {
                    $module.FailJson("Unable to resize partition: Partition is read only")
                } else {
                    try {
                        Resize-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -Size $ansible_partition_size -WhatIf:$module.CheckMode
                    } catch {
                        $module.FailJson("Unable to change partition size: $($_.Exception.Message)", $_)
                    }
                    $module.Result.changed = $true
                }
            } elseif ($ansible_partition_size -gt $max_supported_size) {
                $module.FailJson("Specified partition size exceeds size supported by the partition")
            }
        }

        if ($drive_letter -NotIn ("auto", $null, $ansible_partition.DriveLetter)) {
            if (-not $module.CheckMode) {
                try {
                    Set-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -NewDriveLetter $drive_letter
                } catch {
                    $module.FailJson("Unable to change drive letter: $($_.Exception.Message)", $_)
                }
            }
            $module.Result.changed = $true
        }
    }
}
else {
    if ($state -eq "present") {
        if ($null -eq $disk_number) {
            $module.FailJson("Missing required parameter: disk_number")
        }
        if ($null -eq $ansible_partition_size -and -not $size_is_maximum){
            $module.FailJson("Missing required parameter: partition_size")
        }
        if (-not $size_is_maximum) {
            try {
                $max_supported_size = (Get-Disk -Number $disk_number).LargestFreeExtent
            } catch {
                $module.FailJson("Unable to get maximum size supported by disk: $($_.Exception.Message)", $_)
            }

            if ($ansible_partition_size -gt $max_supported_size) {
                $module.FailJson("Partition size is not supported by disk. Use partition_size: -1 to get maximum size")
            }
        }

        $supp_part_type = (Get-Disk -Number $disk_number).PartitionStyle
        if ($null -ne $mbr_type) {
            if ($supp_part_type -eq "MBR" -and $mbr_styles.ContainsKey($mbr_type)) {
                $partition_style = $mbr_styles.$mbr_type
            } else {
                $module.FailJson("Incorrect partition style specified")
            }
        }
        if ($null -ne $gpt_type) {
            if ($supp_part_type -eq "GPT" -and $gpt_styles.ContainsKey($gpt_type)) {
                $partition_style = $gpt_styles.$gpt_type
            } else {
                $module.FailJson("Incorrect partition style specified")
            }
        }

        if (-not $module.CheckMode) {
            $ansible_partition = New-AnsiblePartition -DiskNumber $disk_number -Letter $drive_letter -SizeMax $size_is_maximum -Size $ansible_partition_size -MbrType $mbr_type -GptType $gpt_type -Style $partition_style
        }
        $module.Result.changed = $true
    }
}

if ($state -eq "present" -and $ansible_partition) {
    if ($offline -NotIn ($null, $ansible_partition.IsOffline)) {
        if (-not $module.CheckMode) {
            try {
                Set-Partition -DiskNumber $ansible_partition.DiskNumber -PartitionNumber $ansible_partition.PartitionNumber -IsOffline $offline
            } catch {
                $module.FailJson("Error setting partition offline: $($_.Exception.Message)", $_)
            }
        }
        $module.Result.changed = $true
    }

    if ($hidden -NotIn ($null, $ansible_partition.IsHidden) -or $read_only -NotIn ($null, $ansible_partition.IsReadOnly) -or $active -NotIn ($null, $ansible_partition.IsActive)) {
        if (-not $module.CheckMode) {
            Set-AnsiblePartitionState -hidden $hidden -read_only $read_only -active $active -partition $ansible_partition
        }
        $module.Result.changed = $true
    }
}

$module.ExitJson()
