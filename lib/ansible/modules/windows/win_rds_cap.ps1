#!powershell

# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

# List of authentication methods as string. Used for parameter validation and conversion to integer flag, so order is important!
$auth_methods_set = @("none", "password", "smartcard", "both")
# List of session timeout actions as string. Used for parameter validation and conversion to integer flag, so order is important!
$session_timeout_actions_set = @("disconnect", "reauth")

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present","enabled","disabled"
$auth_method = Get-AnsibleParam -obj $params -name "auth_method" -type "str" -validateset $auth_methods_set
$order = Get-AnsibleParam -obj $params -name "order" -type "int"
$session_timeout = Get-AnsibleParam -obj $params -name "session_timeout" -type "int"
$session_timeout_action = Get-AnsibleParam -obj $params -name "session_timeout_action" -type "str" -default "disconnect" -validateset $session_timeout_actions_set
$idle_timeout = Get-AnsibleParam -obj $params -name "idle_timeout" -type "int"
$allow_only_sdrts_servers = Get-AnsibleParam -obj $params -name "allow_only_sdrts_servers" -type "bool"
$user_groups = Get-AnsibleParam -obj $params -name "user_groups" -type "list"
$computer_groups = Get-AnsibleParam -obj $params -name "computer_groups" -type "list"

# Device redirections
$redirect_clipboard = Get-AnsibleParam -obj $params -name "redirect_clipboard" -type "bool"
$redirect_drives = Get-AnsibleParam -obj $params -name "redirect_drives" -type "bool"
$redirect_printers = Get-AnsibleParam -obj $params -name "redirect_printers" -type "bool"
$redirect_serial = Get-AnsibleParam -obj $params -name "redirect_serial" -type "bool"
$redirect_pnp = Get-AnsibleParam -obj $params -name "redirect_pnp" -type "bool"


function Get-CAP([string] $name) {
    $cap_path = "RDS:\GatewayServer\CAP\$name"
    $cap = @{
        Name = $name
    }

    # Fetch CAP properties
    Get-ChildItem -Path $cap_path | ForEach-Object { $cap.Add($_.Name,$_.CurrentValue) }
    # Convert boolean values
    $cap.Enabled = $cap.Status -eq 1
    $cap.Remove("Status")
    $cap.AllowOnlySDRTSServers = $cap.AllowOnlySDRTSServers -eq 1

    # Convert multiple choices values
    $cap.AuthMethod = $auth_methods_set[$cap.AuthMethod]
    $cap.SessionTimeoutAction = $session_timeout_actions_set[$cap.SessionTimeoutAction]

    # Fetch CAP device redirection settings
    $cap.DeviceRedirection = @{}
    Get-ChildItem -Path "$cap_path\DeviceRedirection" | ForEach-Object { $cap.DeviceRedirection.Add($_.Name, ($_.CurrentValue -eq 1)) }

    # Fetch CAP user and computer groups in Down-Level Logon format
    $cap.UserGroups = @(
        Get-ChildItem -Path "$cap_path\UserGroups" | 
            Select-Object -ExpandProperty Name |
            ForEach-Object { Convert-FromSID -sid (Convert-ToSID -account_name $_) }
    )
    $cap.ComputerGroups = @(
        Get-ChildItem -Path "$cap_path\ComputerGroups" |
            Select-Object -ExpandProperty Name |
            ForEach-Object { Convert-FromSID -sid (Convert-ToSID -account_name $_) }
    )

    return $cap
}

function Set-CAPPropertyValue {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param (
        [Parameter(Mandatory=$true)]
        [string] $name,
        [Parameter(Mandatory=$true)]
        [string] $property,
        [Parameter(Mandatory=$true)]
        $value,
        [Parameter()]
        $resultobj = @{}
    )

    $cap_path = "RDS:\GatewayServer\CAP\$name"

    try {
        Set-Item -Path "$cap_path\$property" -Value $value -ErrorAction Stop
    } catch {
        Fail-Json -obj $resultobj -message "Failed to set property $property of CAP ${name}: $($_.Exception.Message)"
    }
}

$result = @{
  changed = $false
}
$diff_text = $null

# Validate CAP name
if ($name -match "[*/\\;:?`"<>|\t]+") {
    Fail-Json -obj $result -message "Invalid character in CAP name."
}

# Validate user groups
if ($null -ne $user_groups) {
    if ($user_groups.Count -lt 1) {
        Fail-Json -obj $result -message "Parameter 'user_groups' cannot be an empty list."
    }

    $user_groups = $user_groups | ForEach-Object {
        $group = $_
        # Test that the group is resolvable on the local machine
        $sid = Convert-ToSID -account_name $group
        if (!$sid) {
            Fail-Json -obj $result -message "$group is not a valid user group on the host machine or domain"
        }

        # Return the normalized group name in Down-Level Logon format
        Convert-FromSID -sid $sid
    }
    $user_groups = @($user_groups)
}

# Validate computer groups
if ($null -ne $computer_groups) {
    $computer_groups = $computer_groups | ForEach-Object {
        $group = $_
        # Test that the group is resolvable on the local machine
        $sid = Convert-ToSID -account_name $group
        if (!$sid) {
            Fail-Json -obj $result -message "$group is not a valid computer group on the host machine or domain"
        }

        # Return the normalized group name in Down-Level Logon format
        Convert-FromSID -sid $sid
    }
    $computer_groups = @($computer_groups)
}

# Validate order parameter
if ($null -ne $order -and $order -lt 1) {
    Fail-Json -obj $result -message "Parameter 'order' must be a strictly positive integer."
}

# Ensure RemoteDesktopServices module is loaded
if ($null -eq (Get-Module -Name RemoteDesktopServices -ErrorAction SilentlyContinue)) {
    Import-Module -Name RemoteDesktopServices
}

# Check if a CAP with the given name already exists
$cap_exist = Test-Path -Path "RDS:\GatewayServer\CAP\$name"

if ($state -eq 'absent') {
    if ($cap_exist) {
        Remove-Item -Path "RDS:\GatewayServer\CAP\$name" -Recurse -WhatIf:$check_mode
        $diff_text += "-[$name]"
        $result.changed = $true
    }
} else {
    $diff_text_added_prefix = ''
    if (-not $cap_exist) {
        if ($null -eq $user_groups) {
            Fail-Json -obj $result -message "User groups must be defined to create a new CAP."
        }

        # Auth method is required when creating a new CAP. Set it to password by default.
        if ($null -eq $auth_method) {
            $auth_method = "password"
        }

        # Create a new CAP
        if (-not $check_mode) {
            $CapArgs = @{
                Name = $name
                UserGroupNames = $user_groups -join ';'
            }
            $return = Invoke-CimMethod -Namespace Root\CIMV2\TerminalServices -ClassName Win32_TSGatewayConnectionAuthorizationPolicy -MethodName Create -Arguments $CapArgs
            if ($return.ReturnValue -ne 0) {
                Fail-Json -obj $result -message "Failed to create CAP $name (code: $($return.ReturnValue))"
            }
        }

        $cap_exist = -not $check_mode

        $diff_text_added_prefix = '+'
        $result.changed = $true
    }

    $diff_text += "$diff_text_added_prefix[$name]`n"

    # We cannot configure a CAP that was created above in check mode as it won't actually exist
    if($cap_exist) {
        $cap = Get-CAP -Name $name
        $wmi_cap = Get-CimInstance -ClassName Win32_TSGatewayConnectionAuthorizationPolicy -Namespace Root\CIMv2\TerminalServices -Filter "name='$($name)'"

        if ($state -in @('disabled', 'enabled')) {
            $cap_enabled = $state -ne 'disabled'
            if ($cap.Enabled -ne $cap_enabled) {
                $diff_text += "-State = $(@('disabled', 'enabled')[[int]$cap.Enabled])`n+State = $state`n"
                Set-CAPPropertyValue -Name $name -Property Status -Value ([int]$cap_enabled) -ResultObj $result -WhatIf:$check_mode
                $result.changed = $true
            }
        }

        if ($null -ne $auth_method -and $auth_method -ne $cap.AuthMethod) {
            $diff_text += "-AuthMethod = $($cap.AuthMethod)`n+AuthMethod = $auth_method`n"
            Set-CAPPropertyValue -Name $name -Property AuthMethod -Value ([array]::IndexOf($auth_methods_set, $auth_method)) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $order -and $order -ne $cap.EvaluationOrder) {
            # Order cannot be greater than the total number of existing CAPs (InvalidArgument exception)
            $cap_count =  (Get-ChildItem -Path "RDS:\GatewayServer\CAP").Count
            if($order -gt $cap_count) {
                Add-Warning -obj $result -message "Given value '$order' for parameter 'order' is greater than the number of existing CAPs. The actual order will be capped to '$cap_count'."
                $order = $cap_count
            }

            $diff_text += "-Order = $($cap.EvaluationOrder)`n+Order = $order`n"
            Set-CAPPropertyValue -Name $name -Property EvaluationOrder -Value $order -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $session_timeout -and ($session_timeout -ne $cap.SessionTimeout -or $session_timeout_action -ne $cap.SessionTimeoutAction)) {
            try {
                Set-Item -Path "RDS:\GatewayServer\CAP\$name\SessionTimeout" `
                    -Value $session_timeout `
                    -SessionTimeoutAction ([array]::IndexOf($session_timeout_actions_set, $session_timeout_action)) `
                    -ErrorAction Stop `
                    -WhatIf:$check_mode
            } catch {
                Fail-Json -obj $result -message "Failed to set property ComputerGroupType of RAP ${name}: $($_.Exception.Message)"
            }

            $diff_text += "-SessionTimeoutAction = $($cap.SessionTimeoutAction)`n+SessionTimeoutAction = $session_timeout_action`n"
            $diff_text += "-SessionTimeout = $($cap.SessionTimeout)`n+SessionTimeout = $session_timeout`n"
            $result.changed = $true
        }

        if ($null -ne $idle_timeout -and $idle_timeout -ne $cap.IdleTimeout) {
            $diff_text += "-IdleTimeout = $($cap.IdleTimeout)`n+IdleTimeout = $idle_timeout`n"
            Set-CAPPropertyValue -Name $name -Property IdleTimeout -Value $idle_timeout -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $allow_only_sdrts_servers -and $allow_only_sdrts_servers -ne $cap.AllowOnlySDRTSServers) {
            $diff_text += "-AllowOnlySDRTSServers = $($cap.AllowOnlySDRTSServers)`n+AllowOnlySDRTSServers = $allow_only_sdrts_servers`n"
            Set-CAPPropertyValue -Name $name -Property AllowOnlySDRTSServers -Value ([int]$allow_only_sdrts_servers) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $redirect_clipboard -and $redirect_clipboard -ne $cap.DeviceRedirection.Clipboard) {
            $diff_text += "-RedirectClipboard = $($cap.DeviceRedirection.Clipboard)`n+RedirectClipboard = $redirect_clipboard`n"
            Set-CAPPropertyValue -Name $name -Property "DeviceRedirection\Clipboard" -Value ([int]$redirect_clipboard) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $redirect_drives -and $redirect_drives -ne $cap.DeviceRedirection.DiskDrives) {
            $diff_text += "-RedirectDrives = $($cap.DeviceRedirection.DiskDrives)`n+RedirectDrives = $redirect_drives`n"
            Set-CAPPropertyValue -Name $name -Property "DeviceRedirection\DiskDrives" -Value ([int]$redirect_drives) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $redirect_printers -and $redirect_printers -ne $cap.DeviceRedirection.Printers) {
            $diff_text += "-RedirectPrinters = $($cap.DeviceRedirection.Printers)`n+RedirectPrinters = $redirect_printers`n"
            Set-CAPPropertyValue -Name $name -Property "DeviceRedirection\Printers" -Value ([int]$redirect_printers) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $redirect_serial -and $redirect_serial -ne $cap.DeviceRedirection.SerialPorts) {
            $diff_text += "-RedirectSerial = $($cap.DeviceRedirection.SerialPorts)`n+RedirectSerial = $redirect_serial`n"
            Set-CAPPropertyValue -Name $name -Property "DeviceRedirection\SerialPorts" -Value ([int]$redirect_serial) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $redirect_pnp -and $redirect_pnp -ne $cap.DeviceRedirection.PlugAndPlayDevices) {
            $diff_text += "-RedirectPnP = $($cap.DeviceRedirection.PlugAndPlayDevices)`n+RedirectPnP = $redirect_pnp`n"
            Set-CAPPropertyValue -Name $name -Property "DeviceRedirection\PlugAndPlayDevices" -Value ([int]$redirect_pnp) -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $user_groups) {
            $groups_to_remove = @($cap.UserGroups | Where-Object { $user_groups -notcontains $_ })
            $groups_to_add = @($user_groups | Where-Object { $cap.UserGroups -notcontains $_ })

            $user_groups_diff = $null
            foreach($group in $groups_to_add) {
                if (-not $check_mode) {
                    $return = $wmi_cap | Invoke-CimMethod -MethodName AddUserGroupNames -Arguments @{ UserGroupNames = $group }
                    if ($return.ReturnValue -ne 0) {
                        Fail-Json -obj $result -message "Failed to add user group $($group) (code: $($return.ReturnValue))"
                    }
                }
                $user_groups_diff += "  +$group`n"
                $result.changed = $true
            }

            foreach($group in $groups_to_remove) {
                if (-not $check_mode) {
                    $return = $wmi_cap | Invoke-CimMethod -MethodName RemoveUserGroupNames -Arguments @{ UserGroupNames = $group }
                    if ($return.ReturnValue -ne 0) {
                        Fail-Json -obj $result -message "Failed to remove user group $($group) (code: $($return.ReturnValue))"
                    }
                }
                $user_groups_diff += "  -$group`n"
                $result.changed = $true
            }

            if($user_groups_diff) {
                $diff_text += "~UserGroups`n$user_groups_diff"
            }
        }

        if ($null -ne $computer_groups) {
            $groups_to_remove = @($cap.ComputerGroups | Where-Object { $computer_groups -notcontains $_ })
            $groups_to_add = @($computer_groups | Where-Object { $cap.ComputerGroups -notcontains $_ })

            $computer_groups_diff = $null
            foreach($group in $groups_to_add) {
                if (-not $check_mode) {
                    $return = $wmi_cap | Invoke-CimMethod -MethodName AddComputerGroupNames -Arguments @{ ComputerGroupNames = $group }
                    if ($return.ReturnValue -ne 0) {
                        Fail-Json -obj $result -message "Failed to add computer group $($group) (code: $($return.ReturnValue))"
                    }
                }
                $computer_groups_diff += "  +$group`n"
                $result.changed = $true
            }

            foreach($group in $groups_to_remove) {
                if (-not $check_mode) {
                    $return = $wmi_cap | Invoke-CimMethod -MethodName RemoveComputerGroupNames -Arguments @{ ComputerGroupNames = $group }
                    if ($return.ReturnValue -ne 0) {
                        Fail-Json -obj $result -message "Failed to remove computer group $($group) (code: $($return.ReturnValue))"
                    }
                }
                $computer_groups_diff += "  -$group`n"
                $result.changed = $true
            }

            if($computer_groups_diff) {
                $diff_text += "~ComputerGroups`n$computer_groups_diff"
            }
        }
    }
}

if ($diff_mode -and $result.changed -eq $true) {
    $result.diff = @{
        prepared = $diff_text
    }
}

Exit-Json $result
