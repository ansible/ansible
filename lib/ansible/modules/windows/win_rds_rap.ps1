#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

# List of authentication methods as string. Used for parameter validation and conversion to integer flag, so order is important!
$computer_group_types = @("rdg_group", "ad_network_resource_group", "allow_any")

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
# TODO Support diff mode ?
#$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

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
    Get-ChildItem -Path "$rap_path" | foreach { $rap.Add($_.Name,$_.CurrentValue) }
    # Convert boolean values
    $rap.Enabled = $rap.Status -eq 1
    $rap.Remove("Status")

    # Convert multiple choices values
    $rap.ComputerGroupType = $computer_group_types[$rap.ComputerGroupType]

    # Convert allowed ports from string to list
    if($rap.PortNumbers -eq '*') {
        $rap.PortNumbers = @("any")
    } else {
        $rap.PortNumbers = @($rap.PortNumbers -split ',')
    }

    # Fetch RAP user groups
    $rap.UserGroups = @(Get-ChildItem -Path "$rap_path\UserGroups" | Select -ExpandProperty Name)

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

# Validate RAP name
if ($name -match "[*/\\;:?`"<>|\t]+") {
    Fail-Json -obj $result -message "Invalid character in RAP name."
}

# Validate user groups
if ($null -ne $user_groups) {
    if ($user_groups.Count -lt 1) {
        Fail-Json -obj $result -message "Parameter 'user_groups' cannot be an empty list."
    }

    $user_groups = $user_groups | foreach {
        $group = $_
        # Test that the group is resolvable on the local machine
        $sid = Convert-ToSID -account_name $group
        if (!$sid) {
            Fail-Json -obj $result -message "$group is not a valid user group on the host machine or domain"
        }

        # Return the normalized group name in UPN format
        $group_name = Convert-FromSID -sid $sid
        ($group_name -split "\\")[1..0] -join "@"
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
        Fail-Json -obj $result -message "$computer_group is not a valid computer group on the host machine or domain"
    }
    # Ensure the group name is in UPN format
    $computer_group = Convert-FromSID -sid $sid
    $computer_group = ($computer_group -split "\\")[1..0] -join "@"
}

# Validate port numbers
if ($null -ne $allowed_ports) {
    foreach ($port in $allowed_ports) {
        if ($port -notmatch "^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]|any)$") {
            Fail-Json -obj $result -message "$port is not a valid port number."
        }
    }
}

# Ensure RemoteDesktopServices module is loaded
if ((Get-Module -Name RemoteDesktopServices -ErrorAction SilentlyContinue) -eq $null) {
    Import-Module -Name RemoteDesktopServices
}

# Check if a RAP with the given name already exists
$rap_exist = Test-Path -Path "RDS:\GatewayServer\RAP\$name"

if ($state -eq 'absent') {
    if ($rap_exist) {
        Remove-Item -Path "RDS:\GatewayServer\RAP\$name" -Recurse -WhatIf:$check_mode
        $result.changed = $true
    }
} else {
    if (-not $rap_exist) {
        if ($null -eq $user_groups) {
            Fail-Json -obj $result -message "User groups must be defined to create a new RAP."
        }

        # Computer group type is required when creating a new RAP. Set it to allow connect to any resource by default.
        if ($null -eq $computer_group_type) {
            $computer_group_type = "allow_any"
        }

        # Create a new RAP
        New-Item -Path "RDS:\GatewayServer\RAP" -Name $name -UserGroups $user_groups -ComputerGroupType ([array]::IndexOf($computer_group_types, $computer_group_type)) -WhatIf:$check_mode
        $rap_exist = -not $check_mode
        $result.changed = $true
    }

    # we cannot configure a RAP that was created above in check mode as it
    # won't actually exist
    if($rap_exist) {
        $rap = Get-RAP -Name $name

        if ($state -in @('enabled', 'disabled')) {
            $rap_enabled = $state -ne 'disabled'
            if ($rap.Enabled -ne $rap_enabled) {
                Set-RAPPropertyValue -Name $name -Property Status -Value ([int]$rap_enabled) -ResultObj $result -WhatIf:$check_mode
                $result.changed = $true
            }
        }

        if ($null -ne $description -and $description -ne $rap.Description) {
            Set-RAPPropertyValue -Name $name -Property Description -Value $description -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $allowed_ports -and @(Compare-Object $rap.PortNumbers $allowed_ports -SyncWindow 0).Count -ne 0) {
            if ($allowed_ports -contains 'any') { $allowed_ports = '*' }
            Set-RAPPropertyValue -Name $name -Property PortNumbers -Value $allowed_ports -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $computer_group_type -and $computer_group_type -ne $rap.ComputerGroupType) {
            if ($computer_group_type -eq "allow_any") {
                Set-RAPPropertyValue -Name $name -Property ComputerGroupType -Value ([array]::IndexOf($computer_group_types, $computer_group_type)) -ResultObj $result -WhatIf:$check_mode
            } else {
                try {
                    Set-Item -Path "RDS:\GatewayServer\RAP\$name\ComputerGroupType" `
                        -Value ([array]::IndexOf($computer_group_types, $computer_group_type)) `
                        -ComputerGroup $computer_group `
                        -ErrorAction Stop `
                        -WhatIf:$check_mode
                } catch {
                    Fail-Json -obj $resultobj -message "Failed to set property ComputerGroupType of RAP ${name}: $($_.Exception.Message)"
                }
            }

            $result.changed = $true

        } elseif ($null -ne $computer_group -and $computer_group -ne $rap.ComputerGroup) {
            Set-RAPPropertyValue -Name $name -Property ComputerGroup -Value $computer_group -ResultObj $result -WhatIf:$check_mode
            $result.changed = $true
        }

        if ($null -ne $user_groups) {
            $groups_to_remove = @($rap.UserGroups | where { $user_groups -notcontains $_ })
            $groups_to_add = @($user_groups | where { $rap.UserGroups -notcontains $_ })

            foreach($group in $groups_to_add) {
                New-Item -Path "RDS:\GatewayServer\RAP\$name\UserGroups" -Name $group -WhatIf:$check_mode
                $result.changed = $true
            }

            foreach($group in $groups_to_remove) {
                Remove-Item -Path "RDS:\GatewayServer\RAP\$name\UserGroups\$group" -WhatIf:$check_mode
                $result.changed = $true
            }
        }

        # ASK Should we return the full RAP object?
        # $result.rap = Get-RAP -Name $name
    }
}

Exit-Json $result