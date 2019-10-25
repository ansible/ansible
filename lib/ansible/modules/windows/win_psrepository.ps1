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

$result = New-Object -TypeName PSObject -Property @{"changed" = $false}
$repositoryProperties = New-Object -TypeName PSObject -Property @{"name" = $name; "source" = $source; "installationPolicy" = $installationpolicy }

function Update-NuGetPackageProvider {
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object { ($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201") }
    if ($null -eq $PackageProvider) {
        Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force | Out-Null
    }
}

$repository = Get-PSRepository -Name $repositoryProperties.Name -ErrorAction Ignore -WarningAction Ignore

if($null -eq $repository) {
    if(-not $check_mode){
        if($state -eq "present") {
            try
            {
                Register-PSRepository -Name $repositoryProperties.Name -SourceLocation $repositoryProperties.source -InstallationPolicy $repositoryProperties.installationPolicy
                $result.changed = $true
            }
            catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
    }
}

if($null -ne $repository) {
    if(-not $check_mode) {
        if($state -eq "absent") {
            try
            {
                Unregister-PSRepository -Name $repositoryProperties.Name
                $result.changed = $true
            }
            catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
        else {

            if($repository.SourceLocation -ne $repositoryProperties.source -and $null -ne $repositoryProperties.source) {
                Set-PSRepository -Name $repositoryProperties.Name -SourceLocation $repositoryProperties.source
                $result.changed = $true
            }

            if($repository.InstallationPolicy -ne $repositoryProperties.installationPolicy -and $null -ne $repositoryProperties.installationPolicy) {
                Set-PSRepository -Name $repositoryProperties.Name -InstallationPolicy $repositoryProperties.installationPolicy
                $result.changed = $true
            }

        }
    }
}

Exit-Json -obj $result
