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
$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"

function Get-User($user) {
    $adsi.Children | where {$_.SchemaClassName -eq 'user' -and $_.Name -eq $user }
    return
}

function Create-User([string]$user, [string]$passwd) {
   $adsiuser = $adsi.Create("User", $user)
   $adsiuser.SetPassword($passwd)
   $adsiuser.SetInfo()
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
########

$params = Parse-Args $args;

$result = New-Object psobject @{
    changed = $false
};

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name"
}

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'present') -and ($state -ne 'absent')) {
        Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
    }
}
Elseif (!$params.state) {
    $state = "present"
}

If ((-not $params.password.GetType) -and ($state -eq 'present'))
{
    Fail-Json $result "missing required arguments: password"
}

$username = Get-Attr $params "name"
$password = Get-Attr $params "password"

$user_obj = Get-User $username

if ($state -eq 'present') {
    # Add or update user
    try {
        if ($user_obj.GetType) {
            Update-Password $user_obj $password
        }
        else {
            Create-User $username $password
        }
        $result.changed = $true
        $user_obj = Get-User $username
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}
else {
    # Remove user
    try {
        if ($user_obj.GetType) {
            Delete-User $user_obj
            $result.changed = $true
        }
        else {
            Set-Attr $result "msg" "User '$username' was not found"
        }
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

# Set-Attr $result "user" $user_obj
Set-Attr $result "user_name" $user_obj.Name
Set-Attr $result "user_fullname" $user_obj.FullName
Set-Attr $result "user_path" $user_obj.Path

Exit-Json $result;
