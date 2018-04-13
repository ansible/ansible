#!powershell

# Copyright: (c) 2017, Ansible Project

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","directory","file","touch"

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
            Remove-Directory -directory $file -checkmode $checkmode
        } else {
            Remove-Item -Path $file.FullName -Force -WhatIf:$checkmode
        }
    } catch [Exception] {
        Fail-Json $result "Failed to delete $($file.FullName): $($_.Exception.Message)"
    }
}

function Remove-Directory($directory, $checkmode) {
    foreach ($file in Get-ChildItem $directory.FullName) {
        Remove-File -file $file -checkmode $checkmode
    }
    Remove-Item -Path $directory.FullName -Force -Recurse -WhatIf:$checkmode
}


if ($state -eq "touch") {
    if (Test-Path -Path $path) {
        (Get-ChildItem -Path $path).LastWriteTime = Get-Date
    } else {
        Write-Output $null | Out-File -FilePath $path -Encoding ASCII -WhatIf:$check_mode
        $result.changed = $true
    }
}

if (Test-Path -Path $path) {
    $fileinfo = Get-Item -Path $path
    if ($state -eq "absent") {
        Remove-File -file $fileinfo -checkmode $check_mode
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
                $fileinfo = Get-Item $_.CategoryInfo.TargetName
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
