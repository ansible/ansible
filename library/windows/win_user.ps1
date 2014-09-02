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

function Create-User([string]$user) {
   $adsiuser = $adsi.Create("User", $user)
   $adsiuser
   return
}

function Update-Password($user, [string]$passwd) {
    $user.SetPassword($passwd)
    $user.SetInfo()
}

function Delete-User($user) {
    $adsi.delete("user", $user.Name.Value)
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
    $user.SetInfo()
}

function Clear-UserFlag($user, $flag) {
    $user.UserFlags = ($user.UserFlags[0] -BXOR $flag)
    $user.SetInfo()
}

########

$params = Parse-Args $args;

$result = New-Object psobject @{
    changed = $false
};

If (-not $params.name.GetType) {
    Fail-Json $result "missing required arguments: name"
}

$username = Get-Attr $params "name"
$fullname = Get-Attr $params "fullname"
$description = Get-Attr $params "description"
$password = Get-Attr $params "password"

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'present') -and ($state -ne 'absent')) {
        Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
    }
}
ElseIf (!$params.state) {
    $state = "present"
}

If ($params.update_password) {
    $update_password = $params.update_password.ToString().ToLower()
    If (($update_password -ne 'always') -and ($update_password -ne 'on_create')) {
        Fail-Json $result "update_password is '$update_password'; must be 'always' or 'on_create'"
    }
}
ElseIf (!$params.update_password) {
    $update_password = "always"
}

$password_expired = Get-Attr $params "password_expired" $null;
If ($password_expired -ne $null) {
    $password_expired = $password_expired | ConvertTo-Bool;
}

$password_never_expires = Get-Attr $params "password_never_expires" $null;
If ($password_never_expires -ne $null) {
    $password_never_expires = $password_never_expires | ConvertTo-Bool;
}

$user_cannot_change_password = Get-Attr $params "user_cannot_change_password" $null;
If ($user_cannot_change_password -ne $null) {
    $user_cannot_change_password = $user_cannot_change_password | ConvertTo-Bool;
}

$account_disabled = Get-Attr $params "account_disabled" $null;
If ($account_disabled -ne $null) {
    $account_disabled = $account_disabled | ConvertTo-Bool;
}

$account_locked = Get-Attr $params "account_locked" $null;
If ($account_locked -ne $null) {
    $account_locked = $account_locked | ConvertTo-Bool;
    if ($account_locked) {
        Fail-Json $result "account_locked must be set to 'no' if provided"
    }
}

$user_obj = Get-User $username

Set-Attr $result "state" $state

If ($state -eq 'present') {
    # Add or update user
    try {
        If (!$user_obj.GetType) {
            $user_obj = Create-User $username
            If ($password -ne $null) {
                Update-Password $user_obj $password
            }
            $result.changed = $true
        }
        ElseIf (($password -ne $null) -and ($update_password -eq 'always')) {
            [void][system.reflection.assembly]::LoadWithPartialName('System.DirectoryServices.AccountManagement')
            $pc = New-Object -TypeName System.DirectoryServices.AccountManagement.PrincipalContext 'Machine', $env:COMPUTERNAME
            # FIXME: ValidateCredentials fails if PasswordExpired == 1
            If (!$pc.ValidateCredentials($username, $password)) {
                Update-Password $user_obj $password
                $result.changed = $true
            }
        }
        If (($fullname -ne $null) -and ($fullname -ne $user_obj.FullName[0])) {
            $user_obj.FullName = $fullname
            $user_obj.SetInfo()
            $result.changed = $true
        }
        If (($description -ne $null) -and ($description -ne $user_obj.Description[0])) {
            $user_obj.Description = $description
            $user_obj.SetInfo()
            $result.changed = $true
        }
        If (($password_expired -ne $null) -and ($password_expired -ne ($user_obj.PasswordExpired | ConvertTo-Bool))) {
            $user_obj.PasswordExpired = If ($password_expired) { 1 } Else { 0 };
            $user_obj.SetInfo()
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
            $user_obj.SetInfo()
            $result.changed = $true
        }
        If (($account_locked -ne $null) -and ($account_locked -ne $user_obj.IsAccountLocked)) {
            $user_obj.IsAccountLocked = $account_locked
            $user_obj.SetInfo()
            $result.changed = $true
        }
        $user_obj.RefreshCache()
        Set-Attr $result "name" $user_obj.Name[0]
        Set-Attr $result "fullname" $user_obj.FullName[0]
        Set-Attr $result "path" $user_obj.Path
        Set-Attr $result "description" $user_obj.Description[0]
        Set-Attr $result "password_expired" ($user_obj.PasswordExpired | ConvertTo-Bool)
        Set-Attr $result "password_never_expires" (Get-UserFlag $user_obj $ADS_UF_DONT_EXPIRE_PASSWD)
        Set-Attr $result "user_cannot_change_password" (Get-UserFlag $user_obj $ADS_UF_PASSWD_CANT_CHANGE)
        Set-Attr $result "account_disabled" $user_obj.AccountDisabled
        Set-Attr $result "account_locked" $user_obj.IsAccountLocked
        Set-Attr $result "sid" (New-Object System.Security.Principal.SecurityIdentifier($user_obj.ObjectSid.Value, 0)).Value
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}
Else {
    # Remove user
    try {
        If ($user_obj.GetType) {
            Set-Attr $result "name" $user_obj.Name[0]
            Delete-User $user_obj
            $result.changed = $true
        }
        Else {
            Set-Attr $result "name" $username
            Set-Attr $result "msg" "User '$username' was not found"
        }
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

Exit-Json $result;
