#!powershell

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installationpolicy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -default "trusted" -validateset "trusted", "untrusted"

$result = @{"changed" = $false}

Function Install-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [Parameter(Mandatory=$true)]
        [String]$SourceLocation,
        [String]$InstallationPolicy,
        [Bool]$CheckMode
    )

    try {
        if (-not $CheckMode) {
            Register-PSRepository -Name $Name -SourceLocation $SourceLocation -InstallationPolicy $InstallationPolicy
        }
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
    $Repo = Get-PSRepository -Name $Name -ErrorAction Ignore

    if ( $null -ne $Repo) {

        try {
            if (-not $CheckMode) {
                Unregister-PSRepository -Name $Name
            }
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
        if (-not $CheckMode) {
            Set-PSRepository -Name $Name -InstallationPolicy $InstallationPolicy
        }
        $result.changed = $true
    }
    catch {
        $ErrorMessage = "Problems changing the InstallationPolicy for $($Name) repository: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
    }
}

if ($state -eq "present") {

    $Repo = Get-PSRepository -Name $name -ErrorAction Ignore

    if ($null -eq $Repo){
        Install-Repository -Name $name -SourceLocation $source -InstallationPolicy $installationpolicy -CheckMode $check_mode
    }
    else {
        if ( $Repo.InstallationPolicy -ne $installationpolicy ) {
            Set-Repository -Name $name -InstallationPolicy $installationpolicy -CheckMode $check_mode
        }
    }
}
elseif ($state -eq "absent") {
    Remove-Repository -Name $name -CheckMode $check_mode
}

Exit-Json $result
