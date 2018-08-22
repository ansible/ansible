#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent", "present"
$value = Get-AnsibleParam -obj $params -name "value" -type "str" -failifempty ($state -eq "present")

$result = @{
    changed = $false
}
if ($diff) {
    $result.diff = @{
        before = $null
        after = $null
    }
}

if ($state -eq "present") {
    if ($value -eq "") {
        Fail-Json -obj $result -message "Cannot set Chocolatey config as an empty string when state=present, use state=absent instead"
    }
    # make sure bool values are lower case
    if ($value -ceq "True" -or $value -ceq "False") {
        $value = $value.ToLower()
    }
}

Function Get-ChocolateyConfig {
    param($choco_app)

    # 'choco config list -r' does not display an easily parsable config entries
    # It contains config/sources/feature in the one command, and is in the
    # structure 'configKey = configValue | description', if the key or value
    # contains a = or |, it will make it quite hard to easily parse it,
    # compared to reading an XML file that already delimits these values
    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -Path $choco_config_path)) {
        Fail-Json -obj $result -message "Expecting Chocolatey config file to exist at '$choco_config_path'"
    }

    try {
        [xml]$choco_config = Get-Content -Path $choco_config_path
    } catch {
        Fail-Json -obj $result -message "Failed to parse Chocolatey config file at '$choco_config_path': $($_.Exception.Message)"
    }

    $config_info = @{}
    foreach ($config in $choco_config.chocolatey.config.GetEnumerator()) {
        $config_info."$($config.key)" = $config.value
    }

    return ,$config_info
}

Function Remove-ChocolateyConfig {
    param(
        $choco_app,
        $name
    )
    $command = Argv-ToString -arguments @($choco_app.Path, "config", "unset", "--name", $name)
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to unset Chocolatey config for '$name': $($res.stderr)"
    }
}

Function Set-ChocolateyConfig {
    param(
        $choco_app,
        $name,
        $value
    )
    $command = Argv-ToString -arguments @($choco_app.Path, "config", "set", "--name", $name, "--value", $value)
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to set Chocolatey config for '$name' to '$value': $($res.stderr)"
    }
}

$choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $choco_app) {
    Fail-Json -obj $result -message "Failed to find Chocolatey installation, make sure choco.exe is in the PATH env value"
}

$config_info = Get-ChocolateyConfig -choco_app $choco_app
if ($name -notin $config_info.Keys) {
    Fail-Json -obj $result -message "The Chocolatey config '$name' is not an existing config value, check the spelling. Valid config names: $($config_info.Keys -join ', ')"
}
if ($diff) {
    $result.diff.before = $config_info.$name
}

if ($state -eq "absent" -and $config_info.$name -ne "") {
    if (-not $check_mode) {
        Remove-ChocolateyConfig -choco_app $choco_app -name $name
    }
    $result.changed = $true
# choco.exe config set is not case sensitive, it won't make a change if the
# value is the same but doesn't match
} elseif ($state -eq "present" -and $config_info.$name -ne $value) {
    if (-not $check_mode) {
        Set-ChocolateyConfig -choco_app $choco_app -name $name -value $value
    }
    $result.changed = $true
    if ($diff) {
        $result.diff.after = $value
    }
}

Exit-Json -obj $result
