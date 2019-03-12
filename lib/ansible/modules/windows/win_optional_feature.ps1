#!powershell

# Copyright: (c) 2019, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$result = @{
    rc = 0
    changed = $false
}
$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$include_parent = Get-AnsibleParam -obj $params -name "include_parent" -type "bool" -default $false

$win_version = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\").ProductName
if ($win_version -notlike "Windows 10*") {
    Fail-Json -obj $result -message "This version of Windows does not support the Enable-WindowsOptionalFeature."
}

$feature_state_start = Get-WindowsOptionalFeature -Online -FeatureName $name
if (-not $feature_state_start) {
    $result.rc = 1
    $result.failed = $true
    Fail-Json -obj $result -message "Failed to find feature."
}


if ($state -eq "present") {
    if ($feature_state_start.State -notlike "Enabled*") {
        $install_args = @{
            FeatureName = $name
            All = $include_parent
        }
        
        if ($source) {
            if (-not (Test-Path -Path $source)) {
                $result.rc = 1
                $result.failed = $true
                Fail-Json -obj $result -message "Path could not be found"
            }
            $install_args.Source = $source
        }


        if ($check_mode) {
            $result.changed = $true
            $feature_result = @{
                name = $feature.FeatureName
                display_name = $feature.DisplayName
                description = $feature.Description
                state = "Enabled"
            }
            $result.feature_result = $feature_result
            Exit-Json -obj $result
        }
        try {
            $action_result = Enable-WindowsOptionalFeature -Online -NoRestart @install_args
        } catch {
            $result.rc = 1
            $result.failed = $true
            Fail-Json -obj $result -message "$($_.Exception.Message)"
        }
       
        $result.reboot_required = $action_result.RestartNeeded
        $result.changed = $true
    }
} else {
    if ($feature_state_start.State -notlike "Disabled*") {
        $remove_args = @{
            FeatureName = $name
        }

        if ($check_mode) {
            $result.changed = $true
            $feature_result = @{
                name = $feature.FeatureName
                display_name = $feature.DisplayName
                description = $feature.Description
                state = "Disabled"
            }
            $result.feature_result = $feature_result
            Exit-Json -obj $result
        }
        try {
            $action_result = Disable-WindowsOptionalFeature -Online -NoRestart @remove_args
        } catch {
            $result.rc = 1
            $result.failed = $true
            Fail-Json -obj $result -message "$($_.Exception.Message)"
        }
      
        $result.reboot_required = $action_result.RestartNeeded
        $result.changed = $true
    }
}
$feature = Get-WindowsOptionalFeature -Online -FeatureName $name
$feature_result = @{
    name = $feature.FeatureName
    display_name = $feature.DisplayName
    description = $feature.Description
    state = $feature.State.ToString()
}
$result.feature_result = $feature_result
Exit-Json -obj $result
