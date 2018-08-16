#!powershell

# Copyright: (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$value = Get-AnsibleParam -obj $params -name "value" -type "str"
$level = Get-AnsibleParam -obj $params -name "level" -type "str" -validateSet "machine","user","process" -failifempty $true

$before_value = [Environment]::GetEnvironmentVariable($name, $level)

$result = @{
    before_value = $before_value
    changed = $false
    value = $value
}

# When removing environment, set value to $null if set
if ($state -eq "absent" -and $value) {
    Add-Warning -obj $result -message "When removing environment variable '$name' it should not have a value '$value' set"
    $value = $null
} elseif ($state -eq "present" -and (-not $value)) {
    Fail-Json -obj $result -message "When state=present, value must be defined and not an empty string, if you wish to remove the envvar, set state=absent"
}

if ($state -eq "present" -and $before_value -ne $value) {

    if (-not $check_mode) {
        [Environment]::SetEnvironmentVariable($name, $value, $level)
    }
    $result.changed = $true

    if ($diff_mode) {
        if ($before_value -eq $null) {
            $result.diff = @{
                prepared = " [$level]`n+$name = $value`n"
            }
        } else {
            $result.diff = @{
                prepared = " [$level]`n-$name = $before_value`n+$name = $value`n"
            }
        }
    }

} elseif ($state -eq "absent" -and $before_value -ne $null) {

    if (-not $check_mode) {
        [Environment]::SetEnvironmentVariable($name, $null, $level)
    }
    $result.changed = $true

    if ($diff_mode) {
        $result.diff = @{
            prepared = " [$level]`n-$name = $before_value`n"
        }
    }

}

Exit-Json -obj $result
