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

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -default $false -failifempty $true -aliases "dest","name"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","directory","file","touch"

$result = @{
    changed = $false
}

if ($state -eq "touch") {
    if (-not $check_mode) {
        if (Test-Path $path) {
            (Get-ChildItem $path).LastWriteTime = Get-Date
        } else {
            echo $null > $path
        }
    }
    $result.changed = $true
}

if (Test-Path $path) {
    $fileinfo = Get-Item $path
    if ($state -eq "absent") {
        if (-not $check_mode) {
            Remove-Item -Recurse -Force $fileinfo
        }
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
        if (-not $check_mode) {
            New-Item -ItemType directory -Path $path | Out-Null
        }
        $result.changed = $true
    } elseif ($state -eq "file") {
        Fail-Json $result "path $path will not be created"
    }

}

Exit-Json $result
