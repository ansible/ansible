#!powershell
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Daniele Lazzari  <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
$result = @{
    'changed' = $False;
    'output'  = $null
}

Function Test-SQLUser {
    Param(
        [string]$LoginName,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [securestring]$ServerInstancePassword
    )
    try {
        if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
            $exists = Invoke-SQLCmd -ServerInstance $ServerInstance -Query "SELECT name FROM syslogins WHERE name = '$LoginName'"
        }
        else {
            $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
            $exists = Invoke-SQLCmd -ServerInstance $ServerInstance -Query "SELECT name FROM syslogins WHERE name = '$LoginName'" -Credential $SQLCredentials
        }
    }   
    catch {
        Fail-Json -obj $result -message $($_.exception.message)
    }

    if ($exists) {
        return $true
    }

    return $false
}

Function Add-SQLLogin {

    Param (
        [string]$LoginName,
        [string]$Password,
        [string]$LoginType,
        [string]$DefaultDatabase,
        [string]$DefaultLanguage,
        [bool]$CheckExpiration,
        [bool]$CheckPolicy,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [securestring]$ServerInstancePassword,
        [bool]$CheckMode
    )

    $Expiration = 'CHECK_EXPIRATION=OFF'
    $Policy = 'CHECK_POLICY=OFF'

    if ($CheckExpiration) {
        $Expiration = 'CHECK_EXPIRATION=ON'
    }
    if ($CheckPolicy) {
        $Policy = 'CHECK_POLICY=ON'
    }

    if ($LoginType -eq 'sql') {
        $QUERY = "CREATE LOGIN $LoginName WITH PASSWORD=N'$Password', DEFAULT_DATABASE=$DefaultDatabase, DEFAULT_LANGUAGE=$DefaultLanguage, $Expiration, $Policy"
    }
    else {
        if ($LoginName -match "\\") {
            $LoginName = $LoginName.Replace("\\", "\")
        }
        $QUERY = "CREATE LOGIN `"$LoginName`" FROM WINDOWS WITH DEFAULT_DATABASE=$DefaultDatabase, DEFAULT_LANGUAGE=$DefaultLanguage"
    }
    
    $exists = Test-SQLUser -LoginName $LoginName `
        -ServerInstance $ServerInstance `
        -ServerInstanceUser $ServerInstanceUser `
        -ServerInstancePassword $ServerInstancePassword
    
    if (!($exists)) {
        try {
            if (!($CheckMode)) {
                if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
                    Invoke-SQLCmd -ServerInstance $ServerInstance -Query $QUERY
                }
                else {
                    $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
                    Invoke-SQLCmd -ServerInstance $ServerInstance -Query $QUERY -Credential $SQLCredentials
                }
            }
            $result.output = "login $LoginName created"
            $result.changed = $true
        }
        catch {
            Fail-Json -obj $result -message $($_.exception.message)
        }
    }
    else {
        $result.output = "login $LoginName alerady exists"
    }
    Exit-Json $result
}

Function Remove-SQLLogin {
    Param(
        [Parameter(Mandatory = $true)]
        [string]$LoginName,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [securestring]$ServerInstancePassword,
        [bool]$CheckMode
    )
    
    $exists = Test-SQLUser -LoginName $LoginName `
        -Password $Password `
        -ServerInstance $ServerInstance `
        -ServerInstanceUser $ServerInstanceUser `
        -ServerInstancePassword $ServerInstancePassword
    
    if ($exists) {
        $QUERY = "DROP LOGIN `"$LoginName`"" 
        try {
            if (!($CheckMode)) {
                if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
                    Invoke-SQLCmd -ServerInstance $ServerInstance -Query $QUERY 
                }
                else {
                    $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
                    Invoke-SQLCmd -ServerInstance $ServerInstance -Query $QUERY -Credential $SQLCredentials
                }
            }
            $result.output = "loign $LoginName removed"
            $result.changed = $true
        }
        catch {
            Fail-Json -obj $result -message $($_.exception.message)
        }
    }
    else {
        $result.output = "login $LoginName does not exist"
    }
    Exit-Json $result
}

$params = Parse-Args $args -supports_check_mode $true

$loginName = Get-AnsibleParam -obj $params -name "login_name" -type "str" -failifempty $true
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$defaultDb = Get-AnsibleParam -obj $params -name "default_database" -type "str" -default "master"
$defaultLanguage = Get-AnsibleParam -obj $params -name "default_language" -type "str" -default "us_english"
$checkExpiration = Get-AnsibleParam -obj $params -name "check_expiration" -type "bool" -default $true
$checkPolicy = Get-AnsibleParam -obj $params -name "check_policy" -type "bool" -default $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$serverInstance = Get-AnsibleParam -obj $params -name "server_instance" -type "str" -default $env:COMPUTERNAME
$serverInstanceUser = Get-AnsibleParam -obj $params -name "server_instance_user" -type "str" -default $null
$serverInstancePassword = Get-AnsibleParam -obj $params -name "server_instance_password" -type "str" -default $null
$loginType = Get-AnsibleParam -obj $params -name "login_type" -type "str" -default "sql" -validateset "sql", "windows"
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false


if ($serverInstancePassword) {
    $serverInstancePassword = ConvertTo-SecureString $serverInstancePassword -AsPlainText -Force
}

if ($state -eq "present") {
    Add-SQLLogin -LoginName $loginName `
        -Password $password `
        -LoginType $loginType `
        -DefaultDatabase $defaultDb `
        -DefaultLanguage $defaultLanguage `
        -CheckExpiration $checkExpiration `
        -CheckPolicy $checkPolicy `
        -ServerInstance $serverInstance `
        -ServerInstanceUser $serverInstanceUser `
        -ServerInstancePassword $serverInstancePassword `
        -CheckMode $check_mode
}

if ($state -eq "absent")  {
    Remove-SQLLogin -LoginName $loginName `
        -ServerInstance $serverInstance `
        -ServerInstanceUser $serverInstanceUser `
        -ServerInstancePassword $serverInstancePassword `
        -CheckMode $check_mode
}