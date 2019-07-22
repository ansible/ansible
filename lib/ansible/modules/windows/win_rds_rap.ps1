#!powershell

# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

# List of authentication methods as string. Used for parameter validation and conversion to integer flag, so order is important!
$computer_group_types = @("rdg_group", "ad_network_resource_group", "allow_any")
$computer_group_types_wmi = @{rdg_group = "RG"; ad_network_resource_group = "CG"; allow_any = "ALL"}

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present","enabled","disabled"
$computer_group_type = Get-AnsibleParam -obj $params -name "computer_group_type" -type "str" -validateset $computer_group_types
$computer_group = Get-AnsibleParam -obj $params -name "computer_group" -type "str" -failifempty ($computer_group_type -eq "ad_network_resource_group" -or $computer_group_type -eq "rdg_group")
$user_groups = Get-AnsibleParam -obj $params -name "user_groups" -type "list"
$allowed_ports = Get-AnsibleParam -obj $params -name "allowed_ports" -type "list"


function Get-RAP([string] $name) {
    $rap_path = "RDS:\GatewayServer\RAP\$name"
    $rap = @{
        Name = $name
    }

    # Fetch RAP properties
    Get-ChildItem -Path $rap_path | ForEach-Object { $rap.Add($_.Name,$_.CurrentValue) }
    # Convert boolean values
    $rap.Enabled = $rap.Status -eq 1
    $rap.Remove("Status")

    # Convert computer group name from UPN to Down-Level Logon format
    if($rap.ComputerGroupType -ne 2) {
        $rap.ComputerGroup = Convert-FromSID -sid (Convert-ToSID -account_name $rap.ComputerGroup)
    }

    # Convert multiple choices values
    $rap.ComputerGroupType = $computer_group_types[$rap.ComputerGroupType]

    # Convert allowed ports from string to list
    if($rap.PortNumbers -eq '*') {
        $rap.PortNumbers = @("any")
    } else {
        $rap.PortNumbers = @($rap.PortNumbers -split ',')
    }

    # Fetch RAP user groups in Down-Level Logon format
    $rap.UserGroups = @(
        Get-ChildItem -Path "$rap_path\UserGroups" | 
            Select-Object -ExpandProperty Name |
            ForEach-Object { Convert-FromSID -sid (Convert-ToSID -account_name $_) }
    )

    return $rap
}

function Set-RAPPropertyValue {
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

    $rap_path = "RDS:\GatewayServer\RAP\$name"

    try {
        Set-Item -Path "$rap_path\$property" -Value $value -ErrorAction stop
    } catch {
        Fail-Json -obj $resultobj -message "Failed to set property $property of RAP ${name}: $($_.Exception.Message)"
    }
}

$result = @{
  changed = $false
}
$diff_text = $null

# Validate RAP name
if ($name -match "[*/\\;:?`"<>|\t]+") {
    Fail-Json -obj $result -message "Invalid character in RAP name."
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
            Fail-Json -obj $result -message "$group is not a valid user group on the host machine or domain."
        }

        # Return the normalized group name in Down-Level Logon format
        Convert-FromSID -sid $sid
    }
    $user_groups = @($user_groups)
}

# Validate computer group parameter
if ($computer_group_type -eq "allow_any" -and $null -ne $computer_group) {
    Add-Warning -obj $result -message "Parameter 'computer_group' ignored because the computer_group_type is set to allow_any."
} elseif ($computer_group_type -eq "rdg_group" -and -not (Test-Path -Path "RDS:\GatewayServer\GatewayManagedComputerGroups\$computer_group")) {
    Fail-Json -obj $result -message "$computer_group is not a valid gateway managed computer group"
} elseif ($computer_group_type -eq "ad_network_resource_group") {
    $sid = Convert-ToSID -account_name $computer_group
    if (!$sid) {
        Fail-Json -obj $result -message "$computer_group is not a valid computer group on the host machine or domain."
    }
    # Ensure the group name is in Down-Level Logon format
    $computer_group = Convert-FromSID -sid $sid
}

# Validate port numbers
if ($null -ne $allowed_ports) {
    foreach ($port in $allowed_ports) {
        if (-not ($port -eq "any" -or ($port -is [int] -and $port -ge 1 -and $port -le 65535))) {
            Fail-Json -obj $result -message "$port is not a valid port number."
        }
    }
}

# Ensure RemoteDesktopServices module is loaded
if ($null -eq (Get-Module -Name RemoteDesktopServices -ErrorAction SilentlyContinue)) {
    Import-Module -Name RemoteDesktopServices
}

# Check if a RAP with the given name already exists
$rap_exist = Test-Path -Path "RDS:\GatewayServer\RAP\$name"

if ($state -eq 'absent') {
    if ($rap_exist) {
        Remove-Item -Path "RDS:\GatewayServer\RAP\$name" -Recurse -WhatIf:$check_mode
        $diff_text += "-[$name]"
        $result.changed = $true
    }
} else {
    $diff_text_added_prefix = ''
    if (-not $rap_exist) {
        if ($null -eq $user_groups) {
            Fail-Json -obj $result -message "User groups must be defined to create a new RAP."
        }

        # Computer group type is required when creating a new RAP. Set it to allow connect to any resource by default.
        if ($null -eq $computer_group_type) {
            $computer_group_type = "allow_any"
        }

        # Create a new RAP
        if (-not $check_mode) {
            $RapArgs = @{
                Name = $name
                ResourceGroupType = 'ALL'
                UserGroupNames = $user_groups -join ';'
                ProtocolNames = 'RDP'
                PortNumbers = '*'
            }
            $return = Invoke-CimMethod -Namespace Root\CIMV2\TerminalServices -ClassName Win32_TSGatewayResourceAuthorizationPolicy -MethodName Create -Arguments $RapArgs
            if ($return.ReturnValue -ne 0) {
                Fail-Json -obj $result -message "Failed to create RAP $name (code: $($return.ReturnValue))"
            }
        }
        $rap_exist = -not $check_mode

        $diff_text_added_prefix = '+'
        $result.changed = $true
    }

    $diff_text += "$diff_text_added_prefix[$name]`n"

    # We cannot configure a RAP that was created above in check mode as it won't actually exist
    if($rap_exist) {
        $rap = Get-RAP -Name $name
        $wmi_rap = Get-CimInstance -ClassName Win32_TSGatewayResourceAuthorizationPolicy -Namespace Root\CIMv2\TerminalServices -Filter "name='$($name)'"

        if ($state -in @('disabled', 'enabled')) {
            $rap_enabled = $state -ne 'disabled'
            if ($rap.Enabled -ne $rap_enabled) {
                $diff_text += "-State = $(@('disabled', 'enabled')[[int]$rap.Enabled])`n+State = $state`n"
                Set-RAPPropertyValue -Name $name -Property Status -Value ([int]$rap_enabled) -ResultObj $result -WhatIf:$check_mode
                $result.changed = $true
            }
        }

        if ($null -ne $description -and $description -ne $rap.Description) {
            Set-RAPPropertyValue -Name $name -Property Description -Value $description -ResultObj $result -WhatIf:$check_mode
            $diff_text += "-Description = $($rap.Description)`n+Description = $description`n"
            $result.changed = $true
        }

        if ($null -ne $allowed_ports -and @(Compare-Object $rap.PortNumbers $allowed_ports -SyncWindow 0).Count -ne 0) {
            $diff_text += "-AllowedPorts = [$($rap.PortNumbers -join ',')]`n+AllowedPorts = [$($allowed_ports -join ',')]`n"
            if ($allowed_ports -contains 'any') { $allowed_ports = '*' }
            Set-RAPPropertyValue -Name $name -Property PortNumbers -Value $allowed_ports -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $computer_group_type -and $computer_group_type -ne $rap.ComputerGroupType) {
            $diff_text += "-ComputerGroupType = $($rap.ComputerGroupType)`n+ComputerGroupType = $computer_group_type`n"
            if ($computer_group_type -ne "allow_any") {
                $diff_text += "+ComputerGroup = $computer_group`n"
            }
            $return = $wmi_rap | Invoke-CimMethod -MethodName SetResourceGroup -Arguments @{
                ResourceGroupName = $computer_group
                ResourceGroupType = $computer_group_types_wmi.$($computer_group_type)
            }
            if ($return.ReturnValue -ne 0) {
                Fail-Json -obj $result -message "Failed to set computer group type to $($computer_group_type) (code: $($return.ReturnValue))"
            }

            $result.changed = $true

        } elseif ($null -ne $computer_group -and $computer_group -ne $rap.ComputerGroup) {
            $diff_text += "-ComputerGroup = $($rap.ComputerGroup)`n+ComputerGroup = $computer_group`n"
            $return = $wmi_rap | Invoke-CimMethod -MethodName SetResourceGroup -Arguments @{
                ResourceGroupName = $computer_group
                ResourceGroupType = $computer_group_types_wmi.$($rap.ComputerGroupType)
            }
            if ($return.ReturnValue -ne 0) {
                Fail-Json -obj $result -message "Failed to set computer group name to $($computer_group) (code: $($return.ReturnValue))"
            }
            $result.changed = $true
        }

        if ($null -ne $user_groups) {
            $groups_to_remove = @($rap.UserGroups | Where-Object { $user_groups -notcontains $_ })
            $groups_to_add = @($user_groups | Where-Object { $rap.UserGroups -notcontains $_ })

            $user_groups_diff = $null
            foreach($group in $groups_to_add) {
                if (-not $check_mode) {
                    $return = $wmi_rap | Invoke-CimMethod -MethodName AddUserGroupNames -Arguments @{ UserGroupNames = $group }
                    if ($return.ReturnValue -ne 0) {
                        Fail-Json -obj $result -message "Failed to add user group $($group) (code: $($return.ReturnValue))"
                    }
                }
                $user_groups_diff += "  +$group`n"
                $result.changed = $true
            }

            foreach($group in $groups_to_remove) {
                if (-not $check_mode) {
                    $return = $wmi_rap | Invoke-CimMethod -MethodName RemoveUserGroupNames -Arguments @{ UserGroupNames = $group }
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
    }
}

if ($diff_mode -and $result.changed -eq $true) {
    $result.diff = @{
        prepared = $diff_text
    }
}

Exit-Json $result
