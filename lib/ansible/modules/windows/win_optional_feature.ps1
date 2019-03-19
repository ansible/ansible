#!powershell

# Copyright: (c) 2019, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
	options = @{
		name = @{ type = "str"; required = $true }
		state = @{ type = "str"; default = "present"; choices = @("absent", "present") }
		source = @{ type = "str" }
		include_parent = @{ type = "bool"; default = $false }
	}
	supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name
$state = $module.Params.state
$source = $module.Params.source
$include_parent = $module.Params.include_parent

if (-not (Get-Command -Name Enable-WindowsOptionalFeature -ErrorAction SilentlyContinue)) {
    $module.FailJson("This version of Windows does not support the Enable-WindowsOptionalFeature.")
}

$feature_state_start = Get-WindowsOptionalFeature -Online -FeatureName $name
if (-not $feature_state_start) {
    $module.FailJson("Failed to find feature '$name'")
}

$feature_result = @{
    name = $feature_state_start.FeatureName
    display_name = $feature_state_start.DisplayName
    description = $feature_state_start.Description
}
if ($state -eq "present") {
    if ($feature_state_start.State -notlike "Enabled*") {
        $install_args = @{
            FeatureName = $name
            All = $include_parent
        }

        if ($source) {
            if (-not (Test-Path -LiteralPath $source)) {
                $module.FailJson("Path could not be found '$source'")
            }
            $install_args.Source = $source
        }

        if ($module.CheckMode) {
            $module.Result.changed = $true
			break
        }
        $action_result = Enable-WindowsOptionalFeature -Online -NoRestart @install_args

        $module.Result.reboot_required = $action_result.RestartNeeded
        $module.Result.changed = $true
    }
} else {
    if ($feature_state_start.State -notlike "Disabled*") {
        $remove_args = @{
            FeatureName = $name
        }

        if ($check_mode) {
            $module.Result.changed = $true
			break
        }
        $action_result = Disable-WindowsOptionalFeature -Online -NoRestart @remove_args

        $module.Result.reboot_required = $action_result.RestartNeeded
        $module.Result.changed = $true
    }
}
$module.ExitJson()
