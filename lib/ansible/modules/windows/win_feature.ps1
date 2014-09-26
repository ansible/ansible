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
Elseif (!$params.state) {
    $state = "present"
}

If ($params.restart) {
    $restart = $params.restart | ConvertTo-Bool
}
Else
{
    $restart = $false
}

if ($params.include_sub_features)
{
    $includesubfeatures = $params.include_sub_features | ConvertTo-Bool
}
Else
{
    $includesubfeatures = $false
}

if ($params.include_management_tools)
{
    $includemanagementtools = $params.include_management_tools | ConvertTo-Bool
}
Else
{
    $includemanagementtools = $false
}



If ($state -eq "present") {
    try {
        $featureresult = Add-WindowsFeature -Name $name -Restart:$restart -IncludeAllSubFeature:$includesubfeatures -IncludeManagementTools:$includemanagementtools
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}
Elseif ($state -eq "absent") {
    try {
        $featureresult = Remove-WindowsFeature -Name $name -Restart:$restart
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

# Loop through results and create a hash containing details about
# each role/feature that is installed/removed
$installed_features = @()
#$featureresult.featureresult is filled if anything was changed
if ($featureresult.FeatureResult)
{
    ForEach ($item in $featureresult.FeatureResult) {
        $installed_features += New-Object psobject @{
            id = $item.id.ToString()
            display_name = $item.DisplayName
            message = $item.Message.ToString()
            restart_needed = $item.RestartNeeded.ToString()
            skip_reason = $item.SkipReason.ToString()
            success = $item.Success.ToString()
        }
    }
    Set-Attr $result "feature_result" $installed_features
    

    $result.changed = $true
}
Else
{
    Set-Attr $result "feature_result" $null
}

Set-Attr $result "feature_success" $featureresult.Success.ToString()
Set-Attr $result "feature_exitcode" $featureresult.ExitCode.ToString()
Set-Attr $result "feature_restart_needed" $featureresult.RestartNeeded.ToString()

Exit-Json $result;
