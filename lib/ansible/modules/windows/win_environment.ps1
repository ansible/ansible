#!powershell

# Copyright: (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        name = @{ type = "str"; required = $true }
        level = @{ type = "str"; choices = "machine", "process", "user"; required = $true }
        state = @{ type = "str"; choices = "absent", "present"; default = "present" }
        value = @{ type = "str" }
    }
    required_if = @(,@("state", "present", @("value")))
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name
$level = $module.Params.level
$state = $module.Params.state
$value = $module.Params.value

$before_value = [Environment]::GetEnvironmentVariable($name, $level)
$module.Result.before_value = $before_value
$module.Result.value = $value

# When removing environment, set value to $null if set
if ($state -eq "absent" -and $value) {
    $module.Warn("When removing environment variable '$name' it should not have a value '$value' set")
    $value = $null
} elseif ($state -eq "present" -and (-not $value)) {
    $module.FailJson("When state=present, value must be defined and not an empty string, if you wish to remove the envvar, set state=absent")
}

$module.Diff.before = @{ $level = @{} }
if ($before_value) {
    $module.Diff.before.$level.$name = $before_value
}
$module.Diff.after = @{ $level = @{} }
if ($value) {
    $module.Diff.after.$level.$name = $value
}

if ($state -eq "present" -and $before_value -ne $value) {
    if (-not $module.CheckMode) {
        [Environment]::SetEnvironmentVariable($name, $value, $level)
    }
    $module.Result.changed = $true

} elseif ($state -eq "absent" -and $null -ne $before_value) {
    if (-not $module.CheckMode) {
        [Environment]::SetEnvironmentVariable($name, $null, $level)
    }
    $module.Result.changed = $true
}

$module.ExitJson()

