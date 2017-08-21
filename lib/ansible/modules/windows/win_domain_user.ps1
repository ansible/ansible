#!powershell
# This file is part of Ansible
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
try {
    Import-Module ActiveDirectory
 }
 catch {
     Fail-Json $result "Failed to import ActiveDirectory PowerShell module. This module should be run on a domain controller, and the ActiveDirectory module must be available."
 }

$result = @{
    changed = $false
    password_updated = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

# Module control parameters
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","query"
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "str" -default "always" -validateset "always","on_create"
$groups_action = Get-AnsibleParam -obj $params -name "groups_action" -type "str" -default "replace" -validateset "add","remove","replace"

# User account parameters
$username = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$password_expired = Get-AnsibleParam -obj $params -name "password_expired" -type "bool"
$password_never_expires = Get-AnsibleParam -obj $params -name "password_never_expires" -type "bool"
$user_cannot_change_password = Get-AnsibleParam -obj $params -name "user_cannot_change_password" -type "bool"
$account_locked = Get-AnsibleParam -obj $params -name "account_locked" -type "bool"
$groups = Get-AnsibleParam -obj $params -name "groups" -type "list"
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool" -default $true
$path = Get-AnsibleParam -obj $params -name "path" -type "str"
$upn = Get-AnsibleParam -obj $params -name "upn" -type "str"

# User informational parameters
$user_info = @{
    GivenName = Get-AnsibleParam -obj $params -name "firstname" -type "str"
    Surname = Get-AnsibleParam -obj $params -name "surname" -type "str"
    Company = Get-AnsibleParam -obj $params -name "company" -type "str"
    EmailAddress = Get-AnsibleParam -obj $params -name "email" -type "str"
    StreetAddress = Get-AnsibleParam -obj $params -name "street" -type "str"
    City = Get-AnsibleParam -obj $params -name "city" -type "str"
    State = Get-AnsibleParam -obj $params -name "state_province" -type "str"
    PostalCode = Get-AnsibleParam -obj $params -name "postal_code" -type "str"
    Country = Get-AnsibleParam -obj $params -name "country" -type "str"
}

# Parameter validation
If ($account_locked -ne $null -and $account_locked) {
    Fail-Json $result "account_locked must be set to 'no' if provided"
}
If (($password_expired -ne $null) -and ($password_never_expires -ne $null)) {
    Fail-Json $result "password_expired and password_never_expires are mutually exclusive but have both been set"
}

try {
    $user_obj = Get-ADUser -Identity $username -Properties *
}
catch {
    $user_obj = $null
}

If ($state -eq 'present') {
    # Ensure user exists
    try {
        $new_user = $false

        # If the account does not exist, create it
        If (-not $user_obj) {
            If ($path -ne $null){
                New-ADUser -Name $username -Path $path -WhatIf:$check_mode
            }
            Else {
                New-ADUser -Name $username -WhatIf:$check_mode
            }
            $new_user = $true
            $result.changed = $true
            If ($check_mode) {
                Exit-Json $result
            }
            $user_obj = Get-ADUser -Identity $username -Properties *
        }

        # Set the password if required
        If ($password -and (($new_user -and $update_password -eq "on_create") -or $update_password -eq "always")) {
            $secure_password = ConvertTo-SecureString $password -AsPlainText -Force
            Set-ADAccountPassword -Identity $username -Reset:$true -Confirm:$false -NewPassword $secure_password -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.password_updated = $true
            $result.changed = $true
        }

        # Configure password policies
        If (($password_never_expires -ne $null) -and ($password_never_expires -ne $user_obj.PasswordNeverExpires)) {
            Set-ADUser -Identity $username -PasswordNeverExpires $password_never_expires -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }
        If (($password_expired -ne $null) -and ($password_expired -ne $user_obj.PasswordExpired)) {
            Set-ADUser -Identity $username -ChangePasswordAtLogon $password_expired -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }
        If (($user_cannot_change_password -ne $null) -and ($user_cannot_change_password -ne $user_obj.CannotChangePassword)) {
            Set-ADUser -Identity $username -CannotChangePassword $user_cannot_change_password -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }

        # Assign other account settings
        If (($upn -ne $null) -and ($upn -ne $user_obj.UserPrincipalName)) {
            Set-ADUser -Identity $username -UserPrincipalName $upn -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }
        If (($description -ne $null) -and ($description -ne $user_obj.Description)) {
            Set-ADUser -Identity $username -description $description -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }
        If ($enabled -ne $user_obj.Enabled) {
            Set-ADUser -Identity $username -Enabled $enabled -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }
        If ((-not $account_locked) -and ($user_obj.LockedOut -eq $true)) {
            Unlock-ADAccount -Identity $username -WhatIf:$check_mode
            $user_obj = Get-ADUser -Identity $username -Properties *
            $result.changed = $true
        }

        # Set user information
        Foreach ($key in $user_info.Keys) {
            If ($user_info[$key] -eq $null) {
                continue
            }
            $value = $user_info[$key]
            If ($value -ne $user_obj.$key) {
                $expression = "Set-ADUser -Identity $username -$key '$value'"
                If (-not $check_mode) {
                    Invoke-Expression $expression
                }
                $result.changed = $true
                $user_obj = Get-ADUser -Identity $username -Properties *
            }
        }

        # Configure group assignment
        If ($groups -ne $null) {
            $group_list = $groups

            $groups = @()
            Foreach ($group in $group_list) {
                $groups += (Get-ADGroup -Identity $group).DistinguishedName
            }

            $assigned_groups = @()
            Foreach ($group in (Get-ADPrincipalGroupMembership -Identity $username)) {
                $assigned_groups += $group.DistinguishedName
            }

            switch ($groups_action) {
                "add" {
                    Foreach ($group in $groups) {
                        If (-not ($assigned_groups -Contains $group)) {
                            Add-ADGroupMember -Identity $group -Members $username -WhatIf:$check_mode
                            $user_obj = Get-ADUser -Identity $username -Properties *
                            $result.changed = $true
                        }
                    }
                }
                "remove" {
                    Foreach ($group in $groups) {
                        If ($assigned_groups -Contains $group) {
                            Remove-ADGroupMember -Identity $group -Members $username -Confirm:$false -WhatIf:$check_mode
                            $user_obj = Get-ADUser -Identity $username -Properties *
                            $result.changed = $true
                        }
                    }
                }
                "replace" {
                    Foreach ($group in $assigned_groups) {
                        If (($group -ne $user_obj.PrimaryGroup) -and -not ($groups -Contains $group)) {
                            Remove-ADGroupMember -Identity $group -Members $username -Confirm:$false -WhatIf:$check_mode
                            $user_obj = Get-ADUser -Identity $username -Properties *
                            $result.changed = $true
                        }
                    }
                    Foreach ($group in $groups) {
                        If (-not ($assigned_groups -Contains $group)) {
                            Add-ADGroupMember -Identity $group -Members $username -WhatIf:$check_mode
                            $user_obj = Get-ADUser -Identity $username -Properties *
                            $result.changed = $true
                        }
                    }
                }
            }
        }

    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
} ElseIf ($state -eq 'absent') {
    # Ensure user does not exist
    try {
        If ($user_obj) {
            Remove-ADUser $user_obj -Confirm:$false -WhatIf:$check_mode
            $result.changed = $true
            If ($check_mode) {
                Exit-Json $result
            }
            $user_obj = $null
        }
    }
    catch {
        Fail-Json $result $_.Exception.Message
    }
}

try {
    If ($user_obj) {
        $user_obj = Get-ADUser -Identity $username -Properties *
        $result.name = $user_obj.Name
        $result.firstname = $user_obj.GivenName
        $result.surname = $user_obj.Surname
        $result.enabled = $user_obj.Enabled
        $result.company = $user_obj.Company
        $result.street = $user_obj.StreetAddress
        $result.email = $user_obj.EmailAddress
        $result.city = $user_obj.City
        $result.state_province = $user_obj.State
        $result.country = $user_obj.Country
        $result.postal_code = $user_obj.PostalCode
        $result.distinguished_name = $user_obj.DistinguishedName
        $result.description = $user_obj.Description
        $result.password_expired = $user_obj.PasswordExpired
        $result.password_never_expires = $user_obj.PasswordNeverExpires
        $result.user_cannot_change_password = $user_obj.CannotChangePassword
        $result.account_locked = $user_obj.LockedOut
        $result.sid = [string]$user_obj.SID
        $result.upn = $user_obj.UserPrincipalName
        $user_groups = @()
        Foreach ($group in (Get-ADPrincipalGroupMembership $username)) {
            $user_groups += $group.name
        }
        $result.groups = $user_groups
        $result.msg = "User '$username' is present"
        $result.state = "present"
    }
    Else {
        $result.name = $username
        $result.msg = "User '$username' is absent"
        $result.state = "absent"
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result