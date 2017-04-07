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

Import-Module Servermanager

$result = @{
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$restart = Get-AnsibleParam -obj $params -name "restart" -type "bool" -default $false
$includesubfeatures = Get-AnsibleParam -obj $params -name "include_sub_features" -type "bool" -default $false
$includemanagementtools = Get-AnsibleParam -obj $params -name "include_management_tools" -type "bool" -default $false
$source = Get-AnsibleParam -obj $params -name "source" -type "str"

$name = $name -split ',' | % { $_.Trim() }


# Determine which cmdlets we need to work with. Then we can set options appropriate for the cmdlet
$installWF= $false
$addWF = $false

try {
    # We can infer uninstall/remove if install/add cmdlets exist
    if (Get-Command "Install-WindowsFeature" -ErrorAction SilentlyContinue) {
        $addCmdlet = "Install-WindowsFeature"
        $removeCmdlet = "Uninstall-WindowsFeature"
        $installWF = $true
    }
    elseif (Get-Command "Add-WindowsFeature" -ErrorAction SilentlyContinue) {
        $addCmdlet = "Add-WindowsFeature"
        $removeCmdlet = "Remove-WindowsFeature"
        $addWF = $true
    }
    else {
        throw [System.Exception] "Not supported on this version of Windows"
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}


If ($state -eq "present") {

    # Base params to cover both Add/Install-WindowsFeature
    $InstallParams = @{
        Name = $name
        Restart = $restart
        IncludeAllSubFeature = $includesubfeatures
        ErrorAction = "SilentlyContinue"
        WhatIf = $check_mode
    }

    # IncludeManagementTools and source are options only for Install-WindowsFeature
    if ($installWF) {

        if ($source) {
            if (-not (Test-Path -Path $source)) {
                Fail-Json $result "Failed to find source path $source"
            }

            $InstallParams.add("Source",$source)
        }

        if ($IncludeManagementTools) {
            $InstallParams.add("IncludeManagementTools",$includemanagementtools)
        }
    }

    try {
        $featureresult = Invoke-Expression "$addCmdlet @InstallParams"
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}
ElseIf ($state -eq "absent") {

    $UninstallParams = @{
        Name = $name
        Restart = $restart
        ErrorAction = "SilentlyContinue"
        WhatIf = $check_mode
    }

    try {
        $featureresult = Invoke-Expression "$removeCmdlet @UninstallParams"
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

# Loop through results and create a hash containing details about
# each role/feature that is installed/removed
$installed_features = @()
#$featureresult.featureresult is filled if anything was changed
If ($featureresult.FeatureResult)
{
    ForEach ($item in $featureresult.FeatureResult) {
        $message = @()
        ForEach ($msg in $item.Message) {
            $message += @{
                message_type = $msg.MessageType.ToString()
                error_code = $msg.ErrorCode
                text = $msg.Text
            }
        }
        $installed_features += @{
            id = $item.Id
            display_name = $item.DisplayName
            message = $message
            restart_needed = $item.RestartNeeded.ToString() | ConvertTo-Bool
            skip_reason = $item.SkipReason.ToString()
            success = $item.Success.ToString() | ConvertTo-Bool
        }
    }
    $result.changed = $true
}

$result.feature_result = $installed_features
$result.success = ($featureresult.Success.ToString() | ConvertTo-Bool)
$result.exitcode = $featureresult.ExitCode.ToString()
$result.restart_needed = ($featureresult.RestartNeeded.ToString() | ConvertTo-Bool)

If ($result.success) {
    Exit-Json $result
}
ElseIf ($state -eq "present") {
    Fail-Json $result "Failed to add feature"
}
Else {
    Fail-Json $result "Failed to remove feature"
}
