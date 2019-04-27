#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy

# basic script to get the lsit of users in a particular right
# this is quite complex to put as a simple script so this is
# just a simple module

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $false
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true

$result = @{
    changed = $false
    users = @()
}

Function Get-Username($sid) {
    $object = New-Object System.Security.Principal.SecurityIdentifier($sid)
    $user = $object.Translate([System.Security.Principal.NTAccount])
    $user.Value
}

$secedit_ini_path = [IO.Path]::GetTempFileName()
&SecEdit.exe /export /cfg $secedit_ini_path /quiet
$secedit_ini = Get-Content -LiteralPath $secedit_ini_path
Remove-Item -LiteralPath $secedit_ini_path -Force

foreach ($line in $secedit_ini) {
    if ($line.ToLower().StartsWith("$($name.ToLower()) = ")) {
        $right_split = $line -split "="
        $existing_users = $right_split[-1].Trim() -split ","
        foreach ($user in $existing_users) {
            if ($user.StartsWith("*S")) {
                $result.users += Get-Username -sid $user.substring(1)
            } else {
                $result.users += $user
            }
        }
    }
}

Exit-Json $result
