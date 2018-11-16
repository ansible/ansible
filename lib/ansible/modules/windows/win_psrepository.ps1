#!powershell

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -aliases "repository" -failifempty $true
$url = Get-AnsibleParam -obj $params -name "source_location" -type "str" -aliases "url"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installationpolicy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -validateset "trusted", "untrusted"
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$result = @{"changed" = $false
            "output" = ""}

Function Install-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [Parameter(Mandatory=$true)]
        [String]$Url,
        [String]$InstallationPolicy,
        [Bool]$CheckMode
    )
        try {
            if (-not($CheckMode)) {
               Register-PSRepository -Name $Name -SourceLocation $Url -InstallationPolicy $InstallationPolicy
            }
            $result.output = "The repository $Name with the SourceLocation $Url was registered."
            $result.changed = $true
        }
        catch {
            $ErrorMessage = "Problems adding $($Name) repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
}

Function Remove-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [Bool]$CheckMode
    )
    $ReposNames = (Get-PSRepository).Name

    if ($ReposNames -contains $Name){
        try {
            if (-not ($CheckMode)) {
                Unregister-PSRepository -Name $Name
            }
            $result.output = "The repository $Name was unregistered."
            $result.changed = $true
        }
        catch {
            $ErrorMessage = "Problems removing $($Name) repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Set-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [String]$InstallationPolicy,
        [Bool]$CheckMode
    )
    try {
        if (-not ($CheckMode)) {
            Set-PSRepository -Name $Name -InstallationPolicy $InstallationPolicy
        }
        $result.output = "The InstallationPolicy for the repository $Name was changed to $InstallationPolicy."
        $result.changed = $true
    }
    catch {
        $ErrorMessage = "Problems changing the InstallationPolicy for $($Name) repository: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
    }
}

# Check PowerShell version, fail if < 5.0
$PsVersion = $PSVersionTable.PSVersion
if ($PsVersion.Major -lt 5){
    $ErrorMessage = "Windows PowerShell 5.0 or higher is needed."
    Fail-Json $result $ErrorMessage
}

# Check NuGet version, fail if < 2.8.5.201
$NugetVersion = (Get-PackageProvider -Name Nuget).Version
if ( $NugetVersion -lt [Version]"2.8.5.201" ) {
    $ErrorMessage = "The NuGet package provider in version 2.8.5.201 or higher is needed."
    Fail-Json $result $ErrorMessage
}

$Repos = Get-PSRepository

if ($state -eq "present") {
    if ($name -and $url) {
        $ReposSourceLocations = ($Repos).SourceLocation
        # If repository isn't already present, try to register it.
        if ($ReposSourceLocations -notcontains $Url){
            if ( $installationpolicy ) {
                $installationpolicy_internal = $installationpolicy
            }
            else {
                $installationpolicy_internal = "Trusted"
            }

            Install-Repository -Name $name -Url $url -InstallationPolicy $installationpolicy_internal -CheckMode $check_mode
        }
    }
    elseif ($name -and $installationpolicy) {
        $ExistingInstallationPolicy = $($Repos | Where-Object { $_.Name -eq $Name }).InstallationPolicy
        if ( $ExistingInstallationPolicy -ne $installationpolicy ) {
            Set-Repository -Name $Name -InstallationPolicy $installationpolicy -CheckMode $check_mode
        }
    }
    else {
        $ErrorMessage = "Repository Name and Url are mandatory if you want to add a new repository."
        Fail-Json $result $ErrorMessage
    }
}
elseif ($state -eq "absent") {
    if ( $name ) {
        Remove-Repository -Name $name -CheckMode $check_mode
    }
}

Exit-Json $result
