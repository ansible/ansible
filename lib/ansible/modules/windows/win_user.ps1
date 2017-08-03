#!powershell
# This file is part of Ansible
#
# Copyright 2014, Paul Durivage <paul.durivage@rackspace.com>
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

########
$ADS_UF_PASSWD_CANT_CHANGE = 64
$ADS_UF_DONT_EXPIRE_PASSWD = 65536

$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"

function Get-User($user) {
    $adsi.Children | where {$_.SchemaClassName -eq 'user' -and $_.Name -eq $user }
    return
}

function Get-UserFlag($user, $flag) {
    If ($user.UserFlags[0] -band $flag) {
        $true
    }
    Else {
        $false
    }
}

function Set-UserFlag($user, $flag) { 
    $user.UserFlags = ($user.UserFlags[0] -BOR $flag)
}

function Clear-UserFlag($user, $flag) {
    $user.UserFlags = ($user.UserFlags[0] -BXOR $flag)
}

function Get-Group($grp) {
    $adsi.Children | where { $_.SchemaClassName -eq 'Group' -and $_.Name -eq $grp }
    return
}

########

$params = Parse-Args $args;

$result = @{
    changed = $false
};

$username = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$fullname = Get-AnsibleParam -obj $params -name "fullname" -type "str"
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","query"
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "str" -default "always" -validateset "always","on_create"
$password_expired = Get-AnsibleParam -obj $params -name "password_expired" -type "bool"
$password_never_expires = Get-AnsibleParam -obj $params -name "password_never_expires" -type "bool"
$user_cannot_change_password = Get-AnsibleParam -obj $params -name "user_cannot_change_password" -type "bool"
$account_disabled = Get-AnsibleParam -obj $params -name "account_disabled" -type "bool"
$account_locked = Get-AnsibleParam -obj $params -name "account_locked" -type "bool"
$groups = Get-AnsibleParam -obj $params -name "groups"
$groups_action = Get-AnsibleParam -obj $params -name "groups_action" -type "str" -default "replace" -validateset "add","remove","replace"

If ($account_locked -ne $null -and $account_locked) {
    Fail-Json $result "account_locked must be set to 'no' if provided"
}

If ($groups -ne $null) {
    If ($groups -is [System.String]) {
        [string[]]$groups = $groups.Split(",")
    }
    ElseIf ($groups -isnot [System.Collections.IList]) {
        Fail-Json $result "groups must be a string or array"
    }
    $groups = $groups | ForEach { ([string]$_).Trim() } | Where { $_ }
    If ($groups -eq $null) {
        $groups = @()
    }
}

$user_obj = Get-User $username

If ($state -eq 'present') {
    # Add or update user
    try {
        If (-not $user_obj) {
            $user_obj = $adsi.Create("User", $username)
            If ($password -ne $null) {
                $user_obj.SetPassword($password)
            }
            $user_obj.SetInfo()
            $result.changed = $true
        }
        ElseIf (($password -ne $null) -and ($update_password -eq 'always')) {
            [void][system.reflection.assembly]::LoadWithPartialName('System.DirectoryServices.AccountManagement')
            $host_name = [System.Net.Dns]::GetHostName()
            $pc = New-Object -TypeName System.DirectoryServices.AccountManagement.PrincipalContext 'Machine', $host_name

            # ValidateCredentials will fail if either of these are true- just force update...
            If($user_obj.AccountDisabled -or $user_obj.PasswordExpired) {
                $password_match = $false
            }
            Else {
                $password_match = $pc.ValidateCredentials($username, $password)
            }

            If (-not $password_match) {
                $user_obj.SetPassword($password)
                $result.changed = $true
            }
        }
        If (($fullname -ne $null) -and ($fullname -ne $user_obj.FullName[0])) {
            $user_obj.FullName = $fullname
            $result.changed = $true
        }
        If (($description -ne $null) -and ($description -ne $user_obj.Description[0])) {
            $user_obj.Description = $description
            $result.changed = $true
        }
        If (($password_expired -ne $null) -and ($password_expired -ne ($user_obj.PasswordExpired | ConvertTo-Bool))) {
            $user_obj.PasswordExpired = If ($password_expired) { 1 } Else { 0 }
            $result.changed = $true
        }
        If (($password_never_expires -ne $null) -and ($password_never_expires -ne (Get-UserFlag $user_obj $ADS_UF_DONT_EXPIRE_PASSWD))) {
            If ($password_never_expires) {
                Set-UserFlag $user_obj $ADS_UF_DONT_EXPIRE_PASSWD
            }
            Else {
                Clear-UserFlag $user_obj $ADS_UF_DONT_EXPIRE_PASSWD
            }
            $result.changed = $true
        }
        If (($user_cannot_change_password -ne $null) -and ($user_cannot_change_password -ne (Get-UserFlag $user_obj $ADS_UF_PASSWD_CANT_CHANGE))) {
            If ($user_cannot_change_password) {
                Set-UserFlag $user_obj $ADS_UF_PASSWD_CANT_CHANGE
            }
            Else {
                Clear-UserFlag $user_obj $ADS_UF_PASSWD_CANT_CHANGE
            }
            $result.changed = $true
        }
        If (($account_disabled -ne $null) -and ($account_disabled -ne $user_obj.AccountDisabled)) {
            $user_obj.AccountDisabled = $account_disabled
            $result.changed = $true
        }
        If (($account_locked -ne $null) -and ($account_locked -ne $user_obj.IsAccountLocked)) {
            $user_obj.IsAccountLocked = $account_locked
            $result.changed = $true
        }
        If ($result.changed) {
            $user_obj.SetInfo()
        }
        If ($null -ne $groups) {
            [string[]]$current_groups = $user_obj.Groups() | ForEach { $_.GetType().InvokeMember("Name", "GetProperty", $null, $_, $null) }
            If (($groups_action -eq "remove") -or ($groups_action -eq "replace")) {
                ForEach ($grp in $current_groups) {
                    If ((($groups_action -eq "remove") -and ($groups -contains $grp)) -or (($groups_action -eq "replace") -and ($groups -notcontains $grp))) {
                        $group_obj = Get-Group $grp
                        If ($group_obj) {
                            $group_obj.Remove($user_obj.Path)
                            $result.changed = $true
                        }
                        Else {
                            Fail-Json $result "group '$grp' not found"
                        }
                    }
                }
            }
            If (($groups_action -eq "add") -or ($groups_action -eq "replace")) {
                ForEach ($grp in $groups) {
                    If ($current_groups -notcontains $grp) {
                        $group_obj = Get-Group $grp
                        If ($group_obj) {
                            $group_obj.Add($user_obj.Path)
                            $result.changed = $true
                        }
                        Else {
                            Fail-Json $result "group '$grp' not found"
                        }
                    }
                }
            }
        }
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}
ElseIf ($state -eq 'absent') {
    # Remove user
    try {
        If ($user_obj) {
            $username = $user_obj.Name.Value
            $adsi.delete("User", $user_obj.Name.Value)
            $result.changed = $true
            $result.msg = "User '$username' deleted successfully"
            $user_obj = $null
        } else {
            $result.msg = "User '$username' was not found"
        }
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

try {
    If ($user_obj -and $user_obj -is [System.DirectoryServices.DirectoryEntry]) {
        $user_obj.RefreshCache()
        $result.name = $user_obj.Name[0]
        $result.fullname = $user_obj.FullName[0]
        $result.path = $user_obj.Path
        $result.description = $user_obj.Description[0]
        $result.password_expired = ($user_obj.PasswordExpired | ConvertTo-Bool)
        $result.password_never_expires = (Get-UserFlag $user_obj $ADS_UF_DONT_EXPIRE_PASSWD)
        $result.user_cannot_change_password = (Get-UserFlag $user_obj $ADS_UF_PASSWD_CANT_CHANGE)
        $result.account_disabled = $user_obj.AccountDisabled
        $result.account_locked = $user_obj.IsAccountLocked
        $result.sid = (New-Object System.Security.Principal.SecurityIdentifier($user_obj.ObjectSid.Value, 0)).Value
        $user_groups = @()
        ForEach ($grp in $user_obj.Groups()) {
            $group_result = @{
                name = $grp.GetType().InvokeMember("Name", "GetProperty", $null, $grp, $null)
                path = $grp.GetType().InvokeMember("ADsPath", "GetProperty", $null, $grp, $null)
            }
            $user_groups += $group_result;
        }
        $result.groups = $user_groups
        $result.state = "present"
    }
    Else {
        $result.name = $username
        if ($state -eq 'query') {
            $result.msg = "User '$username' was not found"
        }
        $result.state = "absent"
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result
