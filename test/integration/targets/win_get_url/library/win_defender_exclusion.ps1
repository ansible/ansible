#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent", "present"

$result = @{
    changed = $false
}

# This is a test module, just skip instead of erroring out if we cannot set the rule
if ($null -eq (Get-Command -Name Get-MpPreference -ErrorAction SilentlyContinue)) {
    $result.skipped = $true
    $result.msg = "Skip as cannot set exclusion rule"
    Exit-Json -obj $result
}

$exclusions = (Get-MpPreference).ExclusionPath
if ($null -eq $exclusions) {
    $exclusions = @()
}

if ($state -eq "absent") {
    if ($path -in $exclusions) {
        Remove-MpPreference -ExclusionPath $path
        $result.changed = $true
    }
} else {
    if ($path -notin $exclusions) {
        Add-MpPreference -ExclusionPath $path
        $result.changed = $true
    }
}

Exit-Json -obj $result
