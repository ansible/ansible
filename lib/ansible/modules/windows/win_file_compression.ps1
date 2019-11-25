#!powershell

# Copyright: (c) 2019, Micah Hunsberger
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

Set-StrictMode -Version 2

$spec = @{
    options = @{
        path = @{ type = 'path'; required = $true }
        state = @{ type = 'str'; default = 'present'; choices = 'absent', 'present' }
        recurse = @{ type = 'bool'; default = $false }
        force = @{ type = 'bool'; default = $true }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$state = $module.Params.state
$recurse = $module.Params.recurse
$force = $module.Params.force

$module.Result.rc = 0

if(-not (Test-Path -LiteralPath $path)) {
    $module.FailJson("Path to item, $path, does not exist.")
}

$item = Get-Item -LiteralPath $path -Force  # Use -Force for hidden files
if (-not $item.PSIsContainer -and $recurse) {
    $module.Warn("The recurse option has no effect when path is not a folder.")
}

$cim_params = @{
    ClassName = 'Win32_LogicalDisk'
    Filter = "DeviceId='$($item.PSDrive.Name):'"
    Property = @('FileSystem', 'SupportsFileBasedCompression')
}
$drive_info = Get-CimInstance @cim_params
if ($drive_info.SupportsFileBasedCompression -eq $false) {
    $module.FailJson("Path, $path, is not on a filesystemi '$($drive_info.FileSystem)' that supports file based compression.")
}

function Get-ReturnCodeMessage {
    param(
        [int]$code
    )
    switch ($code) {
        0 { return "The request was successful." }
        2 { return "Access was denied." }
        8 { return "An unspecified failure occurred." }
        9 { return "The name specified was not valid." }
        10 { return "The object specified already exists." }
        11 { return "The file system is not NTFS." }
        12 { return "The platform is not Windows." }
        13 { return "The drive is not the same." }
        14 { return "The directory is not empty." }
        15 { return "There has been a sharing violation." }
        16 { return "The start file specified was not valid." }
        17 { return "A privilege required for the operation is not held." }
        21 { return "A parameter specified is not valid." }
    }
}

function Get-EscapedFileName {
    param(
        [string]$FullName
    )
    return $FullName.Replace("\","\\").Replace("'","\'")
}

$is_compressed = ($item.Attributes -band [System.IO.FileAttributes]::Compressed) -eq [System.IO.FileAttributes]::Compressed
$needs_changed = $is_compressed -ne ($state -eq 'present')

if($force -and $recurse -and $item.PSIsContainer) {
    if (-not $needs_changed) {
        # Check the subfolders and files
        $entries_to_check = $item.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
        foreach ($entry in $entries_to_check) {
            $is_compressed = ($entry.Attributes -band [System.IO.FileAttributes]::Compressed) -eq [System.IO.FileAttributes]::Compressed
            if ($is_compressed -ne ($state -eq 'present')) {
                $needs_changed = $true
                break
            }
        }
    }
}

if($needs_changed) {
    $module.Result.changed = $true
    if ($item.PSIsContainer) {
        $cim_obj = Get-CimInstance -ClassName 'Win32_Directory' -Filter "Name='$(Get-EscapedFileName -FullName $item.FullName)'"
    } else {
        $cim_obj = Get-CimInstance -ClassName 'CIM_LogicalFile' -Filter "Name='$(Get-EscapedFileName -FullName $item.FullName)'"
    }
    if($state -eq 'present') {
        if(-not $module.CheckMode) {
            $ret = Invoke-CimMethod -InputObject $cim_obj -MethodName 'CompressEx' -Arguments @{ Recursive = $recurse }
            $module.Result.rc = $ret.ReturnValue
        }
    } else {
        if(-not $module.CheckMode) {
            $ret = $ret = Invoke-CimMethod -InputObject $cim_obj -MethodName 'UnCompressEx' -Arguments @{ Recursive = $recurse }
            $module.Result.rc = $ret.ReturnValue
        }
    }
}

$module.Result.msg = Get-ReturnCodeMessage -code $module.Result.rc
if($module.Result.rc -ne 0) {
    $module.FailJson($module.Result.msg)
}

$module.ExitJson()
