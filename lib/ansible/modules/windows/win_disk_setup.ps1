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
    $OperationalStatus
)

$DiskSize = $DiskSize *1GB

Get-Disk -ErrorAction SilentlyContinue | Where-Object {($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.Size -eq $DiskSize)}

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
default {throw "Neither '-Stop', '-Start' nor 'Check' switch was passed to the function when invoked. Without the switches the service can not be maintained."}
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

if($FileSystem -eq "NTFS"){

        if(!($FileSystemLargeFRS)){
                $Volume | Format-Volume @ParaVol -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }
        else{
                $Volume | Format-Volume @ParaVol -UseLargeFRS -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }

}
elseif($FileSystem -eq "ReFs"){
$Volume | Format-Volume @ParaVol -SetIntegrityStreams $FileSystemIntegrityStreams -Force -Confirm:$false
}

}

$params = Parse-Args $args;

# Create a new result object
$result = [pscustomobject]@{changed=$false;log=[pscustomobject]@{};generallog=[pscustomobject]@{};parameters=[pscustomobject]@{};switches=[pscustomobject]@{}}

## Extract each attributes into a variable
# Find attributes
$Size = Get-Attr -obj $params -name "FindSize" -resultobj $result -failifempty $true
$FindPartitionStyle = Get-Attr -obj $params -name "FindPartitionStyle" -default "RAW" -ValidateSet "RAW","MBR","GPT" -resultobj $result -failifempty $false
$OperationalStatus = Get-Attr -obj $params -name "FindOperationalStatus" -default "Offline" -ValidateSet "Offline","Online" -resultobj $result -failifempty $false

# Set attributes partition
$SetPartitionStyle = Get-Attr -obj $params -name "SetPartitionStyle" -default "GPT" -ValidateSet "GPT","MBR" -resultobj $result -failifempty $false
$DriveLetter = Get-Attr -obj $params -name "SetDriveLetter" -default "E" -resultobj $result -failifempty $false
# Set attributes partition
$FileSystem = Get-Attr -obj $params -name "SetFileSystem" -default "NTFS" -ValidateSet "NTFS","ReFs" -resultobj $result -failifempty $false
$Label = Get-Attr -obj $params -name "SetLabel" -default "AdditionalDisk" -resultobj $result -failifempty $false
$AllocUnitSize = Get-Attr -obj $params -name "SetAllocUnitSize" -default "4" -ValidateSet "4","8","16","32","64" -resultobj $result -failifempty $false
$LargeFRS = Get-Attr -obj $params -name "SetLargeFRS" -default $false -type "bool" -resultobj $result -failifempty $false
$ShortNames = Get-Attr -obj $params -name "SetShortNames" -default $false -type "bool" -resultobj $result -failifempty $false
$IntegrityStreams = Get-Attr -obj $params -name "SetIntegrityStreams" -default $false -type "bool" -resultobj $result -failifempty $false

# Convert variable for disk size
[int32]$DSize = [convert]::ToInt32($Size, 10)

# Define script environment variables
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

# Rescan disks
try{
Invoke-Expression '"rescan" | diskpart' | Out-Null
   }
catch{
Set-Attr $result.generallog "Rescan disks" "Failed"
}

Set-Attr $result.generallog "Rescan disks" "Successful"

[hashtable]$ParamsDisk = @{
                          DiskSize = $DSize
                          PartitionStyle = $FindPartitionStyle
                          OperationalStatus = $OperationalStatus
                          }

# Search disk
try{
$disk = Search-Disk @ParamsDisk
}
catch{
Set-Attr $result.generallog "Search disk" "Failed"
Fail-Json $result $_
}

if($disk){
            $diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
                                                      if($diskcount -ge 2){
                                                                                        $disk = $disk[0]
                                                                                        [string]$DiskNumber = $disk.Number
                                                                                        [string]$Location = $disk.Location
                                                                                        [string]$SerialN = $disk.SerialNumber
                                                                                        [string]$UniqueID = $disk.UniqueId
                                                                                        Set-Attr $result.log "Disk" "Disks found: $diskcount, choosed: Disk number: $DiskNumber, Location: $Location, Serial Number: $SerialN, Unique ID: $UniqueID"
                                                                                        }
                                                      else{
                                                              [string]$DiskNumber = $disk.Number
                                                              [string]$Location = $disk.Location
                                                              [string]$SerialN = $disk.SerialNumber
                                                              [string]$UniqueID = $disk.UniqueId
                                                              Set-Attr $result.log "Disk" "Disks found: $diskcount, Disk number: $DiskNumber, Location: $Location, Serial Number: $SerialN, Unique ID: $UniqueID"
                                                              }
}
else{
        Set-Attr $result.log "Disk" "Disks found: 0, Disk number: n.a., Location: n.a., Serial Number: n.a., Unique ID: n.a."
        Set-Attr $result.generallog "Search disk" "Failed"
        Fail-Json $result "No disk found (size or property is wrong or disk is not attached)."
}

Set-Attr $result.generallog "Search disk" "Successful"

# Check and set Operational Status and writeable state
$SetOnline = $false
[string]$DPartStyle = $disk.PartitionStyle
if($DPartStyle -eq "RAW"){
    Set-Attr $result.log "Operational Status" "Disk set not online because partition style is $DPartStyle"
    Set-Attr $result.log "Disk Writeable" "Disk need not set to writeable because partition style is $DPartStyle"
}
else{
        if($disk.OperationalStatus -eq "Online"){
                Set-Attr $result.log "Operational Status" "Disk is online already"
        }
        else{
                try{
                    Set-OperationalStatus -Online -Disk $disk
                }
                catch{
                            Set-Attr $result.generallog "Set Operational Status" "Failed"
                            Set-Attr $result.log "Operational Status" "Disk failed to set online"
                            Fail-Json $result $_
                            }
                Set-Attr $result.log "Operational Status" "Disk set online"
                Set-Attr $result "changed" $true;
                $SetOnline = $true   
                
                try{
                    Set-DiskWriteable -Disk $disk
                }
                catch{
                            Set-Attr $result.generallog "Set Writeable Status" "Failed"
                            Set-Attr $result.log "Disk Writeable" "Disk failed to set from read-only to writeable"
                            Fail-Json $result $_
                            }
                Set-Attr $result.log "Disk Writeable" "Disk set set from read-only to writeable"
                Set-Attr $result "changed" $true;                               
        }      
}

Set-Attr $result.generallog "Set Operational Status" "Successful"
Set-Attr $result.generallog "Set Writeable Status" "Successful"

# Check volumes and partitions
[string]$PartNumber = $disk.NumberOfPartitions
$OPStatusFailed = $false
if($disk.NumberOfPartitions -ge 1){

                try{
                     $Fpartition = Get-Partition -DiskNumber ($disk.Number)
                }
                catch{
                        Set-Attr $result.generallog "Check volumes / partitions" "Failed"
                        Fail-Json $result "General error while getting partitions of found disk."
                }

                [string]$PartType = $Fpartition.Type

                try{
                    $volume = Search-Volume -Partition $Fpartition
                }
                catch{
                        Set-Attr $result.generallog "Check volumes / partitions" "Failed"
                        if($SetOnline){
                                        try{
                                            Set-OperationalStatus -Offline -Disk $disk
                                        }
                                        catch{
                                                $OPStatusFailed = $true
                                        }
                                        if(!$OPStatusFailed){
                                                        Set-Attr $result.generallog "Set Operational Status" "Successful"
                                                        Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                                        Set-Attr $result "changed" $true;
                                        }
                                        else{
                                                Set-Attr $result.generallog "Set Operational Status" "Failed"
                                                Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                                        }
                        }
                        else{
                              Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
                        }
                        Fail-Json $result $_
                            }
                

                if(!$volume){
                                        Set-Attr $result.log "Existing volumes" "Volumes found: 0"
                                                Set-Attr $result.log "Existing partitions" "Partition Style: $DPartStyle, Partitions found: $PartNumber, Partition types: $PartType"
                                                Set-Attr $result.generallog "Check volumes / partitions" "Failed"
                                                if($SetOnline){
                                                            try{
                                                                Set-OperationalStatus -Offline -Disk $disk
                                                            }
                                                            catch{
                                                                    $OPStatusFailed = $true
                                                            }
                                                            if(!$OPStatusFailed){
                                                                            Set-Attr $result.generallog "Set Operational Status" "Successful"
                                                                            Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                                                            Set-Attr $result "changed" $true;
                                                            }
                                                            else{
                                                                    Set-Attr $result.generallog "Set Operational Status" "Failed"
                                                                    Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                                                            }
                                                }
                                                else{
                                                        Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
                                                }
                                                Fail-Json $result "Existing terminating partitions recognized on found disk."
                }
                else{
                    [string]$VolNumber = ($volume | Measure-Object).Count 
                    [string]$VolType = $volume.FileSystemType
                    Set-Attr $result.log "Existing volumes" "Volumes found: $VolNumber" "Volume types: $VolType" "Partition Style: $DPartStyle, Partitions found: $PartNumber, Partition types: $PartType"
                    Set-Attr $result.generallog "Check volumes / partitions" "Failed"
                    if($SetOnline){
                               try{
                                    Set-OperationalStatus -Offline -Disk $disk
                                }
                                catch{
                                        $OPStatusFailed = $true
                                }
                                if(!$OPStatusFailed){
                                                Set-Attr $result.generallog "Set Operational Status" "Successful"
                                                Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                                Set-Attr $result "changed" $true;
                                }
                                else{
                                        Set-Attr $result.generallog "Set Operational Status" "Failed"
                                        Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                                }
                    }
                    else{
                            Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
                    }
                    Fail-Json $result "Existing volumes recognized on found disk."
                }
 
}
else{
    Set-Attr $result.log "Existing volumes" "Volumes found: 0"
    Set-Attr $result.log "Existing partitions" "Partition Style: $FindPartitionStyle, Partitions found: $PartNumber" 
}

Set-Attr $result.generallog "Check volumes / partitions" "Successful"


# Check set parameters
[char]$DriveLetter = [convert]::ToChar($DriveLetter)
if((Get-Partition).DriveLetter -notcontains $DriveLetter){
                                                                Set-Attr $result.parameters "Set drive letter" "$DriveLetter"
                                                                Set-Attr $result.parameters "Found same drive letter" "No"
}
else{
    Set-Attr $result.parameters "Set drive letter" "$DriveLetter"
    Set-Attr $result.parameters "Found same drive letter" "Yes"
    Set-Attr $result.generallog "Check parameters" "Failed"
    Fail-Json $result "Partition parameter 'SetDriveLetter' with value $DriveLetter is already set on another partition on this server which is not allowed."
}

if($DriveLetter -ne "C" -and $DriveLetter -ne "D"){
                                                                                    Set-Attr $result.parameters "Set forbidden drive letter C or D" "No"
}
else{
    Set-Attr $result.parameters "Set forbidden drive letter C or D" "Yes"
    Set-Attr $result.generallog "Check parameters" "Failed"
    Fail-Json $result "Partition parameter 'SetDriveLetter' with value $DriveLetter contains protected letters C or D."
}

if($FileSystem -eq "NTFS"){
                                                Set-Attr $result.parameters "File system" "$FileSystem"
                                                if($DSize -le 256000){
                                                                                    Set-Attr $result.parameters "Disks size" "$DSize GB"
                                                                                    Set-Attr $result.parameters "Allocation Unit size" "$AllocUnitSize KB"
                                                }
                                                else{
                                                    Set-Attr $result.parameters "Disks size" "$DSize GB"
                                                    Set-Attr $result.generallog "Check parameters" "Failed"
                                                    if($SetOnline){
                                                                try{
                                                                    Set-OperationalStatus -Offline -Disk $disk
                                                                }
                                                                catch{
                                                                        $OPStatusFailed = $true
                                                                }
                                                                if(!$OPStatusFailed){
                                                                                Set-Attr $result.generallog "Set Operational Status" "Successful"
                                                                                Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                                                                Set-Attr $result "changed" $true;
                                                                }
                                                                else{
                                                                        Set-Attr $result.generallog "Set Operational Status" "Failed"
                                                                        Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                                                                }
                                                    }
                                                    else{
                                                            Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
                                                    }
                                                    Fail-Json $result "Disk parameter 'FindSize' with value $DSize GB is not a valid size for NTFS. Disk will be findable but could be not formatted with this file system."
                                                }
}
elseif($FileSystem -eq "ReFs"){
                                                    Set-Attr $result.parameters "File system" "$FileSystem"
                                                    if($AllocUnitSize -ne 64){
                                                                                                $AllocUnitSize = 64
                                                                                                Set-Attr $result.parameters "Allocation Unit size" "$AllocUnitSize KB (adjusted for ReFs)"
                                                    }
                                                    else{
                                                        Set-Attr $result.parameters "Allocation Unit size" "$AllocUnitSize KB"
                                                    }
}

Set-Attr $result.generallog "Check parameters" "Successful"

# Check set switches
if($LargeFRS){
                        Set-Attr $result.switches "Large FRS" "Enabled"
                        if($FileSystem -ne "ReFs"){
                                                                    Set-Attr $result.switches "Large FRS" "Enabled - activated (no ReFs)"
                                                                    }
                        else{
                                $LargeFRS = $false # also works without setting false, because Create-Volume recognizes by itself, but will be kept for maybe later tasks
                                Set-Attr $result.switches "Large FRS" "Enabled - deactivated (ReFs)"
                                }
}
else{
    Set-Attr $result.switches "Large FRS" "Disabled"
}

if($ShortNames){
                        Set-Attr $result.switches "Short Names" "Enabled"
                        if($FileSystem -ne "ReFs"){
                                                                    Set-Attr $result.switches "Short Names" "Enabled - activated (no ReFs)"
                                                                    }
                        else{
                                $ShortNames = $false # also works without setting false, because Create-Volume recognizes by itself, but will be kept for maybe later tasks
                                Set-Attr $result.switches "Short Names" "Enabled - deactivated (ReFs)"
                                }
}
else{
    Set-Attr $result.switches "Short Names" "Disabled"
}

if($IntegrityStreams){
                        Set-Attr $result.switches "Integrity Streams" "Enabled"
                        if($FileSystem -eq "ReFs"){
#                                                                    Set-Attr $result.switches "Integrity Streams" "Enabled - activated (no NTFS)"
                                                                    }
                        else{
                                $IntegrityStreams = $false # also works without setting false, because Create-Volume recognizes by itself, but will be kept for maybe later tasks
                                Set-Attr $result.switches "Integrity Streams" "Enabled - deactivated (NTFS)"
                                }
}
else{
    Set-Attr $result.switches "Integrity Streams" "Disabled"
}

Set-Attr $result.generallog "Check switches" "Successful"

# Initialize / convert disk
if($DPartStyle -eq "RAW"){
                            try{
                                $Initialize = Set-Initialized -Disk $disk -PartitionStyle $SetPartitionStyle
                            }
                            catch{
                                    Set-Attr $result.generallog "Initialize / convert disk" "Failed"
                                    Set-Attr $result.log "Initialize disk" "Disk initialization failed - Partition style $DPartStyle (FindPartitionStyle) could not be initalized to $SetPartitionStyle (SetPartitionStyle)"
                                    Fail-Json $result $_
                            }
                            Set-Attr $result.log "Initialize disk" "Disk initialization successful - Partition style $DPartStyle (FindPartitionStyle) was initalized to $SetPartitionStyle (SetPartitionStyle)"
                            Set-Attr $result "changed" $true;
}
else{
    # Convert disk
    if($DPartStyle -ne $SetPartitionStyle){
    try{
        $Convert = Convert-PartitionStyle -Disk $disk -PartitionStyle $SetPartitionStyle
    }
    catch{
        Set-Attr $result.generallog "Initialize / convert disk" "Failed"
        Set-Attr $result.log "Convert disk (no initialization needed)" "Partition style $DPartStyle (FindPartitionStyle) could not be converted to $SetPartitionStyle (SetPartitionStyle)"
            if($SetOnline){
                       try{
                            Set-OperationalStatus -Offline -Disk $disk
                        }
                        catch{
                                $OPStatusFailed = $true
                        }
                        if(!$OPStatusFailed){
                                        Set-Attr $result.generallog "Set Operational Status" "Successful"
                                        Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                        Set-Attr $result "changed" $true;
                        }
                        else{
                                Set-Attr $result.generallog "Set Operational Status" "Failed"
                                Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                        }
            }
            else{
                    Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
            }
        Fail-Json $result $_
    }
    Set-Attr $result.log "Convert disk (no initialization needed)" "Partition style $DPartStyle (FindPartitionStyle) was converted to $SetPartitionStyle (SetPartitionStyle)"
    Set-Attr $result "changed" $true;
    }
    else{
    # No convertion
    Set-Attr $result.log "Convert disk (no initialization needed)" "$SetPartitionStyle (SetPartitionStyle) is equal to found partition style on disk, no convertion needed"
    }
}

Set-Attr $result.generallog "Initialize / convert disk" "Successful"

# Maintain ShellHWService (not module terminating)
$StopSuccess = $false
$StopFailed = $false
$StartFailed = $false
try{
    $Check = Manage-ShellHWService -Action "Check"
}
catch{
        Set-Attr $result.generallog "Maintain ShellHWService" "Failed"
        Set-Attr $result.log "ShellHWService State" "Check failed"
}

if($Check){
                try{
                    Manage-ShellHWService -Action "Stop"
                    }
                catch{
                        $StopFailed = $true
                          }
                if(!$StopFailed){
                            Set-Attr $result.generallog "Maintain ShellHWService" "Successful"
                            Set-Attr $result.log "ShellHWService State" "Set from Running to Stopped"
                            $StopSuccess = $true
                            Set-Attr $result "changed" $true;
                }
                else{
                        Set-Attr $result.generallog "Maintain ShellHWService" "Failed"
                        Set-Attr $result.log "ShellHWService State" "Could not be set from Running to Stopped"
                }
}
else{
Set-Attr $result.log "ShellHWService State" "Already Stopped"
Set-Attr $result.generallog "Maintain ShellHWService" "Successful"
}

# Part disk
try{
    $CPartition = Create-Partition -Disk $disk -SetDriveLetter $DriveLetter
}
catch{
        Set-Attr $result.generallog "Create Partition" "Failed"
        Set-Attr $result.log "Partitioning" "Partition was failed to create on disk with partition style $SetPartitionStyle"
            if($SetOnline){
                    try{
                        Set-OperationalStatus -Offline -Disk $disk
                    }
                    catch{
                            $OPStatusFailed = $true
                    }
                    if(!$OPStatusFailed){
                                    Set-Attr $result.generallog "Set Operational Status" "Successful"
                                    Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                    Set-Attr $result "changed" $true;
                    }
                    else{
                            Set-Attr $result.generallog "Set Operational Status" "Failed"
                            Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                    }
            }
            else{
                    Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
            }
            if($StopSuccess){
                                    try{
                                        Manage-ShellHWService -Action "Start"
                                        }
                                    catch{
                                            $StartFailed = $true
                                                }
                                    if(!$StartFailed){
                                                Set-Attr $result.log "ShellHWService State" "Set from Stopped to Running again"
                                                Set-Attr $result "changed" $true;
                                    }
                                    else{
                                            Set-Attr $result.generallog "Maintain ShellHWService" "Failed"
                                            Set-Attr $result.log "ShellHWService State" "Could not be set from Stopped to Running again"
                                    }
            }
            else{
                    Set-Attr $result.log "ShellHWService State" "Service was stopped already and need not to be started again"  
            }
        Fail-Json $result $_
}

Set-Attr $result.log "Partitioning" "Initial partition $($CPartition.Type) was created successfully on partition style $SetPartitionStyle"
Set-Attr $result.generallog "Create Partition" "Successful"
Set-Attr $result "changed" $true;

# Create volume
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
        Set-Attr $result.generallog "Create Volume" "Failed"
        Set-Attr $result.log "Formating" "Volume was failed to create on disk with partition $($CPartition.Type)"
            if($SetOnline){
                    try{
                        Set-OperationalStatus -Offline -Disk $disk
                    }
                    catch{
                            $OPStatusFailed = $true
                    }
                    if(!$OPStatusFailed){
                                    Set-Attr $result.generallog "Set Operational Status" "Successful"
                                    Set-Attr $result.log "Operational Status" "Disk set online and now offline again"
                                    Set-Attr $result "changed" $true;
                    }
                    else{
                            Set-Attr $result.generallog "Set Operational Status" "Failed"
                            Set-Attr $result.log "Operational Status" "Disk failed to set offline again"
                    }
            }
            else{
                    Set-Attr $result.log "Operational Status" "Disk was online already and need not to be set offline"  
            }
            if($StopSuccess){
                                    try{
                                        Manage-ShellHWService -Action "Start"
                                        }
                                    catch{
                                            $StartFailed = $true
                                                }
                                    if(!$StartFailed){
                                                Set-Attr $result.log "ShellHWService State" "Set from Stopped to Running again"
                                                Set-Attr $result "changed" $true;
                                    }
                                    else{
                                            Set-Attr $result.generallog "Maintain ShellHWService" "Failed"
                                            Set-Attr $result.log "ShellHWService State" "Could not be set from Stopped to Running again"
                                    }
            }
            else{
                    Set-Attr $result.log "ShellHWService State" "Service was stopped already and need not to be started again"  
            }
        Fail-Json $result $_
}

Set-Attr $result.log "Formating" "Volume $($CVolume.FileSystem) was created successfully on partiton $($CPartition.Type)"
Set-Attr $result.generallog "Create Volume" "Successful"
Set-Attr $result "changed" $true;

# Finally check if ShellHWService needs to be started again
if($StopSuccess){
                        try{
                            Manage-ShellHWService -Action "Start"
                            }
                        catch{
                                $StartFailed = $true
                                    }
                        if(!$StartFailed){
                                    Set-Attr $result.log "ShellHWService State" "Set from Stopped to Running again"
                                    Set-Attr $result "changed" $true;
                        }
                        else{
                                Set-Attr $result.generallog "Maintain ShellHWService" "Failed"
                                Set-Attr $result.log "ShellHWService State" "Could not be set from Stopped to Running again"
                        }
}
else{
        Set-Attr $result.log "ShellHWService State" "Service was stopped already and need not to be started again"  
}

Exit-Json $result;
