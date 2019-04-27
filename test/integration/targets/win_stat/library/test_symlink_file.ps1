#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil

$params = Parse-Args $args

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$target = Get-AnsibleParam -obj $params -name "target" -type "path" -failifempty $($state -eq "present")

$result = @{
    changed = $false
}

if ($state -eq "absent") {
    if (Test-Path -LiteralPath $src) {
        Load-LinkUtils
        Remove-Link -link_path $src
        $result.changed = $true
    }
} else {
    if (-not (Test-Path -LiteralPath $src)) {
        Load-LinkUtils
        New-Link -link_path $src -link_target $target -link_type "link"
        $result.changed = $true
    }
}

Exit-Json -obj $result
