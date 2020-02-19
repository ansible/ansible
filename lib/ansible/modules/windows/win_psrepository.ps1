#!powershell

# Copyright: (c) 2020, Brian Scholer <@briantist>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module @{ ModuleName = 'PowerShellGet' ; ModuleVersion = '1.6.0' }

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$source_location = Get-AnsibleParam -obj $params -name "source_location" -aliases "source","module_source","module_source_location" -type "str"
$script_source_location = Get-AnsibleParam -obj $params -name "script_source_location" -aliases "script_source" -type "str"
$publish_location = Get-AnsibleParam -obj $params -name "publish_location" -aliases "module_publish_location" -type "str"
$script_publish_location = Get-AnsibleParam -obj $params -name "script_publish_location" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installation_policy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -validateset "trusted", "untrusted"
$resolve_locations = Get-AnsibleParam -obj $params -name "resolve_locations" -type "bool" -default $true
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

$result = @{"changed" = $false}

# Update protocols so repos that disable weak TLS can be used
# Logic taken from Ansible.ModuleUtils.WebRequest
# ---
# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::SystemDefault
if ([System.Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls11
}
if ([System.Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls12
}
[System.Net.ServicePointManager]::SecurityProtocol = $security_protocols


Function Resolve-PSGetLocation {
    <#
        .SYNOPSIS
        This is a sort of proxy function for the Resolve-Location function that PowerShellGet uses internally.

        .DESCRIPTION
        It's not exported from the module, and it needs a caller context so wrapping it in a function both convenient
        and functional depending on how the outer module is executed (where $PSCmdlet may not be set).

        Also wraps the needed to call to other internal function, Get-LocationString, which does some normalizing
        or [uri] to [string] conversion.

        .NOTES
        - This must be an advanced function so that $PSCmdlet is populated.
        - Some context around all the things this tries to do: https://github.com/PowerShell/PowerShellGet/issues/317
    #>
    [CmdletBinding()]
    [OutputType([string])]
    Param
    (
        [Parameter(Mandatory=$true)]
        [uri]
        $Location,

        [Parameter(Mandatory=$true)]
        [string]
        $LocationParameterName,

        [Parameter()]
        [pscredential]
        $Credential,

        [Parameter()]
        $Proxy,

        [Parameter()]
        [pscredential]
        $ProxyCredential
    )

    $module = Get-Module -Name PowerShellGet

    $module.Invoke({
        param(
            [System.Collections.IDictionary]
            $Params,

            [System.Management.Automation.PSCmdlet]
            $CallerPSCmdlet
        )
        $Params.Location = Get-LocationString -LocationUri $Params.Location
        Resolve-Location @Params -CallerPSCmdlet $CallerPSCmdlet
    }, @($PSBoundParameters,$PSCmdlet))
}

$repository_params = @{
    Name = $name
}

$Repo = Get-PSRepository @repository_params -ErrorAction Ignore

if ($installation_policy) {
    $repository_params.InstallationPolicy = $installation_policy
}

# Validate location params are valid URIs and add them to the params
if ($source_location) {
    if ($source_location -as [uri]) {
        $repository_params.SourceLocation = if ($resolve_locations) {
            Resolve-PSGetLocation -Location $source_location -LocationParameterName source_location
        }
        else {
            $source_location
        }
    }
    else {
        Fail-Json -obj $result -Message "source_location must be a valid URL."
    }
}
elseif ($state -eq 'present' -and ($force -or -not $Repo)) {
    Fail-Json -obj $result -message "source_location is required when registering a new repository or using force with 'state' == 'present'."
}

if ($script_source_location) {
    if ($script_source_location -as [uri]) {
        $repository_params.ScriptSourceLocation = if ($resolve_locations) {
            Resolve-PSGetLocation -Location $script_source_location -LocationParameterName script_source_location
        }
        else {
            $script_source_location
        }
    }
    else {
        Fail-Json -obj $result -Message "script_source_location must be a valid URL."
    }
}

if ($publish_location) {
    if ($publish_location -as [uri]) {
        $repository_params.PublishLocation = if ($resolve_locations) {
            Resolve-PSGetLocation -Location $publish_location -LocationParameterName publish_location
        }
        else {
            $publish_location
        }
    }
    else {
            Fail-Json -obj $result -Message "publish_location must be a valid URL."
    }
}

if ($script_publish_location) {
    if ($script_publish_location -as [uri]) {
        $repository_params.ScriptPublishLocation = if ($resolve_locations) {
            Resolve-PSGetLocation -Location $script_publish_location -LocationParameterName script_publish_location
        }
        else {
            $script_publish_location
        }
    }
    else {
            Fail-Json -obj $result -Message "script_publish_location must be a valid URL."
    }
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
