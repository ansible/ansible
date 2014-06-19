#!powershell
# This file is part of Ansible.
#
# Copyright 2014, Paul Durivage <paul.durivage@rackspace.com>
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

Import-Module Servermanager;

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_feature = New-Object psobject
    changed = $false
}

If ($params.name) {
    $name = $params.name
}
Else {
    Fail-Json $result "mising required argument: name"
}

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'present') -and ($state -ne 'absent')) {
        Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
    }
}

If ($state -eq "present") {
    try {
        $result = Add-WindowsFeature -Name $name
    }
    catch {
        Fail-Json $_.Exception.Message
    }
}
Elseif ($state -eq "absent") {
    try {
        $result = Remove-WindowsFeature -Name $name
    }
    catch {
        Fail-Json $_.Exception.Message
    }
}
Else {
    $state = "present"
}

$feature_results = @()
ForEach ($item in $result.FeatureResult) {
    $feature_results += New-Object psobject @{
        id = $item.id.ToString()
        message = $item.Message.ToString()
        restart_needed = $item.RestartNeeded.ToString()
        skip_reason = $item.SkipReason.ToString()
        success = $item.Success
    }
}
Set-Attr $result.win_feature "feature_result" $feature_results
Set-Attr $result.win_feature "success" $result.Success
Set-Attr $result.win_feature "exitcode" $result.ExitCode.ToString()
Set-Attr $result.win_feature "restart_needed" $result.RestartNeeded.ToString()

Exit-Json $result;
