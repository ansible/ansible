#!powershell
#
# Copyright 2017, Marc Tschapek <marc.tschapek@bitgroup.de>
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

function Search-Disk{

param(
    $DiskSize,
    $PartitionStyle,
    $OperationalStatus,
    $ReadOnly,
    $Number
)

$DiskSize = $DiskSize *1GB

if($Number -is [int]){
        Get-Disk | Where-Object {($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Number -eq $Number) -and ($_.Size -eq $DiskSize)}
}
else{
    Get-Disk | Where-Object {($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.IsReadOnly -eq $ReadOnly) -and ($_.Size -eq $DiskSize)}
}
}

function Set-OperationalStatus{

param(
            [switch]$Online,
            [switch]$Offline,
            $Disk
            )

if($Online){
        Set-Disk -Number ($Disk.Number) -IsOffline $false
}
elseif($Offline){
        Set-Disk -Number ($Disk.Number) -IsOffline $true
}

}

function Set-DiskWriteable{

param(
            $Disk
            )

Set-Disk -Number ($Disk.Number) -IsReadonly $false

}

function Search-Volume{

param(
            $Partition
            )

Get-Volume | Where-Object{$Partition.AccessPaths -like $_.ObjectId}      

}

function Set-Initialized{

param(
            $Disk,
            $PartitionStyle
            )

$Disk| Initialize-Disk -PartitionStyle $PartitionStyle -Confirm:$false -PassThru
}

function Convert-PartitionStyle{

param(
            $Disk,
            $PartitionStyle
            )

Invoke-Expression "'Select Disk $($Disk.Number)','Convert $($PartitionStyle)' | diskpart"
}

function Manage-ShellHWService{

param(
            $action
            )

switch($action){
Stop {Stop-Service -Name ShellHWDetection -PassThru -ErrorAction Stop}
Start {Start-Service -Name ShellHWDetection -PassThru -ErrorAction Stop}
Check {(Get-Service ShellHWDetection -ErrorAction Stop).Status -eq "Running"}
default {throw "Neither '-Stop', '-Start' nor 'Check' switch was passed to the function when invoked, without the switches the service can not be maintained"}
}
}

function Create-Partition{

param(
            $Disk,
            $SetDriveLetter
            )

$Disk | New-Partition -UseMaximumSize -DriveLetter $SetDriveLetter
}

function Create-Volume{

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

[hashtable]$ParaVol = @{
                                            FileSystem = $FileSystem
                                            NewFileSystemLabel = $FileSystemLabel
                                            AllocationUnitSize = $Alloc
}

if($FileSystem -eq "ntfs"){

        if(-not $FileSystemLargeFRS){
                $Volume | Format-Volume @ParaVol -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }
        else{
                $Volume | Format-Volume @ParaVol -UseLargeFRS -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }

}
elseif($FileSystem -eq "refs"){
$Volume | Format-Volume @ParaVol -SetIntegrityStreams $FileSystemIntegrityStreams -Force -Confirm:$false
}

}

# Define script environment variables
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

# Parse arguments
$params = Parse-Args -arguments $args -supports_check_mode $true

# Create a new result object
$result = @{
    changed = $false
    search_log = @{
                                disk=@{}
                                existing_volumes=@{}
                                existing_partitions=@{}
                                }
    change_log = @{
                                convert_options=@{}
                                }
    general_log = @{}
    parameters = @{}
    switches = @{}
}

## Extract each attributes into a variable
# Find attributes
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$Size = Get-AnsibleParam -obj $params -name "size" -type "str/int" -failifempty $true
$FindPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_select" -type "str" -default "raw" -ValidateSet "raw","mbr","gpt"
$OperationalStatus = Get-AnsibleParam -obj $params -name "operational_status" -type "str" -default "offline" -ValidateSet "offline","online"
$ReadOnly = Get-AnsibleParam -obj $params -name "read_only" -default $true -type "bool"
$Number = Get-AnsibleParam -obj $params -name "number" -type "str/int"

# Set attributes partition
$SetPartitionStyle = Get-AnsibleParam -obj $params -name "partition_style_set" -type "str" -default "gpt" -ValidateSet "gpt","mbr"
$DriveLetter = Get-AnsibleParam -obj $params -name "drive_letter" -type "str" -default "e"
# Set attributes partition
$FileSystem = Get-AnsibleParam -obj $params -name "file_system" -type "str" -default "ntfs" -ValidateSet "ntfs","refs"
$Label = Get-AnsibleParam -obj $params -name "label" -type "str" -default "ansible_disk"
$AllocUnitSize = Get-AnsibleParam -obj $params -name "allocation_unit_size" -type "str/int" -default 4 -ValidateSet 4,8,16,32,64
$LargeFRS = Get-AnsibleParam -obj $params -name "large_frs" -default $false -type "bool"
$ShortNames = Get-AnsibleParam -obj $params -name "short_names" -default $false -type "bool"
$IntegrityStreams = Get-AnsibleParam -obj $params -name "integrity_streams" -default $false -type "bool"

# Convert option variable
if(($Size.GetType()).Name -eq 'String'){
        try{
            [int32]$Size = [convert]::ToInt32($Size, 10)
        }
        catch{
            $result.general_log.convert_validate_options = "failed"
            Fail-Json -obj $result -message "Failed to convert option variable from string to int: $($_.Exception.Message)"
        }
        $result.change_log.convert_options.size = "Converted option variable from string to int"     
}
else{
    $result.change_log.convert_options.size = "No convertion of option variable needed"
}

if(($AllocUnitSize.GetType()).Name -eq 'String'){
        try{
            [int32]$AllocUnitSize = [convert]::ToInt32($AllocUnitSize, 10)
        }
        catch{
            $result.general_log.convert_validate_options = "failed"
            Fail-Json -obj $result -message "Failed to convert option variable from string to int: $($_.Exception.Message)"
        }
        $result.change_log.convert_options.allocation_unit_size = "Converted option variable from string to int"   
}
else{
    $result.change_log.convert_options.allocation_unit_size = "No convertion of option variable needed"
}

if($Number -ne $null){
    if(($Number.GetType()).Name -eq 'String'){
            try{
                [int32]$Number = [convert]::ToInt32($Number, 10)
            }
            catch{
                $result.general_log.convert_validate_options = "failed"
                Fail-Json -obj $result -message "Failed to convert option variable from string to int: $($_.Exception.Message)"
            }
            $result.change_log.convert_options.number = "Converted option variable from string to int"     
    }
    else{
        $result.change_log.convert_options.number = "No convertion of option variable needed"
    }
}
else{
    $result.change_log.convert_options.number = "No number option used, no convertion needed"
}

$result.general_log.convert_validate_options = "successful"

# Rescan disks
try{
    Invoke-Expression '"rescan" | diskpart' | Out-Null
}
catch{
    $result.general_log.rescan_disks = "failed"
}

$result.general_log.rescan_disks = "successful"

[hashtable]$ParamsDisk = @{
                          DiskSize = $Size
                          PartitionStyle = $FindPartitionStyle
                          OperationalStatus = $OperationalStatus
                          ReadOnly = $ReadOnly
                          Number = $Number
                          }

# Search disk
try{
    $disk = Search-Disk @ParamsDisk
}
catch{
    $result.general_log.search_disk = "failed"
    Fail-Json -obj $result -message "Failed to search and/or select the disk with the specified parameter options: $($_.Exception.Message)"
}

if($disk){
            $diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
                                                      if($diskcount -ge 2){
                                                                                        $disk = $disk[0]
                                                                                        $result.search_log.disk.disks_found = "$diskcount"
                                                                                        $result.search_log.disk.disk_number_chosen = "$([string]$disk.Number)"
                                                                                        $result.search_log.disk.location = "$([string]$disk.Location)"
                                                                                        $result.search_log.disk.serial_number = "$([string]$disk.SerialNumber)"
                                                                                        $result.search_log.disk.unique_id = "$([string]$disk.UniqueId)"
                                                                                        $result.search_log.disk.operational_status = "$([string]$DOperSt = $disk.OperationalStatus)$DOperSt"
                                                                                        $result.search_log.disk.partition_style = "$([string]$DPartStyle = $disk.PartitionStyle)$DPartStyle"
                                                                                        $result.search_log.disk.read_only = "$([string]$DROState = $disk.IsReadOnly)$DROState"
                                                                                        }
                                                      else{
                                                            $result.search_log.disk.disks_found = "$diskcount"
                                                            $result.search_log.disk.disk_number_chosen = "$([string]$disk.Number)"
                                                            $result.search_log.disk.location = "$([string]$disk.Location)"
                                                            $result.search_log.disk.serial_number = "$([string]$disk.SerialNumber)"
                                                            $result.search_log.disk.unique_id = "$([string]$disk.UniqueId)"
                                                            $result.search_log.disk.operational_status = "$([string]$DOperSt = $disk.OperationalStatus)$DOperSt"
                                                            $result.search_log.disk.partition_style = "$([string]$DPartStyle = $disk.PartitionStyle)$DPartStyle"
                                                            $result.search_log.disk.read_only = "$([string]$DROState = $disk.IsReadOnly)$DROState"
                                                              }
}
else{
        $result.search_log.disk.disks_found = "0"
        Fail-Json -obj $result -message "No disk could be found and selected with the specified parameter options"
}

$result.general_log.search_disk = "successful"

# Check and set Operational Status and Read-Only state
$SetOnline = $false
if(-not $check_mode){
                if($DPartStyle -eq "RAW"){     
                        $result.change_log.operational_status_disk = "No changes because partition style is $($DPartStyle) and disk will be set to online in intialization part"                        
                        $result.general_log.set_operational_status = "successful"                       
                        if($DROState -ne "True"){
                                    $result.change_log.read_only_disk = "No changes because read-only state is 'False' (writeable)"
                                    $result.general_log.set_read_only_false = "successful"
                        }
                        else{
                            try{
                                Set-DiskWriteable -Disk $disk
                            }
                            catch{
                                        $result.general_log.set_read_only_false = "failed"
                                        $result.change_log.read_only_disk = "Disk failed to set from read-only to writeable state"
                                        Fail-Json -obj $result -message "Failed to set the disk from read-only to writeable state: $($_.Exception.Message)"
                                        }
                            $result.change_log.read_only_disk = "Disk set from read-only to writeable state"
                            $result.general_log.set_read_only_false = "successful"
                            $result.changed = $true
                        }
                }
                else{
                        if($DOperSt -eq "Online"){               
                                    $result.change_log.operational_status_disk = "No changes because disk is online"
                                    $result.general_log.set_operational_status = "successful"
                                    if($DROState -ne "True"){
                                                $result.change_log.read_only_disk = "No changes because read-only state is 'False' (writeable)"
                                                $result.general_log.set_read_only_false = "successful"
                                    }
                                    else{
                                        try{
                                            Set-DiskWriteable -Disk $disk
                                        }
                                        catch{
                                                    $result.general_log.set_read_only_false = "failed"
                                                    $result.change_log.read_only_disk = "Disk failed to set from read-only to writeable state"
                                                    Fail-Json -obj $result -message "Failed to set the disk from read-only to writeable state: $($_.Exception.Message)"
                                                    }
                                        $result.change_log.read_only_disk = "Disk set from read-only to writeable state"
                                        $result.general_log.set_read_only_false = "successful"
                                        $result.changed = $true
                                    }       
                        }
                        else{
                                try{
                                    Set-OperationalStatus -Online -Disk $disk
                                }
                                catch{
                                            $result.general_log.set_operational_status = "failed"
                                            $result.change_log.operational_status_disk = "Disk failed to set online"
                                            Fail-Json -obj $result -message "Failed to set the disk online: $($_.Exception.Message)"
                                            }
                                $result.change_log.operational_status_disk = "Disk set online"
                                $result.general_log.set_operational_status = "successful"
                                $result.changed = $true
                                $SetOnline = $true
                
                                try{
                                    Set-DiskWriteable -Disk $disk
                                }
                                catch{
                                            $result.general_log.set_read_only_false = "failed"
                                            $result.change_log.read_only_disk = "Disk failed to set from read-only to writeable state"
                                            Fail-Json -obj $result -message "Failed to set the disk from read-only to writeable state: $($_.Exception.Message)"
                                            }
                                $result.change_log.read_only_disk = "Disk set from read-only to writeable state"
                                $result.general_log.set_read_only_false = "successful"
                                $result.changed = $true
                        }      
                }
}
else{
        $result.change_log.operational_status_disk = "check_mode"
        $result.change_log.read_only_disk = "check_mode"
        $result.general_log.set_operational_status = "check_mode"
        $result.general_log.set_read_only_false = "check_mode"
}

# Check volumes and partitions
[string]$PartNumber = $disk.NumberOfPartitions
$OPStatusFailed = $false
if($PartNumber -ge 1){
                try{
                     $Fpartition = Get-Partition -DiskNumber ($disk.Number)
                }
                catch{
                        $result.general_log.check_volumes_partitions = "failed"
                        Fail-Json -obj $result -message "General error while searching for partitions on the selected disk: $($_.Exception.Message)"
                }

                try{
                    $volume = Search-Volume -Partition $Fpartition
                }
                catch{
                        $result.general_log.check_volumes_partitions = "failed"
                        if($SetOnline){
                                        try{
                                            Set-OperationalStatus -Offline -Disk $disk
                                        }
                                        catch{
                                                $OPStatusFailed = $true
                                        }
                                        if(-not $OPStatusFailed){
                                                        $result.general_log.set_operational_status = "successful"
                                                        $result.change_log.operational_status = "Disk set online and now offline again"
                                                        $result.changed = $true
                                        }
                                        else{
                                                $result.general_log.set_operational_status = "failed"
                                                $result.change_log.operational_status = "Disk failed to set offline again"
                                        }
                        }
                        else{
                              $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                        }
                        Fail-Json -obj $result -message "General error while searching for volumes on the selected disk: $($_.Exception.Message)"
                            }
                

                if(-not $volume){
                                        $result.search_log.existing_volumes.volumes_found = "0"
                                                $result.search_log.existing_partitions.partitions_found = "$PartNumber"
                                                $result.search_log.existing_partitions.partitions_types = "$([string]$Fpartition.Type)"
                                                $result.general_log.check_volumes_partitions = "failed"
                                                if($SetOnline){
                                                            try{
                                                                Set-OperationalStatus -Offline -Disk $disk
                                                            }
                                                            catch{
                                                                    $OPStatusFailed = $true
                                                            }
                                                            if(-not $OPStatusFailed){
                                                                            $result.general_log.set_operational_status = "successful"
                                                                            $result.change_log.operational_status = "Disk set online and now offline again"
                                                                            $result.changed = $true
                                                            }
                                                            else{
                                                                    $result.general_log.set_operational_status = "failed"
                                                                    $result.change_log.operational_status = "Disk failed to set offline again"
                                                            }
                                                }
                                                else{
                                                        $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                                                }
                                                Fail-Json -obj $result -message "Existing partitions found on the selected disk"
                }
                else{
                    $result.search_log.existing_volumes.volumes_found = "$((($volume | Measure-Object).Count).ToString())"
                    $result.search_log.existing_volumes.volumes_types = "$([string]$volume.FileSystem)"
                    $result.search_log.existing_partitions.partitions_found = "$PartNumber"
                    $result.search_log.existing_partitions.partitions_types = "$([string]$Fpartition.Type)"

                    $result.general_log.check_volumes_partitions = "failed"
                    if($SetOnline){
                               try{
                                    Set-OperationalStatus -Offline -Disk $disk
                                }
                                catch{
                                        $OPStatusFailed = $true
                                }
                                if(-not $OPStatusFailed){
                                                $result.general_log.set_operational_status = "successful"
                                                $result.change_log.operational_status = "Disk set online and now offline again"
                                                $result.changed = $true
                                }
                                else{
                                        $result.general_log.set_operational_status = "failed"
                                        $result.change_log.operational_status = "Disk failed to set offline again"
                                }
                    }
                    else{
                            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                    }
                    Fail-Json -obj $result -message "Existing volumes found on the selected disk"
                }
 
}
else{
    $result.search_log.existing_volumes.volumes_found = "0"
    $result.search_log.existing_partitions.partitions_found = "$PartNumber"
}

$result.general_log.check_volumes_partitions = "successful"


# Check set parameters
[char]$DriveLetter = [convert]::ToChar($DriveLetter)
if((Get-Partition).DriveLetter -notcontains $DriveLetter){
                                                                $result.parameters.drive_letter_set = "$DriveLetter"
                                                                $result.parameters.drive_letter_used = "no"
}
else{
    $result.parameters.drive_letter_set = "$DriveLetter"
    $result.parameters.drive_letter_used = "yes"
    $result.general_log.check_parameters = "failed"
    Fail-Json -obj $result -message "Option drive_letter with value $DriveLetter is already set on another partition on this client which is not allowed"
}

if($DriveLetter -ne "C" -and $DriveLetter -ne "D"){
                                                                                    $result.parameters.forbidden_drive_letter_set = "no"
}
else{
    $result.parameters.forbidden_drive_letter_set = "yes"
    $result.general_log.check_parameters = "failed"
    Fail-Json -obj $result -message "Option drive_letter with value $DriveLetter contains protected letters C or D"
}

if($FileSystem -eq "ntfs"){
                                                $result.parameters.file_system = "$FileSystem"
                                                if($Size -le 256000){
                                                                                    $result.parameters.size = "$($Size)gb"
                                                                                    $result.parameters.allocation_unit_size = "$AllocUnitSize KB"
                                                }
                                                else{
                                                    $result.parameters.size = "$($Size)gb"
                                                    $result.general_log.check_parameters = "failed"
                                                    if($SetOnline){
                                                                try{
                                                                    Set-OperationalStatus -Offline -Disk $disk
                                                                }
                                                                catch{
                                                                        $OPStatusFailed = $true
                                                                }
                                                                if(-not $OPStatusFailed){
                                                                                $result.general_log.set_operational_status = "successful"
                                                                                $result.change_log.operational_status = "Disk set online and now offline again"
                                                                                $result.changed = $true
                                                                }
                                                                else{
                                                                        $result.general_log.set_operational_status = "failed"
                                                                        $result.change_log.operational_status = "Disk failed to set offline again"
                                                                }
                                                    }
                                                    else{
                                                            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                                                    }
                                                    Fail-Json -obj $result -message "Option size with value $Size GB is not a valid size for NTFS, the disk can not be not formatted with this file system"
                                                }
}
elseif($FileSystem -eq "refs"){
                                                    $result.parameters.file_system = "$FileSystem"
                                                    if($AllocUnitSize -ne 64){
                                                                                                $result.parameters.size = "$($Size)gb"
                                                                                                $AllocUnitSize = 64
                                                                                                $result.parameters.allocation_unit_size = "$($AllocUnitSize)kb_adjusted_refs"                                                  
                                                    }
                                                    else{
                                                        $result.parameters.size = "$($Size)gb"
                                                        $result.parameters.allocation_unit_size = "$($AllocUnitSize)_kb"   
                                                    }
}

$result.general_log.check_parameters = "successful"

# Check set switches
if($LargeFRS){
                        $result.switches.large_frs = "enabled"
                        if($FileSystem -ne "refs"){
                                                                    $result.switches.large_frs = "enabled_activated_no_refs"
                                                                    }
                        else{
                                $result.switches.large_frs = "enabled_deactivated_refs"
                                }
}
else{
    $result.switches.large_frs = "disabled"
}

if($ShortNames){
                        $result.switches.short_names = "enabled"
                        if($FileSystem -ne "refs"){
                                                                    $result.switches.short_names = "enabled_activated_no_refs)"
                                                                    }
                        else{
                                $result.switches.short_names = "enabled_deactivated_refs"
                                }
}
else{
    $result.switches.short_names = "disabled"
}

if($IntegrityStreams){
                        $result.switches.integrity_streams = "enabled"
                        if($FileSystem -eq "refs"){
                                                                     $result.switches.integrity_streams = "enabled_activated_no_ntfs"
                                                                    }
                        else{
                                $result.switches.integrity_streams = "enabled_deactivated_ntfs"
                                }
}
else{
    $result.switches.integrity_streams = "disabled"
}

$result.general_log.check_switches = "successful"

# Initialize / convert disk
if($DPartStyle -eq "RAW"){
                            if(-not $check_mode){
                                            try{
                                                $Initialize = Set-Initialized -Disk $disk -PartitionStyle $SetPartitionStyle
                                            }
                                            catch{
                                                    $result.general_log.initialize_convert_disk = "failed"
                                                    $result.change_log.initialize_disk = "Disk initialization failed - Partition style $DPartStyle (partition_style_select) could not be initalized to $SetPartitionStyle (partition_style_set)"
                                                    Fail-Json -obj $result -message "Failed to initialize the disk: $($_.Exception.Message)"
                                            }
                                            $result.change_log.initialize_disk = "Disk initialization successful - Partition style $DPartStyle (partition_style_select) was initalized to $SetPartitionStyle (partition_style_set)"
                                            $result.changed = $true
                            }
                            else{
                                   $result.change_log.initialize_disk = "check_mode"
                            }
}
else{
    # Convert disk
    if($DPartStyle -ne $SetPartitionStyle){
            if(-not $check_mode){
                            try{
                                $Convert = Convert-PartitionStyle -Disk $disk -PartitionStyle $SetPartitionStyle
                            }
                            catch{
                                $result.general_log.initialize_convert_disk = "failed"
                                $result.change_log.convert_disk = "Partition style $DPartStyle (partition_style_select) could not be converted to $SetPartitionStyle (partition_style_set)"
                                    if($SetOnline){
                                               try{
                                                    Set-OperationalStatus -Offline -Disk $disk
                                                }
                                                catch{
                                                        $OPStatusFailed = $true
                                                }
                                                if(-not $OPStatusFailed){
                                                                $result.general_log.set_operational_status = "successful"
                                                                $result.change_log.operational_status = "Disk set online and now offline again"
                                                                $result.changed = $true
                                                }
                                                else{
                                                        $result.general_log.set_operational_status = "failed"
                                                        $result.change_log.operational_status = "Disk failed to set offline again"
                                                }
                                    }
                                    else{
                                            $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                                    }
                                Fail-Json -obj $result -message "Failed to convert the disk: $($_.Exception.Message)"
                            }
                            $result.change_log.convert_disk = "Partition style $DPartStyle (partition_style_select) was converted to $SetPartitionStyle (partition_style_set)"
                            $result.changed = $true
            }
            else{
                   $result.general_log.initialize_convert_disk = "check_mode" 
            }
    }
    else{
    # No convertion
    $result.change_log.convert_disk = "$SetPartitionStyle (partition_style_set) is equal to selected partition style of disk, no convertion needed"
    }
}

if(-not $check_mode){
            $result.general_log.initialize_convert_disk = "successful"
}
else{
        $result.general_log.initialize_convert_disk = "check_mode"
}

# Maintain ShellHWService (not module terminating)
$StopSuccess = $false
$StopFailed = $false
$StartFailed = $false
$CheckFailed = $false
try{
    $Check = Manage-ShellHWService -Action "Check"
}
catch{
        $CheckFailed = $true
}

if($Check){
                $result.search_log.shellhw_service_state = "running"
                if(-not $check_mode){
                                try{
                                    Manage-ShellHWService -Action "Stop"
                                    }
                                catch{
                                        $StopFailed = $true
                                          }
                                if(-not $StopFailed){
                                            $result.general_log.maintain_shellhw_service = "successful"
                                            $result.change_log.shellhw_service_state = "Set from 'Running' to 'Stopped'"
                                            $StopSuccess = $true
                                            $result.changed = $true
                                }
                                else{
                                        $result.general_log.maintain_shellhw_service = "failed"
                                        $result.change_log.shellhw_service_state = "Could not be set from 'Running' to 'Stopped'"
                                }
                }
                else{
                        $result.change_log.shellhw_service_state = "check_mode"
                        $result.general_log.maintain_shellhw_service = "check_mode"
                }
}
elseif($CheckFailed){
        $result.search_log.shellhw_service_state = "check_failed"
        $result.general_log.maintain_shellhw_service = "failed"
}
else{
    $result.search_log.shellhw_service_state = "stopped"
    if(-not $check_mode){
                    $result.general_log.maintain_shellhw_service = "successful"
    }
    else{
        $result.general_log.maintain_shellhw_service = "check_mode"
    }
}

# Part disk
if(-not $check_mode){
                try{
                    $CPartition = Create-Partition -Disk $disk -SetDriveLetter $DriveLetter
                }
                catch{
                        $result.general_log.create_partition = "failed"
                        $result.change_log.partitioning = "Partition was failed to create on disk with partition style $SetPartitionStyle"
                            if($SetOnline){
                                    try{
                                        Set-OperationalStatus -Offline -Disk $disk
                                    }
                                    catch{
                                            $OPStatusFailed = $true
                                    }
                                    if(-not $OPStatusFailed){
                                                    $result.general_log.set_operational_status = "successful"
                                                    $result.change_log.operational_status = "Disk set online and now offline again"
                                                    $result.changed = $true
                                    }
                                    else{
                                            $result.general_log.set_operational_status = "failed"
                                            $result.change_log.operational_status = "Disk failed to set offline again"
                                    }
                            }
                            else{
                                    $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                            }
                            if($StopSuccess){
                                                        try{
                                                            Manage-ShellHWService -Action "Start"
                                                            }
                                                        catch{
                                                                $StartFailed = $true
                                                                    }
                                                        if(-not $StartFailed){
                                                                    $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                                                                    $result.changed = $true
                                                        }
                                                        else{
                                                                $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                                                                $result.general_log.maintain_shellhw_service = "failed"             
                                                        }
                            }
                            elseif($CheckFailed){
                                    $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
                            }
                            else{
                                    $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"
                            }
                        Fail-Json -obj $result -message "Failed to create the partition on the disk: $($_.Exception.Message)"
                }

                $result.change_log.partitioning = "Initial partition $($CPartition.Type) was created successfully on partition style $SetPartitionStyle"
                $result.general_log.create_partition = "successful"
                $result.changed = $true
}
else{
        $result.change_log.partitioning = "check_mode"
        $result.general_log.create_partition = "check_mode"
}

# Create volume
if(-not $check_mode){
                [hashtable]$ParamsVol = @{
                                                                    Volume = $CPartition
                                                                    FileSystem = $FileSystem
                                                                    FileSystemLabel = $Label
                                                                    FileSystemAllocUnitSize = $AllocUnitSize
                                                                    FileSystemLargeFRS = $LargeFRS
                                                                    FileSystemShortNames = $ShortNames
                                                                    FileSystemIntegrityStreams = $IntegrityStreams
                                                                    }

                try{
                    $CVolume = Create-Volume @ParamsVol
                }
                catch{
                        $result.general_log.create_volume = "failed"
                        $result.change_log.formatting = "Volume was failed to create on disk with partition $($CPartition.Type)"
                            if($SetOnline){
                                    try{
                                        Set-OperationalStatus -Offline -Disk $disk
                                    }
                                    catch{
                                            $OPStatusFailed = $true
                                    }
                                    if(-not $OPStatusFailed){
                                                    $result.general_log.set_operational_status = "successful"
                                                    $result.change_log.operational_status = "Disk set online and now offline again"
                                                    $result.changed = $true
                                    }
                                    else{
                                            $result.general_log.set_operational_status = "failed"
                                            $result.change_log.operational_status = "Disk failed to set offline again"
                                    }
                            }
                            else{
                                    $result.change_log.operational_status = "Disk was online already and need not to be set offline"  
                            }
                            if($StopSuccess){
                                                        try{
                                                            Manage-ShellHWService -Action "Start"
                                                            }
                                                        catch{
                                                                $StartFailed = $true
                                                                    }
                                                        if(-not $StartFailed){
                                                                    $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                                                                    $result.changed = $true
                                                        }
                                                        else{
                                                                $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                                                                $result.general_log.maintain_shellhw_service = "failed"        
                                                        }
                            }
                            elseif($CheckFailed){
                                    $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
                            }
                            else{
                                    $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"  
                            }
                        Fail-Json -obj $result -message "Failed to create the volume on the disk: $($_.Exception.Message)"
                }

                $result.change_log.formatting = "Volume $($CVolume.FileSystem) was created successfully on partition $($CPartition.Type)"
                $result.general_log.create_volume = "successful"
                $result.changed = $true
}
else{
        $result.change_log.formatting = "check_mode"
        $result.general_log.create_volume = "check_mode"
}

# Finally check if ShellHWService needs to be started again
if(-not $check_mode){
                if($StopSuccess){
                                            try{
                                                Manage-ShellHWService -Action "Start"
                                                }
                                            catch{
                                                    $StartFailed = $true
                                                        }
                                            if(-not $StartFailed){
                                                        $result.change_log.shellhw_service_state = "Set from 'Stopped' to 'Running' again"
                                                        $result.changed = $true
                                            }
                                            else{
                                                    $result.change_log.shellhw_service_state = "Could not be set from 'Stopped' to 'Running' again"
                                                    $result.general_log.maintain_shellhw_service = "failed"
                                            }
                }
                elseif($CheckFailed){
                        $result.change_log.shellhw_service_state = "Because service check has failed no starting action will be performed"
                }
                else{
                        $result.change_log.shellhw_service_state = "Service was stopped already and need not to be started again"  
                }
}

Exit-Json -obj $result
