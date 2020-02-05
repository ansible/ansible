#!powershell

# Copyright : (c) 2019, Simon Lecoq <simon.lecoq@live.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.CamelConversion

# Specs and init
$spec = @{
    options = @{
        profiles = @{ type = "list"; elements = "str"; choices = "Domain", "Private", "Public"; default = @( "Domain", "Private", "Public" ); aliases = @( "profile" ) }
        enabled = @{ type = "str"; choices = "True", "False", "NotConfigured" }
        default_inbound_action = @{ type = "str"; choices = "NotConfigured", "Allow", "Block"; aliases = @( "inbound" ) }
        default_outbound_action = @{ type = "str"; choices = "NotConfigured", "Allow", "Block"; aliases = @( "outbound" ) }
        log_file_name = @{ type = "path"; aliases = @( "log_file" ) }
        log_max_size_kilobytes = @{ type = "int"; aliases = @( "log_max_size" ) }
        log_allowed = @{ type = "str"; choices = "True", "False", "NotConfigured" }
        log_blocked = @{ type = "str"; choices = "True", "False", "NotConfigured" }
        log_ignored = @{ type = "str"; choices = "True", "False", "NotConfigured" }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$module.Diff.before = @{}
$module.Diff.after = @{}
$check_mode = $module.CheckMode
$supported_options_list = @("Enabled", "DefaultInBoundAction", "DefaultOutBoundAction", "LogFileName", "LogMaxSizeKilobytes", "LogAllowed", "LogBlocked", "LogIgnored")

# Check that required cmdlets are available
try {
    Get-Command Get-NetFirewallProfile | Out-Null
    Get-Command Set-NetFirewallProfile | Out-Null
}
catch {
    $module.FailJson("This Powershell version does not support the following required cmdlets : Get-NetfirewallProfile and Set-NetFirewallProfile.")
}

# Params init
$profiles = $module.Params.profiles
$enabled = $module.Params.enabled
$default_inbound_action = $module.Params.default_inbound_action
$default_outbound_action = $module.Params.default_outbound_action
$log_file_name = $module.Params.log_file_name
$log_max_size_kilobytes = $module.Params.log_max_size_kilobytes
$log_allowed = $module.Params.log_allowed
$log_blocked = $module.Params.log_blocked
$log_ignored = $module.Params.log_ignored

# Process
foreach ($profile in $profiles) {

    # Get settings for current profile
    $current_state = @{}
    $current_state_object = (Get-NetFirewallProfile -Name $profile | Select-Object -Property $supported_options_list)
    $current_state_object.psobject.properties | ForEach-Object { $current_state[$_.Name] = $_.value.toString() }
    $current_state = Convert-DictToSnakeCase($current_state)
    $current_state.log_max_size_kilobytes = [int]$current_state.log_max_size_kilobytes
    $module.Result.$profile = $current_state
    $module.Result.$profile.changed = $false
    $module.Diff.before.$profile = $module.Result.$profile

    # Apply editions
    if (($null -ne $enabled) -and ($enabled -ne $current_state.enabled)) {
        Set-NetFirewallProfile -Name $profile -Enabled $enabled -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.enabled = $enabled
    }

    if (($null -ne $default_inbound_action) -and ($default_inbound_action -ne $current_state.default_inbound_action)) {
        Set-NetFirewallProfile -Name $profile -DefaultInboundAction $default_inbound_action -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.default_inbound_action = $default_inbound_action
    }

    if (($null -ne $default_outbound_action) -and ($default_outbound_action -ne $current_state.default_outbound_action)) {
        Set-NetFirewallProfile -Name $profile -DefaultOutboundAction $default_outbound_action -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.default_outbound_action = $default_outbound_action
    }

    if (($null -ne $log_file_name) -and ($log_file_name -ne $current_state.log_file_name)) {
        Set-NetFirewallProfile -Name $profile -LogFileName $log_file_name -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.log_file_name = $log_file_name
    }

    if (($null -ne $log_max_size_kilobytes) -and ($log_max_size_kilobytes -ne $current_state.log_max_size_kilobytes)) {
        Set-NetFirewallProfile -Name $profile -LogMaxSizeKilobytes $log_max_size_kilobytes -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.log_max_size_kilobytes = $log_max_size_kilobytes
    }

    if (($null -ne $log_allowed) -and ($log_allowed -ne $current_state.log_allowed)) {
        Set-NetFirewallProfile -Name $profile -LogAllowed $log_allowed -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.log_allowed = $log_allowed
    }

    if (($null -ne $log_blocked) -and ($log_blocked -ne $current_state.log_blocked)) {
        Set-NetFirewallProfile -Name $profile -LogBlocked $log_blocked -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.log_blocked = $log_blocked
    }

    if (($null -ne $log_ignored) -and ($log_ignored -ne $current_state.log_ignored)) {
        Set-NetFirewallProfile -Name $profile -LogIgnored $log_ignored -WhatIf:$check_mode
        $module.Result.$profile.changed = $true
        $module.Result.$profile.log_ignored = $log_ignored
    }

    # Update results
    $module.Result.changed = $module.Result.changed -or $module.Result.$profile.changed
    $module.Diff.after.$profile = $module.Result.$profile

}

$module.ExitJson()
