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
$module.Result.rc = 0

$name = $module.Params.name
$state = $module.Params.state
$source = $module.Params.source
$include_parent = $module.Params.include_parent

$win_version = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\").ProductName
if ($win_version -notlike "Windows 10*") {
    $module.FailJson("This version of Windows does not support the Enable-WindowsOptionalFeature.")
}

$feature_state_start = Get-WindowsOptionalFeature -Online -FeatureName $name
if (-not $feature_state_start) {
    $module.Result.rc = 1
    $module.FailJson("Failed to find feature.")
}


if ($state -eq "present") {
    if ($feature_state_start.State -notlike "Enabled*") {
        $install_args = @{
            FeatureName = $name
            All = $include_parent
        }

        if ($source) {
            if (-not (Test-Path -Path $source)) {
                $module.Result.rc = 1
                $module.FailJson("Path could not be found")
            }
            $install_args.Source = $source
        }

        if ($module.CheckMode) {
            $module.Result.changed = $true
            $feature_result = @{
                name = $feature.FeatureName
                display_name = $feature.DisplayName
                description = $feature.Description
                state = "Enabled"
            }
            $module.Result.feature_result = $feature_result
            $module.ExitJson()
        }
        try {
            $action_result = Enable-WindowsOptionalFeature -Online -NoRestart @install_args
        } catch {
            $module.Result.rc = 1
            $module.FailJson("$($_.Exception.Message)")
        }
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
            $feature_result = @{
                name = $feature.FeatureName
                display_name = $feature.DisplayName
                description = $feature.Description
                state = "Disabled"
            }
            $module.Result.feature_result = $feature_result
			$module.ExitJson()
        }
        try {
            $action_result = Disable-WindowsOptionalFeature -Online -NoRestart @remove_args
        } catch {
            $module.Result.rc = 1
            $module.FailJson("$($_.Exception.Message)")
        }
        $module.Result.reboot_required = $action_result.RestartNeeded
        $module.Result.changed = $true
    }
}
$feature = Get-WindowsOptionalFeature -Online -FeatureName $name
$feature_result = @{
    name = $feature.FeatureName
    display_name = $feature.DisplayName
    description = $feature.Description
    state = $feature.State.ToString()
}
$module.Result.feature_result = $feature_result
$module.ExitJson()
