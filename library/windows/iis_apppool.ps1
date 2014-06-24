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

Import-Module WebAdministration

$ErrorActionPreference = "Stop"

$params = Parse-Args $args;

$result = New-Object PSObject;
Set-Attr $result "changed" $false;

If (-not $params.name.GetType) {
    Fail-Json $result "missing required arguments: name"
}

$ValidStates = "started", "stopped", "restarted", "absent"
If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If ($ValidStates -notcontains $state) {
        Fail-Json $result "state is not valid"
    }
}
Else {
    $state = "started"
}

$IdentityTypeEnum = @{
    "localsystem" = 0
    "localservice" = 1
    "networkservice" = 2
    "specificuser" = 3
    "applicationpoolidentity" = 4
}
If ($params.identity_type) {
    $IdentityType = $params.identity_type.ToString().ToLower()
    If ($IdentityTypeEnum.ContainsKey($IdentityType)) {
        $IdentityTypeValue = $IdentityTypeEnum[$IdentityType]
    }
    Else {
        Fail-Json $result "identity_type is not valid"
    }
}
Else {
    $IdentityTypeValue = 4  #ApplicationPoolIdentity
}

If ($params.identity_type -eq "SpecificUser" -and -not ($params.username -or $params.password)) {
    Fail-Json $result "username and password must be specified when identity_type is SpecificUser"
}

$ValidManagedRuntimeVersions = "v1.1", "v2.0", "v4.0", "no managed code"
If ($params.managed_runtime) {
    $ManagedRuntime = $params.managed_runtime.ToString().ToLower()
    If ($ValidManagedRuntimeVersions -notcontains $ManagedRuntime) {
        Fail-Json $result "managed_runtime is not valid"
    }
}

If ($params.force.GetType){
    $Force = $params.force.ToString().ToLower() | ConvertTo-Bool
}
Else {
    $Force = $false
}

If ($params.additional_settings) {
    $AdditionalSettings = $params.additional_settings
}
Else {
    $AdditionalSettings = @()
}

Function Set-AppPoolProperty ($path, $name, $value, $enumValue) {
    $Property = Get-ItemProperty $path $name
    If ($Property) {
        If (($enumValue -and $Property.ToLower() -ne $enumValue) -or (-not $enumValue -and $Property -ne $value)) {
            Set-ItemProperty $path $name $value
            Set-Attr $result "changed" $true
        }
    }
    Else {
        Fail-Json $result "Application pool property '$name' does not exist"
    }
}

try {
    $AppPoolPath = "IIS://AppPools/" + $params.name
    $AppPoolExists = Test-Path $AppPoolPath

    If ($state -eq "absent"){
        If ($AppPoolExists) {
            Remove-WebAppPool $params.name
            Set-Attr $result "changed" $true
        }
    }
    Else {
        If ($AppPoolExists -and $Force) {
            Remove-WebAppPool $params.name
            $AppPoolExists = $false
        }

        If (-not $AppPoolExists) {
            New-WebAppPool $params.name
            Set-Attr $result "changed" $true
        }

        Set-AppPoolProperty $AppPoolPath "processModel.identityType" $IdentityTypeValue $IdentityType

        If ($ManagedRuntime) {
            Set-AppPoolProperty $AppPoolPath "managedRuntimeVersion" $params.managed_runtime
        }

        # Set user and password on new and forced
        If ($IdentityType -eq "specifieduser" -and -not $AppPoolExists) {
            Set-ItemProperty $AppPoolPath "processModel.username" $params.username
            Set-ItemProperty $AppPoolPath "processModel.password" $params.password
        }

        ForEach ($setting in $AdditionalSettings) {
            Set-AppPoolProperty $AppPoolPath $setting.name $setting.value
        }

        $AppPoolState = $(Get-WebAppPoolState -Name $params.name).Value
        If ($AppPoolState -eq "Started") {
            If ($state -eq "stopped") {
                Stop-WebappPool $params.name
                Set-Attr $result "changed" $true
            }
            ElseIf ($state -eq "restarted") {
                Restart-WebappPool $params.name
                Set-Attr $result "changed" $true
            }
        }
        If ($AppPoolState -eq "Stopped") {
            If ($state -ne "stopped") {
                Start-WebappPool $params.name
                Set-Attr $result "changed" $true
            }
        }
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result
