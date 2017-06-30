#!powershell
# This file is part of Ansible
#
# Copyright 2017, Jordan Borean <jborean93@gmail.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$users = Get-AnsibleParam -obj $params -name "users" -type "list" -failifempty $true
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -default "set" -validateset "add","remove","set"

$result = @{
    changed = $false
    added = @()
    removed = @()
}

Function Get-Username($sid) {
    # converts the SID (if it is one) to a username
    # this sid is in the form exported by the SecEdit ini file (*S-.-..)
    if (-not $sid.StartsWith("*S-")) {
        $sid = Get-SID -account_name $sid
    } else {
        $sid = $sid.substring(1)
    }

    $object = New-Object System.Security.Principal.SecurityIdentifier($sid)
    $user = $object.Translate([System.Security.Principal.NTAccount])
    $user.Value
}

Function Get-SID($account_name) {
    # Can take in the following account name forms and convert to a SID
    # UPN:
    #   username@domain (Domain)
    # Down-Level Login Name
    #   domain\username (Domain)
    #   computername\username (Local)
    #   .\username (Local)
    # Login Name
    #   username (Local)

    if ($account_name -like "*\*") {
        $account_name_split = $account_name -split "\\"
        if ($account_name_split[0] -eq ".") {
            $domain = $env:COMPUTERNAME
        } else {
            $domain = $account_name_split[0]
        }
        $username = $account_name_split[1]
    } elseif ($account_name -like "*@*") {
        $account_name_split = $account_name -split "@"
        $domain = $account_name_split[1]
        $username = $account_name_split[0]
    } else {
        $domain = $null
        $username = $account_name
    }

    if ($domain) {
        # searching for a local group with the servername prefixed will fail,
        # need to check for this situation and only use NTAccount(String)
        if ($domain -eq $env:COMPUTERNAME) {
            $adsi = [ADSI]("WinNT://$env:COMPUTERNAME,computer")
            $group = $adsi.psbase.children | Where-Object { $_.schemaClassName -eq "group" } | Where-Object { $_.Name -eq $username }
        } else {
            $group = $null
        }
        if ($group) {
            $account = New-Object System.Security.Principal.NTAccount($username)
        } else {
            $account = New-Object System.Security.Principal.NTAccount($domain, $username)
        }
    } else {
        # when in a domain NTAccount(String) will favour domain lookups check
        # if username is a local user and explictly search on the localhost for
        # that account
        $adsi = [ADSI]("WinNT://$env:COMPUTERNAME,computer")
        $user = $adsi.psbase.children | Where-Object { $_.schemaClassName -eq "user" } | Where-Object { $_.Name -eq $username }
        if ($user) {
            $account = New-Object System.Security.Principal.NTAccount($env:COMPUTERNAME, $username)
        } else {
            $account = New-Object System.Security.Principal.NTAccount($username)
        }
    }
    
    try {
        $account_sid = $account.Translate([System.Security.Principal.SecurityIdentifier])
    } catch {
        Fail-Json $result "Account Name: $account_name is not a valid account, cannot get SID: $($_.Exception.Message)"
    }
    
    $account_sid.Value
}

Function Run-SecEdit($arguments) {
    $rc = $null
    $stdout = $null
    $stderr = $null
    $log_path = [IO.Path]::GetTempFileName()
    $arguments = $arguments + @("/log", $log_path, "/areas", "USER_RIGHTS")

    try {
        $stdout = &SecEdit.exe $arguments | Out-String
    } catch {
        $stderr = $_.Exception.Message
    }
    $log = Get-Content -Path $log_path
    Remove-Item -Path $log_path -Force

    $return = @{
        log = ($log -join "`n").Trim()
        stdout = $stdout
        stderr = $stderr
        rc = $LASTEXITCODE
    }

    $return
}

Function Compare-List($existing_list, $new_list) {
    $comparison = @{
        mismatch = $false
        added = @()
        removed = @()
    }

    foreach ($entry in $existing_list) {
        if ($new_list -notcontains $entry) {
            $comparison.removed += Get-Username -sid $entry
            $comparison.mismatch = $true
        }
    }
    foreach ($entry in $new_list) {
        if ($existing_list -notcontains $entry) {
            $comparison.added += Get-Username -sid $entry
            $comparison.mismatch = $true
        }
    }

    $comparison
}

Function Build-NewUserList($action, $users, $existing_users) {
    $new_users = @()
    if ($action -eq "remove") {
        foreach ($existing_user in $existing_users) {
            $user_match = $true
            foreach ($user in $users) {
                $user_sid = Get-SID -account_name $user
                if ($existing_user -eq "*$user_sid") {
                    $user_match = $false
                }
            }

            if ($user_match) {
                $new_users += $existing_user
            }
        }
    } elseif ($action -eq "add") {
        $new_users = $existing_users
        foreach ($user in $users) {
            $user_sid = Get-SID -account_name $user
            $new_users += "*$user_sid"
        }
    } else {
        foreach ($user in $users) {
            $user_sid = Get-SID -account_name $user
            $new_users += "*$user_sid"
        }
    }

    ,$new_users
}

Function Build-ExistingUserList($existing_users) {
    $users = @()
    foreach ($existing_user in ($existing_users -split ",")) {
        if ($existing_user.StartsWith("*S")) {
            $users += $existing_user
        } else {
            $user_sid = Get-SID -account_name $existing_user
            $users += "*$user_sid"
        }
    }

    ,$users
}

Function ConvertTo-Ini($ini) {
    $content = @()
    foreach ($key in $ini.GetEnumerator()) {
        $section = $key.Name
        $values = $key.Value

        $content += "[$section]"
        foreach ($value in $values.GetEnumerator()) {
            $value_key = $value.Name
            $value_value = $value.Value

            if ($value_value -ne $null) {
                $content += "$value_key = $value_value"
            }
        }
    }

    $content -join "`r`n"
}

Function ConvertFrom-Ini($file_path) {
    $ini = @{}
    $contents = Get-Content -Path $file_path -Encoding Unicode
    foreach ($line in $contents) {
        switch -Regex ($line) {
            "^\[(.+)\]" {
                $section = $matches[1]
                $ini.$section = @{}
            }
            "(.+?)\s*=(.*)" {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                $ini.$section.$name = $value
            }
        }
    }

    $ini
}

### Main code below ###

$ini_right_key = "Privilege Rights"
$secedit_ini_path = [IO.Path]::GetTempFileName()
# while this will technically make a change to the system in check mode by
# creating a new file, we need these values to be able to do anything
# substantial in check mode
$export_result = Run-SecEdit -arguments @("/export", "/cfg", $secedit_ini_path, "/quiet")

# check the return code and if the file has been populated, otherwise error out
if (($export_result.rc -ne 0) -or ((Get-Item -Path $secedit_ini_path).Length -eq 0)) {
    Remove-Item -Path $secedit_ini_path
    Fail-Json $result "Failed to export secedit.ini file to $($secedit_ini_path).`nRC: $($export_result.rc)`nSTDOUT: $($export_result.stdout)`nSTDERR: $($export_result.stderr)`nLOG: $($export_result.log)"
}
$secedit_ini = ConvertFrom-Ini -file_path $secedit_ini_path
Remove-Item -Path $secedit_ini_path

$will_change = $false
if ($secedit_ini.$ini_right_key.ContainsKey($name)) {
    $existing_users = Build-ExistingUserList -existing_users $secedit_ini.$ini_right_key.$name
    $new_users = Build-NewUserList -action $action -users $users -existing_users $existing_users

    # sort the user objects for later comparison and remove duplicates
    $new_users = $new_users | Sort-Object -Unique
    $existing_users = $existing_users | Sort-Object -Unique

    # compare the list and make changes as necessary
    if ($new_users.Length -eq 0) {
        $will_change = $true
        $secedit_ini.$ini_right_key.$name = $null
    }

    $comparison = Compare-List -existing_list $existing_users -new_list $new_users
    if ($comparison.mismatch -eq $true) {
        foreach ($added in $comparison.added) {
            $result.added += $added
        }
        foreach ($removed in $comparison.removed) {
            $result.removed += $removed
        }
        $will_change = $true
        $secedit_ini.$ini_right_key.$name = $new_users -join ","
    }
} else {
    if ($users.Length -gt 0 -and (@("add", "set") -contains $action)) {
        $will_change = $true
        $new_users = @()
        foreach ($user in $users) {
            $username = Get-Username -sid $user
            $result.added += $username
            $new_users += "*$(Get-SID -account_name $user)"
        }
        $secedit_ini.$ini_right_key.$name = $new_users -join ","
    }
}

if ($will_change) {
    $ini_contents = ConvertTo-Ini -ini $secedit_ini
    Set-Content -Path $secedit_ini_path -Value $ini_contents -Encoding Unicode -WhatIf:$check_mode
    $result.changed = $true

    if (-not $check_mode) {
        $secedit_db_path = [IO.Path]::GetTempFileName()
        Remove-Item -Path $secedit_db_path -Force # needs to be deleted for SecEdit.exe /import to work

        $import_result = Run-SecEdit -arguments @("/configure", "/db", $secedit_db_path, "/cfg", $secedit_ini_path, "/quiet")
        $result.changed = $true
        $result.import_log = $import_result.log
        Remove-Item -Path $secedit_ini_path -Force
        if ($import_result.rc -ne 0) {
            Fail-Json $result "Failed to import secedit.ini file from $($secedit_ini_path).`nRC: $($import_result.rc)`nSTDOUT: $($import_result.stdout)`nSTDERR: $($import_result.stderr)`nLOG: $($import_result.log)"
        }

        # secedit doesn't error out on improper entries, re-export and verify
        # the changes occurred
        $export_result = Run-SecEdit -arguments @("/export", "/cfg", $secedit_ini_path, "/quiet")

        # check the return code and if the file has been populated, otherwise error out
        if (($export_result.rc -ne 0) -or ((Get-Item -Path $secedit_ini_path).Length -eq 0)) {
            Remove-Item -Path $secedit_ini_path # file is empty and we don't need it
            Fail-Json $result "Failed to export secedit.ini file to $($secedit_ini_path).`nRC: $($export_result.rc)`nSTDOUT: $($export_result.stdout)`nSTDERR: $($export_result.stderr)`nLOG: $($export_result.log)"
        }
        $secedit_ini = ConvertFrom-Ini -file_path $secedit_ini_path
        Remove-Item -Path $secedit_ini_path

        if ($secedit_ini.$ini_right_key.ContainsKey($name)) {
            $existing_users = Build-ExistingUserList -existing_users $secedit_ini.$ini_right_key.$name
            $new_users = Build-NewUserList -action $action -users $users -existing_users $existing_users

            # sort the user objects for later comparison and remove duplicates
            $new_users = $new_users | Sort-Object -Unique
            $existing_users = $existing_users | Sort-Object -Unique

            $comparison = Compare-List -existing_list $existing_users -new_list $new_users
            if ($comparison.mismatch -eq $true) {
                Fail-Json $result "Failed to modify right $name, right membership does not match expected membership"
            }
        } else {
            if ($users.Length -gt 0 -and (@("add", "set") -contains $action)) {
                Fail-Json $result "Failed to modify right $name, right entry did not exist after import"
            }
        }
    }
}

Exit-Json $result
