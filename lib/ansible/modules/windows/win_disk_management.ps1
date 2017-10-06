#!powershell
#
# Copyright 2017, Marc Tschapek <marc.tschapek@outlook.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

# Define script environment variables
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

# Parse arguments
$params = Parse-Args -arguments $args -supports_check_mode $true

## Extract each attributes into a variable
# Find attributes
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$Logging = Get-AnsibleParam -obj $params -name "logging" -type "str" -default "standard" -ValidateSet "standard","verbose"
$Size = Get-AnsibleParam -obj $params -name "size" -type "str/int"
$FindPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_select" -type "str" -default "raw" -ValidateSet "raw","mbr","gpt"
$OperationalStatus = Get-AnsibleParam -obj $params -name "operational_status" -type "str" -default "offline" -ValidateSet "offline","online"
$ReadOnly = Get-AnsibleParam -obj $params -name "read_only" -type "bool" -default $true
$Number = Get-AnsibleParam -obj $params -name "number" -type "str/int"
# Set attributes partition
$SetPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_set" -type "str" -default "gpt" -ValidateSet "gpt","mbr"
$DriveLetter = Get-AnsibleParam -obj $params -name "drive_letter" -type "str"
# Set attributes file system
$FileSystem = Get-AnsibleParam -obj $params -name "file_system" -type "str" -default "ntfs" -ValidateSet "ntfs","refs"
$Label = Get-AnsibleParam -obj $params -name "label" -type "str" -default "ansible_disk"
$AllocUnitSize = Get-AnsibleParam -obj $params -name "allocation_unit_size" -type "str/int" -default 4 -ValidateSet 4,8,16,32,64
# Set attributes switches
$LargeFRS = Get-AnsibleParam -obj $params -name "large_frs" -type "bool" -default $false
$ShortNames = Get-AnsibleParam -obj $params -name "short_names" -type "bool" -default $false
$IntegrityStreams = Get-AnsibleParam -obj $params -name "integrity_streams" -type "bool" -default $false

# Create a new result object
$result = @{
    changed = $false
    disk_selected = @{
        disk = @{
        }
        existing_volumes = @{
        }
        existing_partitions = @{
        }
    }
    general_log = @{
    }
    change_log = @{
    }
    search_log = @{
    }
    set_options = @{
    }
}

# Convert option variables
if ($Logging -eq "verbose") {
    $result.change_log += @{
        convert_options = @{
        }
    }
}
$SizeInteger = $false
if ($Size -ne $null) {
    if (($Size.GetType()).Name -eq 'String') {
        if ([int32]2147483647 -ge $Size) {
            try {
                [int32]$Size = [convert]::ToInt32($Size, 10)
            } catch {
                if ($Logging -eq "verbose") {
                    $result.general_log.convert_validate_options = "failed"
                }
                Fail-Json -obj $result -message "Failed to convert option variable size from string to int32: $($_.Exception.Message)"
            }
            if ($Logging -eq "verbose") {
                $result.change_log.convert_options.size = "Converted option variable from string to int32"
            }
        } else {
            try {
                [int64]$Size = [convert]::ToInt64($Size, 10)
            } catch {
                if ($Logging -eq "verbose") {
                    $result.general_log.convert_validate_options = "failed"
                }
                Fail-Json -obj $result -message "Failed to convert option variable size from string to int64: $($_.Exception.Message)"
            }
            if ($Logging -eq "verbose") {
                $result.change_log.convert_options.size = "Converted option variable from string to int64"
            }
        }
    } else {
        if ($Logging -eq "verbose") {
            $result.change_log.convert_options.size = "No convertion of option variable needed"
        }
    }
    $SizeInteger = $true
} else {
    if ($Logging -eq "verbose") {
        $result.change_log.convert_options.size = "No size option used, no convertion needed"
    }
}

if (($AllocUnitSize.GetType()).Name -eq 'String') {
    try {
        [int32]$AllocUnitSize = [convert]::ToInt32($AllocUnitSize, 10)
    } catch {
        if ($Logging -eq "verbose") {
            $result.general_log.convert_validate_options = "failed"
        }
        Fail-Json -obj $result -message "Failed to convert option variable allocation_unit_size from string to int32: $($_.Exception.Message)"
    }
    if ($Logging -eq "verbose") {
        $result.change_log.convert_options.allocation_unit_size = "Converted option variable from string to int32" 
    }  
} else {
    if ($Logging -eq "verbose") {
        $result.change_log.convert_options.allocation_unit_size = "No convertion of option variable needed"
    }
}

$NumberInteger = $false
if ($Number -ne $null) {
    if (($Number.GetType()).Name -eq 'String') {
        try {
            [int32]$Number = [convert]::ToInt32($Number, 10)
        } catch {
            if ($Logging -eq "verbose") {
                $result.general_log.convert_validate_options = "failed"
            }
            Fail-Json -obj $result -message "Failed to convert option variable number from string to int32: $($_.Exception.Message)"
        }
        if ($Logging -eq "verbose") {
            $result.change_log.convert_options.number = "Converted option variable from string to int32"
        }
    } else {
        if ($Logging -eq "verbose") {        
            $result.change_log.convert_options.number = "No convertion of option variable needed"
        }
    }
    $NumberInteger = $true
} else {
    if ($Logging -eq "verbose") {   
        $result.change_log.convert_options.number = "No number option used, no convertion needed"
    }
}

$DriveChar = $false
if ($DriveLetter -ne $null) {
    if ($DriveLetter -like "[a-z]") {
        try {
            [char]$DriveLetter = [convert]::ToChar($DriveLetter)
        } catch {
            if ($Logging -eq "verbose") {            
                $result.general_log.convert_validate_options = "failed"
            }
            Fail-Json -obj $result -message "Failed to convert option variable from string to char: $($_.Exception.Message)"
        }
        if ($Logging -eq "verbose") {
            $result.change_log.convert_options.drive_letter = "Converted option variable from string to char"
        }
        $DriveChar = $true
    } else {
        if ($Logging -eq "verbose") {        
            $result.general_log.convert_validate_options = "failed"
        }
        Fail-Json -obj $result -message "Failed to convert option variable drive_letter from string to char because drive_letter value is no letter: $($_.Exception.Message)"
    }
} else {
    if ($Logging -eq "verbose") {
        $result.change_log.convert_options.drive_letter = "No drive_letter option used, no convertion needed"
    }
}

$result.general_log.convert_validate_options = "successful"

# Show option values
if ($Logging -eq "verbose") {
    $result += @{ 
        option_values_passed = @{
            check_mode = "$check_mode"
            logging = "$Logging"
            size = "$(if (-not $SizeInteger) {
                                $Size = "not_passed"
                            }
                            )$($Size)gb"
            partition_style_select = "$FindPartitionStyle"
            operational_status = "$OperationalStatus"
            read_only = "$ReadOnly"
            number = "$(if (-not $NumberInteger) {
                                        $Number = "not_passed"
                                    }
                                    )$Number"
            partition_style_set = "$SetPartitionStyle"
            drive_letter = "$(if (-not $DriveChar) {
                                                $DriveLetter = "not_passed"
                                           }
                                           )$DriveLetter"
            file_system = "$FileSystem"
            label = "$Label"
            allocation_unit_size = "$($AllocUnitSize)kb"
            large_frs = "$LargeFRS"
            short_names = "$ShortNames"
            integrity_streams = "$IntegrityStreams"
        }
    }
    $result.general_log.option_values = "successful"
}

# Functions
function Search-Disk {
        param(
                $DiskSizeInteger,
                $DiskNumberInteger,
                $DiskSize,
                $PartitionStyle,
                $OperationalStatus,
                $ReadOnly,
                $Number
        )

        if ($DiskSizeInteger -and $DiskNumberInteger) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Size -eq $DiskSize) -and ($_.Number -eq $Number)
            }

            return $disk
        } elseif ($DiskSizeInteger) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Size -eq $DiskSize)
            }

            return $disk
        } elseif ($DiskNumberInteger) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Number -eq $Number)
            }

            return $disk
        } else {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly)
            }

            return $disk
        }
}

function Set-OperationalStatus {
        param(
                $Disk,
                [switch]$Deactivate
        )

        if (-not $Deactivate) {
            Set-Disk -Number ($Disk.Number) -IsOffline $false | Out-Null

            return
        } else {
            Set-Disk -Number ($Disk.Number) -IsOffline $true | Out-Null

            return
        }
}

function Set-DiskWriteable {
        param(
                $Disk,
                [switch]$Deactivate
        )

        if (-not $Deactivate) {
            Set-Disk -Number ($Disk.Number) -IsReadonly $false | Out-Null
        } else {
            Set-Disk -Number ($Disk.Number) -IsReadonly $true | Out-Null
        }

        return
}

function Search-Volume {
        param(
                $Partition
        )

        $FoundVolume = Get-Volume | Where-Object {
            $Partition.AccessPaths -like $_.ObjectId
        }

        return $FoundVolume
}

function Set-Initialized {
        param(
                $Disk,
                $PartitionStyle
        )

        $Disk| Initialize-Disk -PartitionStyle $PartitionStyle -Confirm:$false | Out-Null

        return
}

function Convert-PartitionStyle {
        param(
                $Disk,
                $PartitionStyle
        )

        Invoke-Expression "'Select Disk $($Disk.Number)','Convert $($PartitionStyle)' | diskpart" | Out-Null

        return
}

function Manage-ShellHWService {
        param(
                $action
        )

        switch ($action) {
                Stop {
                    Stop-Service -Name ShellHWDetection | Out-Null

                    return
                }
                Start {
                    Start-Service -Name ShellHWDetection | Out-Null

                    return
                }
                Check {
                    $CheckService = (Get-Service ShellHWDetection).Status -eq "Running"

                    return $CheckService
                }
                default {
                    throw "Neither '-Stop', '-Start' nor 'Check' switch was passed to the function when invoked, without the switches the service can not be maintained"
                }
        }
}

function Create-Partition {
        param(
                $Disk,
                $SetDriveLetter
        )

        $Partition = $Disk | New-Partition -UseMaximumSize -DriveLetter $SetDriveLetter

        return $Partition
}

function Create-Volume {
        param(
                $Volume,
                $FileSystem,
                $FileSystemLabel,
                $FileSystemAllocUnitSize,
                $FileSystemLargeFRS,
                $FileSystemShortNames,
                $FileSystemIntegrityStreams
        )

        $Alloc = $FileSystemAllocUnitSize *1KB

        $ParaVol = @{
            FileSystem = $FileSystem
            NewFileSystemLabel = $FileSystemLabel
            AllocationUnitSize = $Alloc
        }

        if ($FileSystem -eq "ntfs") {
            if (-not $FileSystemLargeFRS) {
                $CreatedVolume = $Volume | Format-Volume @ParaVol -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false

                return $CreatedVolume
            } else {
                $CreatedVolume = $Volume | Format-Volume @ParaVol -UseLargeFRS -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false

                return $CreatedVolume
            }
        } elseif ($FileSystem -eq "refs") {
            $CreatedVolume = $Volume | Format-Volume @ParaVol -SetIntegrityStreams $FileSystemIntegrityStreams -Force -Confirm:$false

            return $CreatedVolume
        }
}

# Rescan disks
try {
    Invoke-Expression '"rescan" | diskpart' | Out-Null
} catch {
    $result.general_log.rescan_disks = "failed"
}
$result.general_log.rescan_disks = "successful"

$ParamsDisk = @{
    DiskSizeInteger = $SizeInteger
    DiskNumberInteger = $NumberInteger
    DiskSize = "$(if ($SizeInteger) {
                                $SizeF = $Size *1GB
                            } else {
                                $SizeF = $null
                            }
                           )$SizeF"
    PartitionStyle = $FindPartitionStyle
    OperationalStatus = $OperationalStatus
    ReadOnly = $ReadOnly
    Number = $Number
}

# Search disk
try {
    $disk = Search-Disk @ParamsDisk
} catch {
    $result.general_log.search_disk = "failed"
    Fail-Json -obj $result -message "Failed to search and/or select the disk with the specified option values: $($_.Exception.Message)"
}
if ($disk) {
    $diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
    if ($diskcount -ge 2) {
        $disk = $disk[0]
        $result.disk_selected.disk.total_found_disks = "$diskcount"
        $result.disk_selected.disk.number = "$([string]$disk.Number)"
        $result.disk_selected.disk.size = "$(if (-not $SizeInteger) {
                                                                                $Size = $disk.Size / 1GB
                                                                            }
                                                                           )$($Size)gb"
    } else {
        $result.disk_selected.disk.total_found_disks = "$diskcount"
        $result.disk_selected.disk.number = "$([string]$disk.Number)"
        $result.disk_selected.disk.size = "$(if (-not $SizeInteger) {
                                                                                $Size = $disk.Size / 1GB
                                                                            }
                                                                           )$($Size)gb"
    }
    [string]$DOperSt = $disk.OperationalStatus
    [string]$DPartStyle = $disk.PartitionStyle
    [string]$DROState = $disk.IsReadOnly
} else {
        $result.disk_selected.disk.total_found_disks = "0"
        Fail-Json -obj $result -message "No disk could be found and selected with the passed option values"
}
$result.general_log.search_disk = "successful"

# Check and set operational status and read-only state
$SetOnline = $false
$SetWriteable = $false
$OPStatusFailed = $false
$ROStatusFailed = $false
if ($DPartStyle -eq "RAW") {
    if ($DOperSt -eq "Offline") {
        $result.change_log.operational_status = "Disk is offline, but nothing will be changed because partition style is $($DPartStyle) and disk will be set to online during intialization part"
    } else {
        $result.change_log.operational_status = "Disk is online already"
    }
    if ($DROState -eq "True") {
        $result.change_log.writeable_status = "Disk is read-only, but nothing will be changed because partition style is $($DPartStyle) and disk will be set to writeable during intialization part"
    } else {
        $result.change_log.writeable_status = "Disk is writeable already"
    }
} else {
    if ($DOperSt -eq "Online") {
        $result.change_log.operational_status = "Disk is online already"                                    
    } else {
        if (-not $check_mode) {
            # Set online
            try {
                Set-OperationalStatus -Disk $disk
            } catch {
                $result.general_log.set_operational_status = "failed"
                $result.change_log.operational_status = "Disk failed to set online"
                $result.general_log.set_writeable_status = "untouched"
                $result.change_log.writeable_status = "Disk writeable status was not touched"
                Fail-Json -obj $result -message "Failed to set the disk online: $($_.Exception.Message)"
            }
            $result.change_log.operational_status = "Disk set online" 
            $result.changed = $true
            $SetOnline = $true
        } else {
            $result.change_log.operational_status = "Disk is offline but was not set online due to activated check_mode"
        }
    }      
    if ($DROState -ne "True") {
        $result.change_log.writeable_status = "Disk is writeable already"
    } else {
        if (-not $check_mode) {
            # Set writeable
            try {
                Set-DiskWriteable -Disk $disk
            } catch {
                $result.general_log.set_writeable_status = "failed"
                $result.change_log.writeable_status = "Disk failed to set from read-only to writeable"
                if ($SetOnline) {
                    try {
                        Set-OperationalStatus -Disk $disk -Deactivate
                    } catch {
                        $OPStatusFailed = $true
                    } finally {
                        if (-not $OPStatusFailed) {
                            $result.general_log.set_operational_status = "successful"
                            $result.change_log.operational_status = "Disk set online and now offline again"
                            $result.changed = $true
                        } else {
                            $result.general_log.set_operational_status = "failed"
                            $result.change_log.operational_status = "Disk failed to set offline again"
                        }
                    }
                } else {
                    $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                }
                Fail-Json -obj $result -message "Failed to set the disk from read-only to writeable state: $($_.Exception.Message)"
            }
            $result.change_log.writeable_status = "Disk set from read-only to writeable"
            $result.changed = $true
            $SetWriteable = $true
        } else {
            $result.change_log.writeable_status = "Disk is read-only but was not set writeable due to activated check_mode"
        }
    } 
}
$result.general_log.set_operational_status = "successful"
$result.general_log.set_writeable_status = "successful"

# Check volumes and partitions
[string]$PartNumber = $disk.NumberOfPartitions
# Verify partitons and volumes
if ($PartNumber -ge 1) {
    # Collect partitions
    try {
        $Fpartition = Get-Partition -DiskNumber $disk.Number
    } catch {
        $result.general_log.check_volumes_partitions = "failed"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "General error while searching for partitions on the selected disk: $($_.Exception.Message)"
    }
    # Collect volumes
    try {
        $volume = Search-Volume -Partition $Spartition
    } catch {
        $result.general_log.check_volumes_partitions = "failed"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "General error while searching for volumes on the selected disk: $($_.Exception.Message)"
    }
    # Existent volumes and partitions
    if (-not $volume) {
        $result.general_log.check_volumes_partitions = "successful"
        $result.disk_selected.existing_volumes.volumes_found = "0"
        $result.disk_selected.existing_partitions.partitions_found = "$PartNumber"
        $result.disk_selected.existing_partitions.partitions_types = "$([string]$Spartition.Type)"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "Existing partitions found on the selected disk"
    } else {
        $result.general_log.check_volumes_partitions = "successful"
        $result.disk_selected.existing_volumes.volumes_found = "$((($volume | Measure-Object).Count).ToString())"
        $result.disk_selected.existing_volumes.volumes_types = "$([string]$volume.FileSystem)"
        $result.disk_selected.existing_partitions.partitions_found = "$PartNumber"
        $result.disk_selected.existing_partitions.partitions_types = "$([string]$Spartition.Type)" 
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "Existing volumes found on the selected disk"
    }
} else {
    $result.disk_selected.existing_volumes.volumes_found = "0"
    $result.disk_selected.existing_partitions.partitions_found = "$PartNumber"
}
$result.general_log.check_volumes_partitions = "successful"

# Check set option values
# Check drive letter
if ($DriveLetter -is [char]) {
    # Use defined drive letter
    try {
        $CheckLetter = Get-ChildItem Function:[$DriveLetter]: | Foreach-Object {
            Test-Path $_
        }
    } catch {
        $result.general_log.check_set_options = "failed"
        $result.set_options.drive_letter_set = "$DriveLetter"
        $result.set_options.drive_letter_used = "unchecked"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "Check if drive_letter value is used already on another partition on the target failed"
    }
    if (!$CheckLetter) {
        $result.set_options.drive_letter_set = "$DriveLetter"
        $result.set_options.drive_letter_used = "no"
    } else {
        $result.general_log.check_set_options = "failed"
        $result.set_options.drive_letter_set = "$DriveLetter"
        $result.set_options.drive_letter_used = "yes"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "The drive_letter $DriveLetter is set on another partition on this target already which is not allowed"
    }
} else {
    # Use random drive letter
    try {
        $DriveLetter = Get-ChildItem Function:[a-z]: -name | Where-Object {
            !(Test-Path $_)
        } | Get-Random
    } catch {
        $result.general_log.check_set_options = "failed"
        $result.set_options.drive_letter_set = "not_available"
        $result.set_options.drive_letter_used = "no"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "The check to get free drive letters on the target failed"
    }
    if ($DriveLetter) {
        $DriveLetter = $DriveLetter.TrimEnd(":").ToLower()
        $result.set_options.drive_letter_set = "$DriveLetter"
        $result.set_options.drive_letter_used = "no"
    } else {
        $result.general_log.check_set_options = "failed"
        $result.set_options.drive_letter_set = "no_free_drive_letter_available"
        $result.set_options.drive_letter_used = "yes"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "No free drive_letter left on the target"
    }
}
# Check file system
if ($FileSystem -eq "ntfs") {
    if ($Size -le 256000) {
        $result.set_options.size_file_system = "valid_size"
    } else {
        $result.general_log.check_set_options = "failed"
        $result.set_options.size_file_system = "invalid_size"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "Option size with value $($Size)gb is not a valid size for ntfs hence the disk can not be formatted with this file system"
    }
} elseif ($FileSystem -eq "refs") {
    if ($Size -le 1208925819614650000000000) {
        $result.set_options.size_file_system = "valid_size"
        if ($AllocUnitSize -ne 64) {
            $AllocUnitSize = 64
            $result.set_options.allocation_unit_size = "$($AllocUnitSize)kb_adjusted_refs"                                  
        }
    } else {
        $result.general_log.check_set_options = "failed"
        $result.set_options.size_file_system = "invalid_size"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        Fail-Json -obj $result -message "Option size with value $($Size)gb is not a valid size for refs hence the disk can not be formatted with this file system"
    }
}
# Check large frs
if ($LargeFRS) {
    if ($FileSystem -eq "refs") {
        $result.set_options.large_frs = "disabled_refs"        
    }
}
# Check short names
if ($ShortNames) {
    if ($FileSystem -eq "refs") {
        $result.set_options.short_names ="disabled_refs"
    }
}
# Check integrity streams
if ($IntegrityStreams) {
    if ($FileSystem -eq "ntfs") {
        $result.set_options.integrity_streams = "disabled_ntfs"
    }
}
$result.general_log.check_set_options = "successful"

# Initialize / convert disk
if ($DPartStyle -eq "RAW") {
    if (-not $check_mode) {
        if ($DOperSt -eq "Offline") {
            $SetOnline = $true
        }
        if ($DROState -eq "True") {
            $SetWriteable = $true
        }
        # Initialize disk
        try {
            Set-Initialized -Disk $disk -PartitionStyle $SetPartitionStyle
        } catch {
            $result.general_log.initialize_convert = "failed"
            $result.change_log.initializing = "Disk initialization failed - Partition style $FindPartitionStyle (partition_style_select) could not be initalized to $SetPartitionStyle (partition_style_set)"
            $GetDiskFailed = $false
            $FailDisk = $null
            if ($SetOnline) {
                try {
                    $FailDisk = Get-Disk -Number $disk.Number
                } catch {
                    $GetDiskFailed = $true
                } finally {
                    if (-not $GetDiskFailed) {
                        try {
                            Set-OperationalStatus -Disk $disk -Deactivate
                        } catch {
                            $OPStatusFailed = $true
                        }
                        if (-not $OPStatusFailed) {
                            $result.general_log.set_operational_status = "successful"
                            $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization and set now to it's initial state offline again"
                            $result.changed = $true
                        } else {
                            $result.general_log.set_operational_status = "failed"
                            $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization, set it to it's inital state offline again failed also now"
                        }
                    } else {
                        $result.general_log.set_operational_status = "failed"
                        $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization and was now tried to set offline again but disk could not be found anymore"
                    }
                }
            } else {
                $result.change_log.operational_status = "Disks initial state was online already before failed disk initialization and therefore need not set to offline"
            }
            if ($SetWriteable) {
                if (-not $FailDisk) {
                    try {
                        $FailDisk = Get-Disk -Number $disk.Number
                    } catch {
                        $GetDiskFailed = $true
                    }
                }
                if (-not $GetDiskFailed) {
                    try {
                        Set-DiskWriteable -Disk $disk -Deactivate
                    } catch {
                        $ROStatusFailed = $true
                    } finally {
                        if (-not $ROStatusFailed) {
                            $result.general_log.set_writeable_status = "successful"
                            $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization and set now to it's initial state read-only again"
                            $result.changed = $true
                        } else {
                            $result.general_log.set_writeable_status = "failed"
                            $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization, set it to it's inital state read-only again failed also now"
                        }
                    }
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization and was now tried to set read-only again but disk could not be found anymore"
                }
            } else {
                $result.change_log.writeable_status = "Disks initial state was writeable already before failed disk initialization and therefore need not set to read-only"
            }
            Fail-Json -obj $result -message "Failed to initialize the disk: $($_.Exception.Message)"
        }
        $result.change_log.initializing = "Disk initialization successful - Partition style $FindPartitionStyle (partition_style_select) was initalized to $SetPartitionStyle (partition_style_set)"
        $result.changed = $true
    } else {
        $result.change_log.initializing = "Disk with partition style $FindPartitionStyle (partition_style_select) will not be initialized to $SetPartitionStyle (partition_style_set) due to activated check_mode"
    }
    $result.change_log.converting = "No convertion of partition style needed because disks partition style is $FindPartitionStyle"
} else {
    if ($DPartStyle -ne $SetPartitionStyle) {
        if (-not $check_mode) {
            # Convert disk
            try {
                Convert-PartitionStyle -Disk $disk -PartitionStyle $SetPartitionStyle
            } catch {
                $result.general_log.initialize_convert = "failed"
                $result.change_log.converting = "Partition style $FindPartitionStyle (partition_style_select) could not be converted to $SetPartitionStyle (partition_style_set)"
                if ($SetOnline) {
                    try {
                        Set-OperationalStatus -Disk $disk -Deactivate
                    } catch {
                        $OPStatusFailed = $true
                    } finally {
                        if (-not $OPStatusFailed) {
                            $result.general_log.set_operational_status = "successful"
                            $result.change_log.operational_status = "Disk set online and now offline again"
                            $result.changed = $true
                        } else {
                            $result.general_log.set_operational_status = "failed"
                            $result.change_log.operational_status = "Disk failed to set offline again"
                        }
                    }
                } else {
                    $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                }
                if ($SetWriteable) {
                    try {
                        Set-DiskWriteable -Disk $disk -Deactivate
                    } catch {
                        $ROStatusFailed = $true
                    } finally {
                        if (-not $ROStatusFailed) {
                            $result.general_log.set_writeable_status = "successful"
                            $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                            $result.changed = $true
                        } else {
                            $result.general_log.set_writeable_status = "failed"
                            $result.change_log.writeable_status = "Disk failed to set read-only again"
                        }
                    }
                } else {
                    $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
                }
                Fail-Json -obj $result -message "Failed to convert the disk: $($_.Exception.Message)"
            }
            $result.change_log.converting = "Partition style $FindPartitionStyle (partition_style_select) was converted to $SetPartitionStyle (partition_style_set)"
            $result.changed = $true
        } else {
            $result.change_log.converting = "Disk will not be converted from partition style $FindPartitionStyle (partition_style_select) to $SetPartitionStyle (partition_style_set) due to activated check_mode"
        }
    } else {
        # No convertion
        $result.change_log.converting = "$SetPartitionStyle (partition_style_set) is equal to selected partition style of disk, no convertion needed"
    }
    $result.change_log.initializing = "No initialization of disk needed because disks partition style is $FindPartitionStyle"
}
$result.general_log.initialize_convert = "successful"

# Maintain ShellHWService (not module terminating)
$StopSuccess = $false
$StopFailed = $false
$StartFailed = $false
$CheckFailed = $false
# Check ShellHWService
try {
    $Check = Manage-ShellHWService -Action "Check"
} catch {
    $CheckFailed = $true
} finally {
    if ($Check) {
        $result.search_log.shellhw_service_state = "running"
        if (-not $check_mode) {
            # Stop ShellHWService
            try {
                Manage-ShellHWService -Action "Stop"
            } catch {
                $StopFailed = $true
            } finally {
                if (-not $StopFailed) {
                    $result.general_log.maintain_shellhw_service = "successful"
                    $result.change_log.shellhw_service_state = "Set from 'Running' to 'Stopped'"
                    $StopSuccess = $true
                    $result.changed = $true
                } else {
                    $result.general_log.maintain_shellhw_service = "failed"
                    $result.change_log.shellhw_service_state = "Could not be set from 'Running' to 'Stopped'"
                }
            }
        } else {
            $result.general_log.maintain_shellhw_service = "successful"
            $result.change_log.shellhw_service_state = "Service will not be set from 'Running' to 'Stopped' due to activated check_mode"
        }
    } elseif ($CheckFailed) {
        $result.general_log.maintain_shellhw_service = "failed"
        $result.search_log.shellhw_service_state = "check_failed"
        $result.change_log.shellhw_service_state = "Service will not be changed because the check has failed"
    } else {
        $result.general_log.maintain_shellhw_service = "successful"
        $result.search_log.shellhw_service_state = "stopped"
        $result.change_log.shellhw_service_state = "Service is stopped already"
    }
}

# Part disk
if (-not $check_mode) {
    try {
        $CPartition = Create-Partition -Disk $disk -SetDriveLetter $DriveLetter
    } catch {
        $result.general_log.create_partition = "failed"
        $result.change_log.partitioning = "Partition was failed to create on disk with partition style $SetPartitionStyle"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        if ($StopSuccess) {
            try {
                Manage-ShellHWService -Action "Start"
            } catch {
                $StartFailed = $true
            } finally {
                if (-not $StartFailed) {
                    $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                    $result.changed = $true
                } else {
                    $result.general_log.maintain_shellhw_service = "failed"
                    $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"     
                }
            }
        } elseif ($CheckFailed) {
            $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
        } else {
            $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"
        }
        Fail-Json -obj $result -message "Failed to create the partition on the disk: $($_.Exception.Message)"
    }
    $result.general_log.create_partition = "successful"
    $result.change_log.partitioning = "Initial partition $($CPartition.Type) was created successfully on partition style $SetPartitionStyle"
    $result.changed = $true
} else {
    $result.general_log.create_partition = "successful"
    $result.change_log.partitioning = "Disk will not be partitioned due to activated check_mode"
}

# Create volume
if (-not $check_mode) {
    $ParamsVol = @{
        Volume = $CPartition
        FileSystem = $FileSystem
        FileSystemLabel = $Label
        FileSystemAllocUnitSize = $AllocUnitSize
        FileSystemLargeFRS = $LargeFRS
        FileSystemShortNames = $ShortNames
        FileSystemIntegrityStreams = $IntegrityStreams
    }
    try {
        $CVolume = Create-Volume @ParamsVol
    } catch {
        $result.general_log.create_volume = "failed"
        $result.change_log.formatting = "Volume was failed to create on disk with partition $($CPartition.Type)"
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    $result.general_log.set_operational_status = "successful"
                    $result.change_log.operational_status = "Disk set online and now offline again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_operational_status = "failed"
                    $result.change_log.operational_status = "Disk failed to set offline again"
                }
            }
        } else {
            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    $result.general_log.set_writeable_status = "successful"
                    $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    $result.changed = $true
                } else {
                    $result.general_log.set_writeable_status = "failed"
                    $result.change_log.writeable_status = "Disk failed to set read-only again"
                }
            }
        } else {
            $result.change_log.writeable_status = "Disk was writeable already and need not to be set read-only"  
        }
        if ($StopSuccess) {
            try {
                Manage-ShellHWService -Action "Start"
            } catch {
                $StartFailed = $true
            } finally {
                if (-not $StartFailed) {
                    $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                    $result.changed = $true
                } else {
                    $result.general_log.maintain_shellhw_service = "failed"
                    $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"     
                }
            }
        } elseif ($CheckFailed) {
            $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
        } else {
            $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"
        }
        Fail-Json -obj $result -message "Failed to create the volume on the disk: $($_.Exception.Message)"
    }
    $result.general_log.create_volume = "successful"
    $result.change_log.formatting = "Volume $($CVolume.FileSystem) was created successfully on partition $($CPartition.Type)"
    $result.changed = $true
} else {
    $result.general_log.create_volume = "successful"
    $result.change_log.formatting = "Disk will not be formatted due to activated check_mode"
}

# Finally check if ShellHWService needs to be started again
if (-not $check_mode) {
    if ($StopSuccess) {
        # Start ShellHWService
        try {
            Manage-ShellHWService -Action "Start"
        } catch {
            $StartFailed = $true
        } finally {
            if (-not $StartFailed) {
                $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                $result.changed = $true
            } else {
                $result.general_log.maintain_shellhw_service = "failed"
                $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"     
            }
        }
    } elseif ($CheckFailed) {
            $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
    } else {
            $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"  
    }
}

# Return result
Exit-Json -obj $result
