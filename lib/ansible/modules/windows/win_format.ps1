#!powershell

# Copyright: (c) 2019, Varun Chopra (@chopraaa) <v@chopraaa.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.2

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"

$spec = @{
    options = @{
        drive_letter = @{ type = "str" }
        path = @{ type = "str" }
        label = @{ type = "str" }
        new_label = @{ type = "str" }
        file_system = @{ type = "str"; choices = "ntfs", "refs", "exfat", "fat32", "fat" }
        allocation_unit_size = @{ type = "int" }
        large_frs = @{ type = "bool" }
        full = @{ type = "bool"; default = $false }
        compress = @{ type = "bool" }
        integrity_streams = @{ type = "bool" }
        force = @{ type = "bool"; default = $false }
    }
    mutually_exclusive = @(
        ,@('drive_letter', 'path', 'label')
    )
    required_one_of = @(
        ,@('drive_letter', 'path', 'label')
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$drive_letter = $module.Params.drive_letter
$path = $module.Params.path
$label = $module.Params.label
$new_label = $module.Params.new_label
$file_system = $module.Params.file_system
$allocation_unit_size = $module.Params.allocation_unit_size
$large_frs = $module.Params.large_frs
$full_format = $module.Params.full
$compress_volume = $module.Params.compress
$integrity_streams = $module.Params.integrity_streams
$force_format = $module.Params.force

# Some pre-checks
if ($null -ne $drive_letter -and $drive_letter -notmatch "^[a-zA-Z]$") {
    $module.FailJson("The parameter drive_letter should be a single character A-Z")
}
if ($integrity_streams -eq $true -and $file_system -ne "refs") {
    $module.FailJson("Integrity streams can be enabled only on ReFS volumes. You specified: $($file_system)")
}
if ($compress_volume -eq $true) {
    if ($file_system -eq "ntfs") {
        if ($null -ne $allocation_unit_size -and $allocation_unit_size -gt 4096) {
            $module.FailJson("NTFS compression is not supported for allocation unit sizes above 4096")
        }
    }
    else {
        $module.FailJson("Compression can be enabled only on NTFS volumes. You specified: $($file_system)")
    }
}

function Get-AnsibleVolume {
    param(
        $DriveLetter,
        $Path,
        $Label
    )

    if ($null -ne $DriveLetter) {
        try {
            $volume = Get-Volume -DriveLetter $DriveLetter
        } catch {
            $module.FailJson("There was an error retrieving the volume using drive_letter $($DriveLetter): $($_.Exception.Message)", $_)
        }
    }
    elseif ($null -ne $Path) {
        try {
            $volume = Get-Volume -Path $Path
        } catch {
            $module.FailJson("There was an error retrieving the volume using path $($Path): $($_.Exception.Message)", $_)
        }
    }
    elseif ($null -ne $Label) {
        try {
            $volume = Get-Volume -FileSystemLabel $Label
        } catch {
            $module.FailJson("There was an error retrieving the volume using label $($Label): $($_.Exception.Message)", $_)
        }
    }
    else {
        $module.FailJson("Unable to locate volume: drive_letter, path and label were not specified")
    }

    return $volume
}

function Format-AnsibleVolume {
    param(
        $Path,
        $Label,
        $FileSystem,
        $Full,
        $UseLargeFRS,
        $Compress,
        $SetIntegrityStreams,
        $WhatIf
    )
    $parameters = @{
        Path = $Path
        Full = $Full
        WhatIf = $WhatIf
        Confirm = $false
    }
    if ($null -ne $UseLargeFRS) {
        $parameters.Add("UseLargeFRS", $UseLargeFRS)
    }
    if ($null -ne $SetIntegrityStreams) {
        $parameters.Add("SetIntegrityStreams", $SetIntegrityStreams)
    }
    if ($null -ne $compress_volume){
        $parameters.Add("Compress", $Compress)
    }
    if ($null -ne $Label) {
        $parameters.Add("NewFileSystemLabel", $Label)
    }
    if ($null -ne $FileSystem) {
        $parameters.Add("FileSystem", $FileSystem)
    }

    try {
        Format-Volume @parameters | Out-Null
    } catch {
        $module.FailJson("Unable to format volume at $($Path): $($_.Exception.Message)", $_)
    }
}

$ansible_volume = Get-AnsibleVolume -DriveLetter $drive_letter -Path $path -Label $label

if (-not $force_format) {
    $ansible_volume_size = $ansible_volume.Size
    $ansible_partition_size = (Get-Partition -Volume $ansible_volume).Size

    if ($ansible_volume_size -ne 0 -or $ansible_partition_size -eq $ansible_volume_size) {
        $module.FailJson("Specify force parameter to format non-pristine volumes")
    }
}

Format-AnsibleVolume -Path $ansible_volume.Path -Full $full_format -Label $new_label -SetIntegrityStreams $integrity_streams -UseLargeFRS $large_frs -Compress $compress_volume -WhatIf $module.CheckMode
$module.Result.changed = $true

$module.ExitJson()
