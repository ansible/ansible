#!powershell

# Copyright: (c) 2019, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        name = @{ type = "list"; required = $true }
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

$module.Result.reboot_required = $false

if (-not (Get-Command -Name Enable-WindowsOptionalFeature -ErrorAction SilentlyContinue)) {
    $module.FailJson("This version of Windows does not support the Enable-WindowsOptionalFeature.")
}

$changed_features = [System.Collections.Generic.List`1[String]]@()
foreach ($feature_name in $name) {
    try {
        $feature_state_start = Get-WindowsOptionalFeature -Online -FeatureName $feature_name
    } catch [System.Runtime.InteropServices.COMException] {
        # Server 2012 raises a COMException and doesn't return $null even with -ErrorAction SilentlyContinue
        $feature_state_start = $null
    }
    if (-not $feature_state_start) {
        $module.FailJson("Failed to find feature '$feature_name'")
    }

    if ($state -eq "present" -and $feature_state_start.State -notlike "Enabled*") {
        # Matches for "Enabled" and "EnabledPending"
        $changed_features.Add($feature_name)
    } elseif ($state -eq "absent" -and $feature_state_start.State -notlike "Disabled*") {
        # Matches for Disabled, DisabledPending, and DisabledWithPayloadRemoved
        $changed_features.Add($feature_name)
    }
}


if ($state -eq "present" -and $changed_features.Count -gt 0) {
    $install_args = @{
        FeatureName = $changed_features
        All = $include_parent
    }

    if ($source) {
        if (-not (Test-Path -LiteralPath $source)) {
            $module.FailJson("Path could not be found '$source'")
        }
        $install_args.Source = $source
    }

    if (-not $module.CheckMode) {
        $action_result = Enable-WindowsOptionalFeature -Online -NoRestart @install_args
        $module.Result.reboot_required = $action_result.RestartNeeded
    }
    $module.Result.changed = $true
} elseif ($state -eq "absent" -and $changed_features.Count -gt 0) {
    $remove_args = @{
        FeatureName = $changed_features
    }

    if (-not $module.CheckMode) {
        $action_result = Disable-WindowsOptionalFeature -Online -NoRestart @remove_args
        $module.Result.reboot_required = $action_result.RestartNeeded
    }
    $module.Result.changed = $true
}
$module.ExitJson()

