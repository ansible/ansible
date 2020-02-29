#!powershell

# Copyright: (c) 2020, Brian Scholer <@briantist>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseDeclaredVarsMoreThanAssignments', '', Justification='Some vars are referenced via Get-Variable')]
param() # param() is needed for attribute to take effect.

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$source_location = Get-AnsibleParam -obj $params -name "source_location" -aliases "source" -type "str"
$script_source_location = Get-AnsibleParam -obj $params -name "script_source_location" -type "str"
$publish_location = Get-AnsibleParam -obj $params -name "publish_location" -type "str"
$script_publish_location = Get-AnsibleParam -obj $params -name "script_publish_location" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installation_policy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -validateset "trusted", "untrusted"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

$result = @{"changed" = $false}

if (-not (Import-Module -Name PowerShellGet -MinimumVersion 1.6.0 -PassThru -ErrorAction SilentlyContinue)) {
    Fail-Json -obj $result -Message "PowerShellGet version 1.6.0+ is required."
}

$repository_params = @{
    Name = $name
}

$Repo = Get-PSRepository @repository_params -ErrorAction Ignore

if ($installation_policy) {
    $repository_params.InstallationPolicy = $installation_policy
}

function Resolve-LocationParameter {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string[]]
        $Name ,

        [Parameter(Mandatory=$true)]
        [hashtable]
        $Splatter
    )

    End {
        foreach ($param in $Name) {
            $val = Get-Variable -Name $param -ValueOnly -ErrorAction SilentlyContinue
            if ($val) {
                if ($val -as [uri]) {
                    $Splatter[$param.Replace('_','')] = $val -as [uri]
                }
                else {
                    Fail-Json -obj $result -Message "'$param' must be a valid URI."
                }
            }
        }
    }
}

Resolve-LocationParameter -Name source_location,publish_location,script_source_location,script_publish_location -Splatter $repository_params

if (-not $repository_params.SourceLocation -and $state -eq 'present' -and ($force -or -not $Repo)) {
    Fail-Json -obj $result -message "'source_location' is required when registering a new repository or using force with 'state' == 'present'."
}
Function Update-NuGetPackageProvider {
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object { ($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201") }
    if ($null -eq $PackageProvider) {
        Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force | Out-Null
    }
}

if ($Repo) {
    $changed_properties = @{}

    if ($force -and -not $repository_params.InstallationPolicy) {
        $repository_params.InstallationPolicy = 'trusted'
    }

    if ($repository_params.InstallationPolicy) {
        if ($Repo.InstallationPolicy -ne $repository_params.InstallationPolicy) {
            $changed_properties.InstallationPolicy = $repository_params.InstallationPolicy
        }
    }

    if ($repository_params.SourceLocation) {
        # force check not needed here because it's done earlier; source_location is required with force
        if ($repository_params.SourceLocation -ne $Repo.SourceLocation) {
            $changed_properties.SourceLocation = $repository_params.SourceLocation
        }
    }

    if ($force -or $repository_params.ScriptSourceLocation) {
        if ($repository_params.ScriptSourceLocation -ne $Repo.ScriptSourceLocation) {
            $changed_properties.ScriptSourceLocation = $repository_params.ScriptSourceLocation
        }
    }

    if ($force -or $repository_params.PublishLocation) {
        if ($repository_params.PublishLocation -ne $Repo.PublishLocation) {
            $changed_properties.PublishLocation = $repository_params.PublishLocation
        }
    }

    if ($force -or $repository_params.ScriptPublishLocation) {
        if ($repository_params.ScriptPublishLocation -ne $Repo.ScriptPublishLocation) {
            $changed_properties.ScriptPublishLocation = $repository_params.ScriptPublishLocation
        }
    }
}

if ($Repo -and ($state -eq "absent" -or ($force -and $changed_properties.Count -gt 0))) {
    if (-not $check_mode) {
        Update-NuGetPackageProvider
        Unregister-PSRepository -Name $name
    }
    $result.changed = $true
}

if ($state -eq "present") {
    if (-not $Repo -or ($force -and $changed_properties.Count -gt 0)) {
        if (-not $repository_params.InstallationPolicy) {
            $repository_params.InstallationPolicy = "trusted"
        }
        if (-not $check_mode) {
            Update-NuGetPackageProvider
            Register-PSRepository @repository_params
        }
        $result.changed = $true
    }
    else {
        if ($changed_properties.Count -gt 0) {
            if (-not $check_mode) {
                Update-NuGetPackageProvider
                Set-PSRepository -Name $name @changed_properties
            }
            $result.changed = $true
        }
    }
}

Exit-Json -obj $result
