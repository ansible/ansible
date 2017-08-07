#!powershell
# This file is part of Ansible
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

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","directory","file","touch"
$attributes = Get-AnsibleParam -obj $params -name "attributes" -type "str"

$result = @{
    changed = $false
}

# Used to delete symlinks as powershell cannot delete broken symlinks
$symlink_util = @"
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace Ansible.Command {
    public class SymLinkHelper {
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        public static extern bool RemoveDirectory(string lpPathName);

        public static void DeleteSymLink(string linkPathName) {
            bool result = RemoveDirectory(linkPathName);
            if (result == false)
                throw new Exception(String.Format("Error deleting symlink: {0}", new Win32Exception(Marshal.GetLastWin32Error()).Message));
        }
    }
}
"@
Add-Type -TypeDefinition $symlink_util

# Used to delete directories and files with logic on handling symbolic links
function Remove-File($file, $checkmode) {
    try {
        if ($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            # Bug with powershell, if you try and delete a symbolic link that is pointing
            # to an invalid path it will fail, using Win32 API to do this instead
            if (-Not $checkmode) {
                [Ansible.Command.SymLinkHelper]::DeleteSymLink($file.FullName)
            }
        } elseif ($file.PSIsContainer) {
            Remove-Directory -directory $file -WhatIf:$checkmode
        } else {
            Remove-Item -Path $file.FullName -Force -WhatIf:$checkmode
        }
    } catch [Exception] {
        Fail-Json $result "Failed to delete $($file.FullName): $($_.Exception.Message)"
    }
}

function Remove-Directory($directory) {
    foreach ($file in Get-ChildItem $directory.FullName) {
        Remove-File -file $file
    }
    Remove-Item -Path $directory.FullName -Force -Recurse
}

function Set-FileAttributes($file, $options, $checkmode){

    $CurrentAttributes = Get-ChildItem -Path $file -Force;
    $normalizedOptions = $options.Replace("+",$null);
    $fBucket = ([regex]::Matches($normalizedOptions, "\-"))
    $fBucket | ForEach-Object{
        $AttributesOff = $AttributesOff + $normalizedOptions[($_.Index)+1] | Out-String -Stream
    }
    if($normalizedOptions[0] -eq "-"){$normalizedOptions = "q"+$normalizedOptions}
    if($normalizedOptions[$normalizedOptions.Length-2] -eq "-"){$normalizedOptions = $normalizedOptions+"q"}
    $AttributesOn = $normalizedOptions.Replace("-",$null)

    for($i=0; $i -le $AttributesOn.Length; $i++){
        if(($AttributesOff -gt 0) -and [int]$AttributesOn.IndexOf($AttributesOff[$i]) -gt 0){
            $AttributesOn = $AttributesOn.Remove([int]$AttributesOn.IndexOf($AttributesOff[$i]),1)
        }
    }
    if(-not $checkmode -and $AttributesOn -match "n"){
        $CurrentAttributes.Attributes = "Normal"
        Return (Get-ChildItem -Path $file -Force).Attributes;
    }
    if(-not $checkmode){
        if($AttributesOn -match "a" -and $CurrentAttributes.Attributes -notmatch "Archive"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::Archive)
        }elseif($AttributesOff -match "a" -and $CurrentAttributes.Attributes -match "Archive"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::Archive)
        };
        if($AttributesOn -match "r" -and $CurrentAttributes.Attributes -notmatch "ReadOnly"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::ReadOnly)
        }elseif($AttributesOff -match "r" -and $CurrentAttributes.Attributes -match "ReadOnly"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::ReadOnly)
        };
        if($AttributesOn -match "s" -and $CurrentAttributes.Attributes -notmatch "System"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::System)
        }elseif($AttributesOff -match "s" -and $CurrentAttributes.Attributes -match "System"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::System)
        };
        if($AttributesOn -match "h" -and $CurrentAttributes.Attributes -notmatch "Hidden"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::Hidden)
        }elseif($AttributesOff -match "h" -and $CurrentAttributes.Attributes -match "Hidden"){
            $CurrentAttributes.Attributes = $CurrentAttributes.Attributes -bxor ([System.IO.FileAttributes]::Hidden)
        };
        Return (Get-ChildItem -Path $file -Force).Attributes;
    };
}

if(($attributes -ne $null) -and (Test-Path $path)){
    $NewAttributes = Set-FileAttributes -file $path -options $attributes -checkmode $check_mode;
    if ($check_mode -eq $true) {$result.changed = $false}else{$result.changed = $true};
    $result.msg = $NewAttributes;
}

if ($state -eq "touch") {
    if (Test-Path -Path $path) {
        try {
        (Get-ChildItem -Path $path -Force).LastWriteTime = Get-Date
        } catch {
            if ((Get-ChildItem -Path $path -Force).IsReadOnly) {
                Fail-Json $result "file $path is in a read only state"
            } else {
                Fail-Json $result "file $path is in a bad state"
            }
        }
    } else {
        Write-Output $null | Out-File -FilePath $path -Encoding ASCII -WhatIf:$check_mode
        $result.changed = $true
    }
}

if (Test-Path $path) {
    $fileinfo = Get-Item -Path $path -Force
    if ($state -eq "absent") {
        Remove-File -File $fileinfo -CheckMode $check_mode
        $result.changed = $true
    } else {
        if ($state -eq "directory" -and -not $fileinfo.PsIsContainer) {
            Fail-Json $result "path $path is not a directory"
        }

        if ($state -eq "file" -and $fileinfo.PsIsContainer) {
            Fail-Json $result "path $path is not a file"
        }
    }

} else {

    # If state is not supplied, test the $path to see if it looks like
    # a file or a folder and set state to file or folder
    if ($state -eq $null) {
        $basename = Split-Path -Path $path -Leaf
        if ($basename.length -gt 0) {
           $state = "file"
        } else {
           $state = "directory"
        }
    }

    if ($state -eq "directory") {
        try {
            New-Item -Path $path -ItemType Directory -WhatIf:$check_mode | Out-Null
        } catch {
            if ($_.CategoryInfo.Category -eq "ResourceExists") {
                $fileinfo = Get-Item $_.CategoryInfo.TargetName -Force
                if ($state -eq "directory" -and -not $fileinfo.PsIsContainer) {
                    Fail-Json $result "path $path is not a directory"
                }
            } else {
                Fail-Json $result $_.Exception.Message
            }
        }
        $result.changed = $true
    } elseif ($state -eq "file") {
        Fail-Json $result "path $path will not be created"
    }

}

Exit-Json $result
