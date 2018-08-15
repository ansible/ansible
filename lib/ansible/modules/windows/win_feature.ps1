#!powershell

# Copyright: (c) 2014, Paul Durivage <paul.durivage@rackspace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Import-Module -Name ServerManager

$result = @{
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "list" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"

$include_sub_features = Get-AnsibleParam -obj $params -name "include_sub_features" -type "bool" -default $false
$include_management_tools = Get-AnsibleParam -obj $params -name "include_management_tools" -type "bool" -default $false
$source = Get-AnsibleParam -obj $params -name "source" -type "str"

$install_cmdlet = $false
if (Get-Command -Name Install-WindowsFeature -ErrorAction SilentlyContinue) {
    Set-Alias -Name Install-AnsibleWindowsFeature -Value Install-WindowsFeature
    Set-Alias -Name Uninstall-AnsibleWindowsFeature -Value Uninstall-WindowsFeature
    $install_cmdlet = $true
} elseif (Get-Command -Name Add-WindowsFeature -ErrorAction SilentlyContinue) {
    Set-Alias -Name Install-AnsibleWindowsFeature -Value Add-WindowsFeature
    Set-Alias -Name Uninstall-AnsibleWindowsFeature -Value Remove-WindowsFeature
} else {
    Fail-Json -obj $result -message "This version of Windows does not support the cmdlets Install-WindowsFeature or Add-WindowsFeature"
}

if ($state -eq "present") {
    $install_args = @{
        Name = $name
        IncludeAllSubFeature = $include_sub_features
        Restart = $false
        WhatIf = $check_mode
        ErrorAction = "Stop"
    }

    if ($install_cmdlet) {
        $install_args.IncludeManagementTools = $include_management_tools
        $install_args.Confirm = $false
        if ($source) {
            if (-not (Test-Path -Path $source)) {
                Fail-Json -obj $result -message "Failed to find source path $source for feature install"
            }
            $install_args.Source = $source
        }
    }

    try {
        $action_results = Install-AnsibleWindowsFeature @install_args
    } catch {
        Fail-Json -obj $result -message "Failed to install Windows Feature: $($_.Exception.Message)"
    }
} else {
    $uninstall_args = @{
        Name = $name
        Restart = $false
        WhatIf = $check_mode
        ErrorAction = "Stop"
    }
    if ($install_cmdlet) {
        $uninstall_args.IncludeManagementTools = $include_management_tools
    }

    try {
        $action_results = Uninstall-AnsibleWindowsFeature @uninstall_args
    } catch {
        Fail-Json -obj $result -message "Failed to uninstall Windows Feature: $($_.Exception.Message)"
    }
}

# Loop through results and create a hash containing details about
# each role/feature that is installed/removed
# $action_results.FeatureResult is not empty if anything was changed
$feature_results = @()
foreach ($action_result in $action_results.FeatureResult) {
    $message = @()
    foreach ($msg in $action_result.Message) {
        $message += @{
            message_type = $msg.MessageType.ToString()
            error_code = $msg.ErrorCode
            text = $msg.Text
        }
    }

    $feature_results += @{
        id = $action_result.Id
        display_name = $action_result.DisplayName
        message = $message
        reboot_required = ConvertTo-Bool -obj $action_result.RestartNeeded
        skip_reason = $action_result.SkipReason.ToString()
        success = ConvertTo-Bool -obj $action_result.Success
        restart_needed = ConvertTo-Bool -obj $action_result.RestartNeeded
    }
    $result.changed = $true
}
$result.feature_result = $feature_results
$result.success = ConvertTo-Bool -obj $action_results.Success
$result.exitcode = $action_results.ExitCode.ToString()
$result.reboot_required = ConvertTo-Bool -obj $action_results.RestartNeeded
# controls whether Ansible will fail or not
$result.failed = (-not $action_results.Success)

# DEPRECATED 2.4, remove in 2.8 (standardize naming to "reboot_required")
$result.restart_needed = $result.reboot_required

Exit-Json -obj $result
