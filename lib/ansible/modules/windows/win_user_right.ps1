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
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$users = Get-AnsibleParam -obj $params -name "users" -type "list" -failifempty $true
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -default "set" -validateset "add","remove","set"

$result = @{
    changed = $false
    added = @()
    removed = @()
}

if ($diff_mode) {
    $result.diff = @{}
}

Function Get-Username($sid) {
    # converts the SID (if it is one) to a username
    # this sid is in the form exported by the SecEdit ini file (*S-.-..)

    $sid = $sid.substring(1)
    $object = New-Object System.Security.Principal.SecurityIdentifier($sid)
    $user = $object.Translate([System.Security.Principal.NTAccount])
    return $user.Value
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
    
    return $account_sid.Value
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

    return $return
}

Function Export-SecEdit() {
    $secedit_ini_path = [IO.Path]::GetTempFileName()
    # while this will technically make a change to the system in check mode by
    # creating a new file, we need these values to be able to do anything
    # substantial in check mode
    $export_result = Run-SecEdit -arguments @("/export", "/cfg", $secedit_ini_path, "/quiet")

    # check the return code and if the file has been populated, otherwise error out
    if (($export_result.rc -ne 0) -or ((Get-Item -Path $secedit_ini_path).Length -eq 0)) {
        Remove-Item -Path $secedit_ini_path -Force
        $result.rc = $export_result.rc
        $result.stdout = $export_result.stdout
        $result.stderr = $export_result.stderr
        Fail-Json $result "Failed to export secedit.ini file to $($secedit_ini_path)"
    }
    $secedit_ini = ConvertFrom-Ini -file_path $secedit_ini_path

    return $secedit_ini
}

Function Import-SecEdit($ini) {
    $secedit_ini_path = [IO.Path]::GetTempFileName()
    $secedit_db_path = [IO.Path]::GetTempFileName()
    Remove-Item -Path $secedit_db_path -Force # needs to be deleted for SecEdit.exe /import to work

    $ini_contents = ConvertTo-Ini -ini $ini
    Set-Content -Path $secedit_ini_path -Value $ini_contents

    $import_result = Run-SecEdit -arguments @("/configure", "/db", $secedit_db_path, "/cfg", $secedit_ini_path, "/quiet")
    $result.import_log = $import_result.log
    Remove-Item -Path $secedit_ini_path -Force
    if ($import_result.rc -ne 0) {
        $result.rc = $import_result.rc
        $result.stdout = $import_result.stdout
        $result.stderr = $import_result.stderr
        Fail-Json $result "Failed to import secedit.ini file from $($secedit_ini_path)"
    }
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

            $content += "$value_key = $value_value"
        }
    }

    return $content -join "`r`n"
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

    return $ini
}

Function Get-ExistingUsers($secedit_right_entry, $right) {
    $existing_users = @()
    if ($secedit_right_entry.ContainsKey($right)) {
        foreach ($existing_user in ($secedit_right_entry.$right -split ",")) {
            if ($existing_user.StartsWith("*S")) {
                $existing_users += $existing_user
            } else {
                $user_sid = Get-SID -account_name $existing_user
                $existing_users += "*$user_sid"
            }
        }
    }
    
    return ,$existing_users
}

Function Compare-UserList($existing_users, $new_users) {  
    $added_users = [String[]]@()
    $removed_users = [String[]]@()
    if ($action -eq "add") {
        $added_users = [Linq.Enumerable]::Except($new_users, $existing_users)
    } elseif ($action -eq "remove") {
        $removed_users = [Linq.Enumerable]::Intersect($new_users, $existing_users)
    } else {
        $added_users = [Linq.Enumerable]::Except($new_users, $existing_users)
        $removed_users = [Linq.Enumerable]::Except($existing_users, $new_users)
    }

    $change_result = @{
        added = $added_users
        removed = $removed_users
    }

    return $change_result
}

$ini_right_key = "Privilege Rights"

$new_users = [System.Collections.ArrayList]@()
foreach ($user in $users) {
    $new_users.Add("*$(Get-SID -account_name $user)")
}
$new_users = [String[]]$new_users.ToArray()

$secedit_ini = Export-SecEdit
$existing_users = [String[]](Get-ExistingUsers -secedit_right_entry $secedit_ini.$ini_right_key -right $name)
$change_result = Compare-UserList -existing_users $existing_users -new_users $new_users

if (($change_result.added.Length -gt 0) -or ($change_result.removed.Length -gt 0)) {
    $diff_text = "[$name]`n"

    $new_user_list = [System.Collections.ArrayList]$existing_users
    foreach ($user in $change_result.removed) {
        $user_name = Get-Username -sid $user
        $result.removed += $user_name
        $diff_text += "-$user_name`n"
        $new_user_list.Remove($user)
    }
    foreach ($user in $change_result.added) {
        $user_name = Get-Username -sid $user
        $result.added += $user_name
        $diff_text += "+$user_name`n"
        $new_user_list.Add($user)
    }
    
    if ($new_user_list.Count -eq 0) {
        $diff_text = "-$diff_text"
        $secedit_ini.$ini_right_key.$name = $null
    } else {
        if ($existing_users.Count -eq 0) {
            $diff_text = "+$diff_text"
        }
        $secedit_ini.$ini_right_key.$name = $new_user_list -join ","
    }

    $result.changed = $true
    if ($diff_mode) {
        $result.diff.prepared = $diff_text
    }
    if (-not $check_mode) {
        Import-SecEdit -ini $secedit_ini

        # verify the changes were applied successfully
        $secedit_ini = Export-SecEdit
        if ($secedit_ini.$ini_right_key.ContainsKey($name)) {
            $existing_users = [String[]] (Get-ExistingUsers -secedit_right_entry $secedit_ini.$ini_right_key -right $name)
            $change_result = Compare-UserList -existing_users $existing_users -new_users $new_users

            if (($change_result.added.Length -gt 0) -or ($change_result.removed.Length -gt 0)) {
                Fail-Json $result "Failed to modify right $name, right membership does not match expected membership"
            }
        } else {
            if ($new_user_list.Count -gt 0) {
                Fail-Json $result "Failed to modify right $name, invalid right name"
            }
        }
    }
}

Exit-Json $result
