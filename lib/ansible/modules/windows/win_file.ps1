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
        Fail-Json (New-Object psobject) "Failed to delete $($file.FullName): $($_.Exception.Message)"
    }
}

function Remove-Directory($directory) {
    foreach ($file in Get-ChildItem $directory.FullName) {
        Remove-File -file $file
    }
    Remove-Item -Path $directory.FullName -Force -Recurse
}


if ($state -eq "touch") {
    if (Test-Path -Path $path) {
        (Get-ChildItem -Path $path).LastWriteTime = Get-Date
    } else {
        Write-Output $null | Out-File -FilePath $path -Encoding ASCII -WhatIf:$check_mode
        $result.changed = $true
    }
}

if (Test-Path $path) {
    $fileinfo = Get-Item -Path $path
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
        New-Item -Path $path -ItemType Directory -WhatIf:$check_mode | Out-Null
        $result.changed = $true
    } elseif ($state -eq "file") {
        Fail-Json $result "path $path will not be created"
    }

}

Exit-Json $result
