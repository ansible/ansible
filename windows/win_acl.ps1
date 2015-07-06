#!powershell
# This file is part of Ansible
#
# Copyright 2015, Phil Schwartz <schwartzmx@gmail.com>
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

# win_acl module (File/Resources Permission Additions/Removal)
$params = Parse-Args $args;

$result = New-Object psobject @{
    win_acl = New-Object psobject
    changed = $false
}

If ($params.src) {
    $src = $params.src.toString()

    If (-Not (Test-Path -Path $src)) {
        Fail-Json $result "$src file or directory does not exist on the host"
    }
}
Else {
    Fail-Json $result "missing required argument: src"
}

If ($params.user) {
    $user = $params.user.toString()

    # Test that the user/group exists on the local machine
    $localComputer = [ADSI]("WinNT://"+[System.Net.Dns]::GetHostName())
    $list = ($localComputer.psbase.children | Where-Object { (($_.psBase.schemaClassName -eq "User") -Or ($_.psBase.schemaClassName -eq "Group"))} | Select-Object -expand Name)
    If (-Not ($list -contains "$user")) {
        Fail-Json $result "$user is not a valid user or group on the host machine"
    }
}
Else {
    Fail-Json $result "missing required argument: user.  specify the user or group to apply permission changes."
}

If ($params.type -eq "allow") {
    $type = $true
}
ElseIf ($params.type -eq "deny") {
    $type = $false
}
Else {
    Fail-Json $result "missing required argument: type. specify whether to allow or deny the specified rights."
}

If ($params.inherit) {
    # If it's a file then no flags can be set or an exception will be thrown
    If (Test-Path -Path $src -PathType Leaf) {
        $inherit = "None"
    }
    Else {
        $inherit = $params.inherit.toString()
    }
}
Else {
    # If it's a file then no flags can be set or an exception will be thrown
    If (Test-Path -Path $src -PathType Leaf) {
        $inherit = "None"
    }
    Else {
        $inherit = "ContainerInherit, ObjectInherit"
    }
}

If ($params.propagation) {
    $propagation = $params.propagation.toString()
}
Else {
    $propagation = "None"
}

If ($params.rights) {
    $rights = $params.rights.toString()
}
Else {
    Fail-Json $result "missing required argument: rights"
}

If ($params.state -eq "absent") {
    $state = "remove"
}
Else {
    $state = "add"
}

Try {
    $colRights = [System.Security.AccessControl.FileSystemRights]$rights
    $InheritanceFlag = [System.Security.AccessControl.InheritanceFlags]$inherit
    $PropagationFlag = [System.Security.AccessControl.PropagationFlags]$propagation

    If ($type) {
        $objType =[System.Security.AccessControl.AccessControlType]::Allow
    }
    Else {
        $objType =[System.Security.AccessControl.AccessControlType]::Deny
    }

    $objUser = New-Object System.Security.Principal.NTAccount($user)
    $objACE = New-Object System.Security.AccessControl.FileSystemAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    $objACL = Get-ACL $src

    # Check if the ACE exists already in the objects ACL list
    $match = $false
    ForEach($rule in $objACL.Access){
        If (($rule.FileSystemRights -eq $objACE.FileSystemRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($rule.IdentityReference -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) { 
            $match = $true
            Break
        } 
    }

    If ($state -eq "add" -And $match -eq $false) {
        Try {
            $objACL.AddAccessRule($objACE)
            Set-ACL $src $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json $result "an exception occured when adding the specified rule"
        }
    }
    ElseIf ($state -eq "remove" -And $match -eq $true) {
        Try {
            $objACL.RemoveAccessRule($objACE)
            Set-ACL $src $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json $result "an exception occured when removing the specified rule"
        }
    }
    Else {
        # A rule was attempting to be added but already exists
        If ($match -eq $true) {
            Exit-Json $result "the specified rule already exists"
        }
        # A rule didn't exist that was trying to be removed
        Else {
            Exit-Json $result "the specified rule does not exist"
        }       
    }
}
Catch {
    Fail-Json $result "an error occured when attempting to $state $rights permission(s) on $src for $user"
}

Exit-Json $result