#!powershell

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

# Find attributes
$Size = Get-AnsibleParam -obj $params -name "size" -type "int"
$FindPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_select" -type "str" -default "raw" -ValidateSet "raw","mbr","gpt"
$OperationalStatus = Get-AnsibleParam -obj $params -name "operational_status" -type "str" -default "offline" -ValidateSet "offline","online"
$ReadOnly = Get-AnsibleParam -obj $params -name "read_only" -type "bool" -default $true
$Number = Get-AnsibleParam -obj $params -name "number" -type "int"
# Set attributes partition
$SetPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_set" -type "str" -default "gpt" -ValidateSet "gpt","mbr"
$DriveLetter = Get-AnsibleParam -obj $params -name "drive_letter" -type "str" -ValidateSet "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"
$PartitionAccessPath = Get-AnsibleParam -obj $params -name "access_path" -type "str"
# Set attributes file system
$FileSystem = Get-AnsibleParam -obj $params -name "file_system" -type "str" -default "ntfs" -ValidateSet "ntfs","refs"
$Label = Get-AnsibleParam -obj $params -name "label" -type "str" -default "ansible_disk"
$AllocUnitSize = Get-AnsibleParam -obj $params -name "allocation_unit_size" -type "int" -default 4 -ValidateSet 4,8,16,32,64
# Set attributes switches
$LargeFRS = Get-AnsibleParam -obj $params -name "large_frs" -type "bool" -default $false
$ShortNames = Get-AnsibleParam -obj $params -name "short_names" -type "bool" -default $false
$IntegrityStreams = Get-AnsibleParam -obj $params -name "integrity_streams" -type "bool" -default $false

# Create a new result object
$result = @{
    changed = $false
}

# Validate option values
if ($Size -ne $null) {
    if ($Size -lt 1) {
        Fail-Json -obj $result -message "Size option value must be at least 1gb"
    }
}
if ($Number -ne $null) {
    if ([int32]2147483647 -lt $Number) {
        Fail-Json -obj $result -message "Number option must be of type int32"
    }
}
if ($PartitionAccessPath -ne $null) {
    if ((-not ((Get-Partition).AccessPaths -like "$PartitionAccessPath*")) -and (Test-Path $PartitionAccessPath -PathType Container) -and ((Get-Item $PartitionAccessPath).LinkType -eq $null)) {
        if (-not (Get-ChildItem $PartitionAccessPath)) {
            $true
        } else {
            Fail-Json -obj $result -message "$PartitionAccessPath is not an empty folder (contains files and/or folders)"                                    
        }
    } elseif ((Get-Partition).AccessPaths -like "$PartitionAccessPath*") {
        Fail-Json -obj $result -message "$PartitionAccessPath is already in use as access path by another disk"
    } elseif (-not (Test-Path $PartitionAccessPath -PathType Container)) {
        Fail-Json -obj $result -message "$PartitionAccessPath is not a valid path/directory/folder on the target for option SetPartitionStyle"
    } elseif((Get-Item $PartitionAccessPath).LinkType -ne $null) {
        Fail-Json -obj $result -message "$PartitionAccessPath is already in use as a link of type $((Get-Item $PartitionAccessPath).LinkType)"
    }
}

# Functions
function Search-Disk {
        param(
                $DiskSize,
                $PartitionStyle,
                $OperationalStatus,
                $ReadOnly,
                $Number
        )
        if ($DiskSize -ne $null) {
            $DiskSize = $DiskSize *1GB
        }
        if ($DiskSize -and ($Number -ne $null)) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Size -eq $DiskSize) -and ($_.Number -eq $Number)
            }
        } elseif ($DiskSize) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Size -eq $DiskSize)
            }
        } elseif ($Number -ne $null) {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Number -eq $Number)
            }
        } else {
            $disk = Get-Disk | Where-Object {
                ($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly)
            }
        }

        return $disk
}

function Set-OperationalStatus {
        param(
                $Disk,
                [switch]$Deactivate
        )
        $null = Set-Disk -Number ($Disk.Number) -IsOffline $Deactivate.IsPresent
}

function Set-DiskWriteable {
        param(
                $Disk,
                [switch]$Deactivate
        )
        $null = Set-Disk -Number ($Disk.Number) -IsReadonly $Deactivate.IsPresent
}

function Search-Volume {
        param(
                $Partition
        )
        $FoundVolume = Get-Volume | Where-Object {
            $Partition.AccessPaths -like $_.ObjectId
        }
        if ($FoundVolume -eq $null) {
            
            return $false
        }

        return $FoundVolume
}

function Set-Initialized {
        param(
                $Disk,
                $PartitionStyle
        )
        $null = $Disk| Initialize-Disk -PartitionStyle $PartitionStyle -Confirm:$false
}

function Convert-PartitionStyle {
        param(
                $Disk,
                $PartitionStyle
        )
        $null = Invoke-Expression "'Select Disk $($Disk.Number)','Convert $($PartitionStyle)' | diskpart"
}

function Manage-ShellHWService {
        param(
                $Action
        )
        switch ($Action) {
                Stop {
                    $null = Stop-Service -Name ShellHWDetection
                }
                Start {
                    $null = Start-Service -Name ShellHWDetection
                }
                Check {
                    $CheckService = (Get-Service ShellHWDetection).Status -eq "Running"

                    return $CheckService
                }
        }
}

function Create-Partition {
        param(
                $Disk,
                $SetDriveLetter
        )
        if ($SetDriveLetter -ne $null) {
            $Partition = $Disk | New-Partition -UseMaximumSize -DriveLetter $SetDriveLetter
        } else {
            $Partition = $Disk | New-Partition -UseMaximumSize
        }

        return $Partition
}

function Add-AccessPath {
        param(
                $Partition,
                $Path
        )
        $null = $Partition | Add-PartitionAccessPath -AccessPath $Path
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
        switch ($FileSystem) {
                ntfs {
                    $ParaVol += @{ShortFileNameSupport = $FileSystemShortNames; UseLargeFRS = $FileSystemLargeFRS}
                }
                refs {
                    $ParaVol['SetIntegrityStreams'] = $FileSystemIntegrityStreams
                }
        }
        $CreatedVolume = $Volume | Format-Volume @ParaVol -Force -Confirm:$false

        return $CreatedVolume
}

# Rescan disks
$null = Invoke-Expression '"rescan" | diskpart'

# Search disk
$ParamsDisk = @{
    DiskSize = $Size
    PartitionStyle = $FindPartitionStyle
    OperationalStatus = $OperationalStatus
    ReadOnly = $ReadOnly
    Number = $Number
}
try {
    $disk = Search-Disk @ParamsDisk
} catch {
    Fail-Json -obj $result -message "Failed to search and/or select the disk with the specified option values: $($_.Exception.Message)"
}
if ($disk) {
    $diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
    if ($diskcount -ge 2) {
        $disk = $disk[0]
    }
    [string]$DOperSt = $disk.OperationalStatus
    [string]$DPartStyle = $disk.PartitionStyle
    [string]$DROState = $disk.IsReadOnly
} else {
        Fail-Json -obj $result -message "No disk could be found and selected with the passed option values"
}

if ($check_mode -or $diff_mode) {
    $result += @{ 
        change_log = @{
        }
    }
}

# Check and set operational status and read-only state
$SetOnline = $false
$SetWriteable = $false
$OPStatusFailed = $false
$ROStatusFailed = $false
if ($DPartStyle -ne "RAW") {
    if ($DOperSt -ne "Online") {
        if (-not $check_mode) {
            # Set online
            try {
                Set-OperationalStatus -Disk $disk
            } catch {
                if ($Verbose) {
                    $result.Remove("change_log")
                }
                Fail-Json -obj $result -message "Failed to set the disk online: $($_.Exception.Message)"
            }
            if ($diff_mode) {
                $result.change_log.operational_status = "Disk set online"
            }
            $result.changed = $true
            $SetOnline = $true
        } else {
            $result.change_log.operational_status = "Disk is offline but was not set online due to activated check_mode"
        }
    }      
    if ($DROState -eq "True") {
        if (-not $check_mode) {
            # Set writeable
            try {
                Set-DiskWriteable -Disk $disk
            } catch {
                if ($diff_mode) {
                    $result.change_log.writeable_status = "Disk failed to set from read-only to writeable"
                }
                if ($SetOnline) {
                    try {
                        Set-OperationalStatus -Disk $disk -Deactivate
                    } catch {
                        $OPStatusFailed = $true
                    } finally {
                        if (-not $OPStatusFailed) {
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk set online and now offline again"
                            }
                            $result.changed = $true
                        } else {
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk failed to set offline again"
                            }
                        }
                    }
                }
                Fail-Json -obj $result -message "Failed to set the disk from read-only to writeable state: $($_.Exception.Message)"
            }
            if ($diff_mode) {
                $result.change_log.writeable_status = "Disk set from read-only to writeable"
            }
            $result.changed = $true
            $SetWriteable = $true
        } else {
            $result.change_log.writeable_status = "Disk is read-only but was not set writeable due to activated check_mode"
        }
    } 
}

# Check volumes and partitions
[string]$PartNumber = $disk.NumberOfPartitions
# Verify partitons and volumes
if ($PartNumber -ge 1) {
    # Collect partitions
    try {
        $partition = Get-Partition -DiskNumber $disk.Number
    } catch {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "General error while searching for partitions on the selected disk: $($_.Exception.Message)"
    }
    # Collect volumes
    try {
        $volume = Search-Volume -Partition $partition
    } catch {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "General error while searching for volumes on the selected disk: $($_.Exception.Message)"
    }
    # Existent volumes and partitions
    if (-not $volume) {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Existing partitions found on the selected disk"
    } else {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Existing volumes found on the selected disk"
    }
}

# Check set option values
# Check drive letter and access path
if (($DriveLetter -eq $null) -and ($PartitionAccessPath -eq $null)) {
        # Use random drive letter
        try {
            $DriveLetter = Get-ChildItem Function:[a-z]: -Name | Where-Object {
                -not (Test-Path -Path $_)
            } | Get-Random
        } catch {
            if ($SetOnline) {
                try {
                    Set-OperationalStatus -Disk $disk -Deactivate
                } catch {
                    $OPStatusFailed = $true
                } finally {
                    if (-not $OPStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk set online and now offline again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk failed to set offline again"
                        }
                    }
                }
            }
            if ($SetWriteable) {
                try {
                    Set-DiskWriteable -Disk $disk -Deactivate
                } catch {
                    $ROStatusFailed = $true
                } finally {
                    if (-not $ROStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk failed to set read-only again"
                        }
                    }
                }
            }
            Fail-Json -obj $result -message "The check to get free drive letters on the target failed"
        }
        if ($DriveLetter) {
            $DriveLetter = $DriveLetter.TrimEnd(":")
        } else {
            if ($SetOnline) {
                try {
                    Set-OperationalStatus -Disk $disk -Deactivate
                } catch {
                    $OPStatusFailed = $true
                } finally {
                    if (-not $OPStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk set online and now offline again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk failed to set offline again"
                        }
                    }
                }
            }
            if ($SetWriteable) {
                try {
                    Set-DiskWriteable -Disk $disk -Deactivate
                } catch {
                    $ROStatusFailed = $true
                } finally {
                    if (-not $ROStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk failed to set read-only again"
                        }
                    }
                }
            }
            Fail-Json -obj $result -message "No free drive letter left on the target"
        }
} elseif ($DriveLetter -eq [string]) {
    # Use defined drive letter
    try {
        $CheckLetter = Get-ChildItem Function:[$DriveLetter]: | Foreach-Object {
            Test-Path -Path $_
        }
    } catch {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Check if drive_letter value is used already on another partition on the target failed"
    }
    if ($CheckLetter) {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "The drive letter $DriveLetter is set on another partition on this target already which is not allowed"
    }
}
# Check file system
if ($FileSystem -eq "ntfs") {
    if ($Size -le 256000) {
    } else {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Option size with value $($Size)gb is not a valid size for ntfs hence the disk can not be formatted with this file system"
    }
} elseif ($FileSystem -eq "refs") {
    if ($AllocUnitSize -ne 64) {
        $AllocUnitSize = 64
        if ($diff_mode) {
            $result.change_log.allocation_unit = "Size was automatically adjusted to 64kb due to file_system option value refs"
        }      
    }
}

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
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization and set now to it's initial state offline again"
                            }
                            $result.changed = $true
                        } else {
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization, set it to it's inital state offline again failed also now"
                            }
                        }
                    } else {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk was tried to set online during failed disk initalization and was now tried to set offline again but disk could not be found anymore"
                        }
                    }
                }
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
                            if ($diff_mode) {
                                $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization and set now to it's initial state read-only again"
                            }
                            $result.changed = $true
                        } else {
                            if ($diff_mode) {
                                $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization, set it to it's inital state read-only again failed also now"
                            }
                        }
                    }
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk was tried to set writeable during failed disk initalization and was now tried to set read-only again but disk could not be found anymore"
                    }
                }
            }
            Fail-Json -obj $result -message "Failed to initialize the disk: $($_.Exception.Message)"
        }
        if ($diff_mode) {
            $result.change_log.initializing = "Disk initialization successful - Partition style $FindPartitionStyle (partition_style_select) was initalized to $SetPartitionStyle (partition_style_set)"
        }
        $result.changed = $true
    } else {
        $result.change_log.initializing = "Disk with partition style $FindPartitionStyle (partition_style_select) will not be initialized to $SetPartitionStyle (partition_style_set) due to activated check_mode"
    }
} else {
    if ($DPartStyle -ne $SetPartitionStyle) {
        if (-not $check_mode) {
            # Convert disk
            try {
                Convert-PartitionStyle -Disk $disk -PartitionStyle $SetPartitionStyle
            } catch {
                if ($SetOnline) {
                    try {
                        Set-OperationalStatus -Disk $disk -Deactivate
                    } catch {
                        $OPStatusFailed = $true
                    } finally {
                        if (-not $OPStatusFailed) {
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk set online and now offline again"
                            }
                            $result.changed = $true
                        } else {
                            if ($diff_mode) {
                                $result.change_log.operational_status = "Disk failed to set offline again"
                            }
                        }
                    }
                }
                if ($SetWriteable) {
                    try {
                        Set-DiskWriteable -Disk $disk -Deactivate
                    } catch {
                        $ROStatusFailed = $true
                    } finally {
                        if (-not $ROStatusFailed) {
                            if ($diff_mode) {
                                $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                            }
                            $result.changed = $true
                        } else {
                            if ($diff_mode) {
                                $result.change_log.writeable_status = "Disk failed to set read-only again"
                            }
                        }
                    }
                }
                Fail-Json -obj $result -message "Failed to convert the disk: $($_.Exception.Message)"
            }
            if ($diff_mode) {
                $result.change_log.converting = "Partition style $FindPartitionStyle (partition_style_select) was converted to $SetPartitionStyle (partition_style_set)"
            }
            $result.changed = $true
        } else {
            $result.change_log.converting = "Disk will not be converted from partition style $FindPartitionStyle (partition_style_select) to $SetPartitionStyle (partition_style_set) due to activated check_mode"
        }
    }
}

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
        if (-not $check_mode) {
            # Stop ShellHWService
            try {
                Manage-ShellHWService -Action "Stop"
            } catch {
                $StopFailed = $true
            } finally {
                if (-not $StopFailed) {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Set from 'Running' to 'Stopped'"
                    }
                    $StopSuccess = $true
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Could not be set from 'Running' to 'Stopped'"
                    }
                }
            }
        } else {
            $result.change_log.shellhw_service_state = "Service will not be set from 'Running' to 'Stopped' due to activated check_mode"
        }
    } elseif ($CheckFailed) {
        if ($diff_mode) {
            $result.change_log.shellhw_service_state = "Service will not be changed because the check has failed"
        }
    }
}

# Part disk
if (-not $check_mode) {
    try {
        $CPartition = Create-Partition -Disk $disk -SetDriveLetter $DriveLetter
    } catch {
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        if ($StopSuccess) {
            try {
                Manage-ShellHWService -Action "Start"
            } catch {
                $StartFailed = $true
            } finally {
                if (-not $StartFailed) {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Failed to create the partition on the disk: $($_.Exception.Message)"
    }
    if ($diff_mode) {
        if (($DriveLetter -eq $null) -and ($PartitionAccessPath -eq $null)) {
            $result.change_log.partitioning = "Initial partition $($CPartition.Type) with random drive letter $DriveLetter was created successfully on partition style $SetPartitionStyle"
        } elseif ($DriveLetter -eq $null) {
            $result.change_log.partitioning = "Initial partition $($CPartition.Type) with no drive letter was created successfully on partition style $SetPartitionStyle"
        } else {
            $result.change_log.partitioning = "Initial partition $($CPartition.Type) with passed drive letter $DriveLetter was created successfully on partition style $SetPartitionStyle"
        }
    }
    $result.changed = $true
} else {
    $result.change_log.partitioning = "Disk will not be partitioned due to activated check_mode"
}

# Add partition access path
if (-not $PartitionAccessPath -eq [String]::Empty) {
    if (-not $check_mode) {
        try {
            Add-AccessPath -Partition $CPartition -Path $PartitionAccessPath
        } catch {
            if ($SetOnline) {
                try {
                    Set-OperationalStatus -Disk $disk -Deactivate
                } catch {
                    $OPStatusFailed = $true
                } finally {
                    if (-not $OPStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk set online and now offline again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.operational_status = "Disk failed to set offline again"
                        }
                    }
                }
            }
            if ($SetWriteable) {
                try {
                    Set-DiskWriteable -Disk $disk -Deactivate
                } catch {
                    $ROStatusFailed = $true
                } finally {
                    if (-not $ROStatusFailed) {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.writeable_status = "Disk failed to set read-only again"
                        }
                    }
                }
            }
            if ($StopSuccess) {
                try {
                    Manage-ShellHWService -Action "Start"
                } catch {
                    $StartFailed = $true
                } finally {
                    if (-not $StartFailed) {
                        if ($diff_mode) {
                            $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                        }
                        $result.changed = $true
                    } else {
                        if ($diff_mode) {
                            $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                        }
                    }
                }
            }
            Fail-Json -obj $result -message "Failed to create partition access path: $($_.Exception.Message)"
        }
        if ($diff_mode) {
            $result.change_log.access_path = "Partition access path $PartitionAccessPath was created successfully for partition $($CPartition.Type)"
        }
        $result.changed = $true
    } else {
        $result.change_log.access_path = "Partition access path will not be added to partition due to activated check_mode"
    }
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
        if ($SetOnline) {
            try {
                Set-OperationalStatus -Disk $disk -Deactivate
            } catch {
                $OPStatusFailed = $true
            } finally {
                if (-not $OPStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk set online and now offline again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.operational_status = "Disk failed to set offline again"
                    }
                }
            }
        }
        if ($SetWriteable) {
            try {
                Set-DiskWriteable -Disk $disk -Deactivate
            } catch {
                $ROStatusFailed = $true
            } finally {
                if (-not $ROStatusFailed) {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk set writeable and now read-only again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.writeable_status = "Disk failed to set read-only again"
                    }
                }
            }
        }
        if ($StopSuccess) {
            try {
                Manage-ShellHWService -Action "Start"
            } catch {
                $StartFailed = $true
            } finally {
                if (-not $StartFailed) {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                    }
                    $result.changed = $true
                } else {
                    if ($diff_mode) {
                        $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                    }
                }
            }
        }
        Fail-Json -obj $result -message "Failed to create the volume on the disk: $($_.Exception.Message)"
    }
    if ($diff_mode) {
        $result.change_log.formatting = "Volume $($CVolume.FileSystem) with allocation unit size $AllocUnitSize and label $Label was created successfully on partition $($CPartition.Type)"
    }
    $result.changed = $true
} else {
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
                if ($diff_mode) {
                    $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                }
                $result.changed = $true
            } else {
                if ($diff_mode) {
                    $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                }
            }
        }
    }
}

# Return result
Exit-Json -obj $result
