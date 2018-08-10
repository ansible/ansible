#!powershell
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Daniele Lazzari  <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
$result = @{
    'changed' = $False;
}

Function Test-SQLServerRole {
    Param (
        [string]$LogiName,
        [string]$ServerRole,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [Security.SecureString]$ServerInstancePassword
    )

    $QUERY = "SELECT IS_SRVROLEMEMBER ( N'$ServerRole', '$LogiName' ) AS role"
    try {
        if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
            $HasRole = Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY
        }
        else {
            $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
            $HasRole = Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY -Credential $SQLCredentials
        }
    }
    catch {
        Fail-Json -obj $result -message $($_.exception.message)
    }
    
    if ($HasRole.role -eq 1) {
        return $true
    }
    return $false
}

Function Add-LoginServerRole {
    Param (
        [string]$LogiName,
        [string]$ServerRole,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [Security.SecureString]$ServerInstancePassword,
        [bool]$CheckMode
    )

    $HasRole = Test-SQLServerRole -LogiName $LoginName `
        -ServerRole $ServerRole `
        -ServerInstance $ServerInstance `
        -ServerInstanceUser $ServerInstanceUser `
        -ServerInstancePassword $ServerInstancePassword

    if ($HasRole) {
        $result.role = $ServerRole
        $result.output = "role already present"
    }
    else {
        $QUERY = "sp_addsrvrolemember @loginame= N'$LoginName', @rolename=N'$ServerRole'"
        try {
            if (!($CheckMode)) {
                if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
                    Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY
                }
                else {
                    $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
                    Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY -Credential $SQLCredentials
                }
            }
        }
        catch {
            Fail-Json -obj $result -message $($_.exception.message)
        }
        $result.output = "role added"
        $result.role = $ServerRole
        $result.changed = $true
    }   

    Exit-Json $result
}

Function Remove-LoginServerRole {
    Param (
        [string]$LogiName,
        [string]$ServerRole,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [Security.SecureString]$ServerInstancePassword,
        [bool]$CheckMode
    )

    $HasRole = Test-SQLServerRole -LogiName $LoginName `
        -ServerRole $ServerRole `
        -ServerInstance $ServerInstance `
        -ServerInstanceUser $ServerInstanceUser `
        -ServerInstancePassword $ServerInstancePassword
    
    if (!($HasRole)) {
        $result.role = $ServerRole
        $result.output = "no role to remove"
    }
    else {
        $QUERY = "sp_dropsrvrolemember @loginame= N'$LoginName', @rolename=N'$ServerRole'"
        try {
            if (!($CheckMode)) {
                if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
                    Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY
                }
                else {
                    $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
                    Invoke-SqlCmd -ServerInstance $ServerInstance -Query $QUERY -Credential $SQLCredentials
                }
            }
        }
        catch {
            Fail-Json -obj $result -message $($_.exception.message)
        }
        $result.output = "role removed"
        $result.role = $ServerRole
        $result.changed = $true
    }

    Exit-Json $result
}

$params = Parse-Args $args -supports_check_mode $true

$loginName = Get-AnsibleParam -obj $params -name "login_name" -type "str" -failifempty $true
$serverRole = Get-AnsibleParam -obj $params -name "server_role" -type "list" -failifempty $true
$serverInstance = Get-AnsibleParam -obj $params -name "server_instance" -type "str" -default $env:COMPUTERNAME
$serverInstanceUser = Get-AnsibleParam -obj $params -name "server_instance_user" -type "str" -default $null
$serverInstancePassword = Get-AnsibleParam -obj $params -name "server_instance_password" -type "str" -default $null
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"

if ($serverInstancePassword) {
    $serverInstancePassword = ConvertTo-SecureString $serverInstancePassword -AsPlainText -Force
}

if ($state -eq "present") {
    Add-LoginServerRole -LogiName $loginName `
        -ServerRole $serverRole `
        -ServerInstance $serverInstance `
        -ServerInstanceUser $serverInstanceUser `
        -ServerInstancePassword $serverInstancePassword `
        -CheckMode $check_mode
}
else {
    Remove-LoginServerRole -LogiName $loginName `
        -ServerRole $serverRole `
        -ServerInstance $serverInstance `
        -ServerInstanceUser $serverInstanceUser `
        -ServerInstancePassword $serverInstancePassword `
        -CheckMode $check_mode
}