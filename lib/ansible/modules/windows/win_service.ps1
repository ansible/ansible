#!powershell
# This file is part of Ansible
#
# Copyright 2014, Chris Hoffman <choffman@chathamfinancial.com>
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

$check_mode = Get-AnsibleParam -obj $params "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -default "started" -validateset "started","stopped","restarted"
$start_mode = Get-AnsibleParam -obj $params -name "start_mode" -validateset "auto","manual","disabled"

$result = @{
    changed = $false
    warnings = @()
}

$service = Get-Service -Name $name -ErrorAction SilentlyContinue
if (-not $service) {
    Fail-Json $result "Service '$name' not installed"
}

$result.name = $service.ServiceName
$result.display_name = $service.DisplayName

# Use service name instead of display name for remaining actions.
if ($name -ne $service.ServiceName) {
    $result.warnings += "Please use `"$service.ServiceName`" as service name instead of `"$name`""
    $name = $service.ServiceName
}

$current_mode = Get-WmiObject -Class Win32_Service -Property StartMode -Filter "Name='$name'"
$result.start_mode = $current_mode.StartMode.ToLower()
if ($start_mode -ne $null) {
    if ($start_mode -ne $result.start_mode) {
        if ($check_mode) {
            Set-Service -Name $name -StartupType $start_mode -WhatIf
        } else {
            Set-Service -Name $name -StartupType $start_mode
        }
        $result.changed = $true
        $result.start_mode = $start_mode
    }
}

if ($state -eq "started" -and $service.Status -ne "Running") {

    try {
        if ($check_mode) {
            Start-Service -Name $name -WhatIf
        } else {
            Start-Service -Name $name
        }
    } catch {
        Fail-Json $result $_.Exception.Message
    }
    $result.changed = $true

} elseif ($state -eq "stopped" -and $service.Status -ne "Stopped") {

    try {
        if ($check_mode) {
            Stop-Service -Name $name -WhatIf
        } else {
            Stop-Service -Name $name
        }
    } catch {
        Fail-Json $result $_.Exception.Message
    }
    $result.changed = $true

} elseif ($state -eq "restarted") {

    try {
        if ($checkmode) {
            Restart-Service -Name $name -WhatIf
        } else {
            Restart-Service -Name $name
        }
    } catch {
        Fail-Json $result $_.Exception.Message
    }
    $result.changed = $true

}
$service.Refresh()
$result.state = $service.Status.ToString().ToLower()

Exit-Json $result
