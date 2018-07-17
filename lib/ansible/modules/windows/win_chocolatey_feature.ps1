#!powershell

# Copyright: (c), 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "enabled" -validateset "disabled", "enabled"

$result = @{
    changed = $false
}

Function Get-ChocolateyFeatures {
    param($choco_app)

    $res = Run-Command -command "`"$($choco_app.Path)`" feature list -r"
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to list Chocolatey features: $($res.stderr)"
    }
    $feature_info = @{}
    $res.stdout -split "`r`n" | Where-Object { $_ -ne "" } | ForEach-Object {
        $feature_split = $_ -split "\|"
        $feature_info."$($feature_split[0])" = $feature_split[1] -eq "Enabled"
    }

    return ,$feature_info
}

Function Set-ChocolateyFeature {
    param(
        $choco_app,
        $name,
        $enabled
    )

    if ($enabled) {
        $state_string = "enable"
    } else {
        $state_string = "disable"
    }
    $res = Run-Command -command "`"$($choco_app.Path)`" feature $state_string --name `"$name`""
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to set Chocolatey feature $name to $($state_string): $($res.stderr)"
    }
}

$choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $choco_app) {
    Fail-Json -obj $result -message "Failed to find Chocolatey installation, make sure choco.exe is in the PATH env value"
}

$feature_info = Get-ChocolateyFeatures -choco_app $choco_app
if ($name -notin $feature_info.keys) {
    Fail-Json -obj $result -message "Invalid feature name '$name' specified, valid features are: $($feature_info.keys -join ', ')"
}

$expected_status = $state -eq "enabled"
$feature_status = $feature_info.$name
if ($feature_status -ne $expected_status) {
    if (-not $check_mode) {
        Set-ChocolateyFeature -choco_app $choco_app -name $name -enabled $expected_status
    }
    $result.changed = $true
}

Exit-Json -obj $result
