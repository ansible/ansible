#!powershell
# (c) 2017, Dag Wieers <dag@wieers.com>
#
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

Function New-TempFile {
    Param ([string]$path, [string]$prefix, [string]$suffix, [string]$type, [bool]$checkmode)
    $temppath = $null
    $attempt = 0

    # Since we don't know if the file already exists, we try 5 times with a random name
    do {
        $attempt += 1
        $randomname = [System.IO.Path]::GetRandomFileName()
        $temppath = (Join-Path -Path $path -ChildPath "$prefix$randomname$suffix")
        Try {
            New-Item -Path $temppath -ItemType $type -WhatIf:$checkmode | Out-Null
        } Catch {
            $temppath = $null
            $error = $_.Exception.Message
        }
    } until ($temppath -ne $null -or $attempt -ge 5)

    # If it fails 5 times, something is wrong and we have to report the details
    if ($temppath -eq $null) {
        Fail-Json @{} "No random temporary file worked in $attempt attempts. Error: $error"
    }

    return $temppath
}

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -default "%TEMP%" -aliases "dest"
$state = Get-AnsibleParam -obj $params -name "state" -type "string" -default "file" -validateset "file","directory"
$prefix = Get-AnsibleParam -obj $params -name "prefix" -type "string" -default "ansible."
$suffix = Get-AnsibleParam -obj $params -name "suffix" -type "string"

# Expand environment variables on non-path types
$prefix = Expand-Environment($prefix)
$suffix = Expand-Environment($suffix)

$result = @{
    changed = $true
    state = $state
}

$result.path = New-TempFile -Path $path -Prefix $prefix -Suffix $suffix -Type $state -CheckMode $check_mode

Exit-Json $result