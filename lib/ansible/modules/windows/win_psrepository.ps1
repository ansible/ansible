#!powershell

# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installationpolicy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -validateset "trusted", "untrusted"

$result = @{"changed" = $false}

# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::SystemDefault
if ([System.Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls11
}
if ([System.Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls12
}
[System.Net.ServicePointManager]::SecurityProtocol = $security_protocols

Function Update-NuGetPackageProvider {
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object { ($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201") }
    if ($null -eq $PackageProvider) {
        Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force | Out-Null
    }
}

$Repo = Get-PSRepository -Name $name -ErrorAction SilentlyContinue
if ($state -eq "present") {
    if ($null -eq $Repo) {
        if ($null -eq $installationpolicy) {
            $installationpolicy = "trusted"
        }
        if (-not $check_mode) {
            Update-NuGetPackageProvider
            Register-PSRepository -Name $name -SourceLocation $source -InstallationPolicy $installationpolicy
        }
        $result.changed = $true
    }
    else {
        $changed_properties = @{}

        if ($Repo.SourceLocation -ne $source) {
            $changed_properties.SourceLocation = $source
        }

        if ($null -ne $installationpolicy -and $Repo.InstallationPolicy -ne $installationpolicy) {
            $changed_properties.InstallationPolicy = $installationpolicy
        }

        if ($changed_properties.Count -gt 0) {
            if (-not $check_mode) {
                Update-NuGetPackageProvider
                Set-PSRepository -Name $name @changed_properties
            }
            $result.changed = $true
        }
    }
}
elseif ($state -eq "absent" -and $null -ne $Repo) {
    if (-not $check_mode) {
        Update-NuGetPackageProvider
        Unregister-PSRepository -Name $name
    }
    $result.changed = $true
}

Exit-Json -obj $result
