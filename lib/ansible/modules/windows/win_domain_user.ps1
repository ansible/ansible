#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -CSharpUtil Ansible.AccessToken

Function Test-Credential {
    param(
        [String]$Username,
        [String]$Password,
        [String]$Domain = $null
    )
    if (($Username.ToCharArray()) -contains [char]'@') {
        # UserPrincipalName
        $Domain = $null # force $Domain to be null, to prevent undefined behaviour, as a domain name is already included in the username
    } elseif (($Username.ToCharArray()) -contains [char]'\') {
        # Pre Win2k Account Name
        $Username = ($Username -split '\')[0]
        $Domain = ($Username -split '\')[1]
    } else {
        # No domain provided, so maybe local user, or domain specified separately.
    }

    try {
        $handle = [Ansible.AccessToken.TokenUtil]::LogonUser($Username, $Domain, $Password, "Network", "Default")
        $handle.Dispose()
        return $true
    } catch [Ansible.AccessToken.Win32Exception] {
        # following errors indicate the creds are correct but the user was
        # unable to log on for other reasons, which we don't care about
        $success_codes = @(
            0x0000052F,  # ERROR_ACCOUNT_RESTRICTION
            0x00000530,  # ERROR_INVALID_LOGON_HOURS
            0x00000531,  # ERROR_INVALID_WORKSTATION
            0x00000569  # ERROR_LOGON_TYPE_GRANTED
        )
        $failed_codes = @(
            0x0000052E,  # ERROR_LOGON_FAILURE
            0x00000532  # ERROR_PASSWORD_EXPIRED
        )

        if ($_.Exception.NativeErrorCode -in $failed_codes) {
            return $false
        } elseif ($_.Exception.NativeErrorCode -in $success_codes) {
            return $true
        } else {
            # an unknown failure, reraise exception
            throw $_
        }
    }
}

try {
    Import-Module ActiveDirectory
 }
 catch {
     Fail-Json $result "Failed to import ActiveDirectory PowerShell module. This module should be run on a domain controller, and the ActiveDirectory module must be available."
 }

$result = @{
    changed = $false
    created = $false
    password_updated = $false
}

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

# Module control parameters
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","query"
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "str" -default "always" -validateset "always","on_create","when_changed"
$groups_action = Get-AnsibleParam -obj $params -name "groups_action" -type "str" -default "replace" -validateset "add","remove","replace"
$domain_username = Get-AnsibleParam -obj $params -name "domain_username" -type "str"
$domain_password = Get-AnsibleParam -obj $params -name "domain_password" -type "str" -failifempty ($null -ne $domain_username)
$domain_server = Get-AnsibleParam -obj $params -name "domain_server" -type "str"

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

# Additional attributes
$attributes = Get-AnsibleParam -obj $params -name "attributes"

# Parameter validation
If ($null -ne $account_locked -and $account_locked) {
    Fail-Json $result "account_locked must be set to 'no' if provided"
}
If (($null -ne $password_expired) -and ($null -ne $password_never_expires)) {
    Fail-Json $result "password_expired and password_never_expires are mutually exclusive but have both been set"
}

$extra_args = @{}
if ($null -ne $domain_username) {
    $domain_password = ConvertTo-SecureString $domain_password -AsPlainText -Force
    $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $domain_username, $domain_password
    $extra_args.Credential = $credential
}
if ($null -ne $domain_server) {
    $extra_args.Server = $domain_server
}

try {
    $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
}
catch [Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException] {
    $user_obj = $null
}

If ($state -eq 'present') {
    # Ensure user exists
    $new_user = $false

    # If the account does not exist, create it
    If (-not $user_obj) {
        If ($null -ne $path){
            New-ADUser -Name $username -Path $path -WhatIf:$check_mode @extra_args
        }
        Else {
            New-ADUser -Name $username -WhatIf:$check_mode @extra_args
        }
        $new_user = $true
	$result.created = $true
        $result.changed = $true
        If ($check_mode) {
            Exit-Json $result
        }
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
    }

    If ($password) {
        # Don't unnecessary check for working credentials.
        # Set the password if we need to.
        # For new_users there is also no difference between always and when_changed
        # so we don't need to differentiate between this two states.
        If ($new_user -or ($update_password -eq "always")) {
            $set_new_credentials = $true
        } elseif ($update_password -eq "when_changed") {
            $set_new_credentials = -not (Test-Credential -Username $user_obj.UserPrincipalName -Password $password)
        } else {
            $set_new_credentials = $false
        }
        If ($set_new_credentials) {
            $secure_password = ConvertTo-SecureString $password -AsPlainText -Force
            Set-ADAccountPassword -Identity $username -Reset:$true -Confirm:$false -NewPassword $secure_password -WhatIf:$check_mode @extra_args
            $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
            $result.password_updated = $true
            $result.changed = $true
        }
    }

    # Configure password policies
    If (($null -ne $password_never_expires) -and ($password_never_expires -ne $user_obj.PasswordNeverExpires)) {
        Set-ADUser -Identity $username -PasswordNeverExpires $password_never_expires -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }
    If (($null -ne $password_expired) -and ($password_expired -ne $user_obj.PasswordExpired)) {
        Set-ADUser -Identity $username -ChangePasswordAtLogon $password_expired -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }
    If (($null -ne $user_cannot_change_password) -and ($user_cannot_change_password -ne $user_obj.CannotChangePassword)) {
        Set-ADUser -Identity $username -CannotChangePassword $user_cannot_change_password -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }

    # Assign other account settings
    If (($null -ne $upn) -and ($upn -ne $user_obj.UserPrincipalName)) {
        Set-ADUser -Identity $username -UserPrincipalName $upn -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }
    If (($null -ne $description) -and ($description -ne $user_obj.Description)) {
        Set-ADUser -Identity $username -description $description -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }
    If ($enabled -ne $user_obj.Enabled) {
        Set-ADUser -Identity $username -Enabled $enabled -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }
    If ((-not $account_locked) -and ($user_obj.LockedOut -eq $true)) {
        Unlock-ADAccount -Identity $username -WhatIf:$check_mode @extra_args
        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        $result.changed = $true
    }

    # Set user information
    Foreach ($key in $user_info.Keys) {
        If ($null -eq $user_info[$key]) {
            continue
        }
        $value = $user_info[$key]
        If ($value -ne $user_obj.$key) {
            $set_args = $extra_args.Clone()
            $set_args.$key = $value
            Set-ADUser -Identity $username -WhatIf:$check_mode @set_args
            $result.changed = $true
            $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
        }
    }

    # Set additional attributes
    $set_args = $extra_args.Clone()
    $run_change = $false
    if ($null -ne $attributes) {
        $add_attributes = @{}
        $replace_attributes = @{}
        foreach ($attribute in $attributes.GetEnumerator()) {
            $attribute_name = $attribute.Name
            $attribute_value = $attribute.Value

            $valid_property = [bool]($user_obj.PSobject.Properties.name -eq $attribute_name)
            if ($valid_property) {
                $existing_value = $user_obj.$attribute_name
                if ($existing_value -cne $attribute_value) {
                    $replace_attributes.$attribute_name = $attribute_value
                }
            } else {
                $add_attributes.$attribute_name = $attribute_value
            }
        }
        if ($add_attributes.Count -gt 0) {
            $set_args.Add = $add_attributes
            $run_change = $true
        }
        if ($replace_attributes.Count -gt 0) {
            $set_args.Replace = $replace_attributes
            $run_change = $true
        }
    }

    if ($run_change) {
        try {
            $user_obj = $user_obj | Set-ADUser -WhatIf:$check_mode -PassThru @set_args
        } catch {
            Fail-Json $result "failed to change user $($username): $($_.Exception.Message)"
        }
        $result.changed = $true
    }


    # Configure group assignment
    If ($null -ne $groups) {
        $group_list = $groups

        $groups = @()
        Foreach ($group in $group_list) {
            $groups += (Get-ADGroup -Identity $group @extra_args).DistinguishedName
        }

        $assigned_groups = @()
        Foreach ($group in (Get-ADPrincipalGroupMembership -Identity $username @extra_args)) {
            $assigned_groups += $group.DistinguishedName
        }

        switch ($groups_action) {
            "add" {
                Foreach ($group in $groups) {
                    If (-not ($assigned_groups -Contains $group)) {
                        Add-ADGroupMember -Identity $group -Members $username -WhatIf:$check_mode @extra_args
                        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
                        $result.changed = $true
                    }
                }
            }
            "remove" {
                Foreach ($group in $groups) {
                    If ($assigned_groups -Contains $group) {
                        Remove-ADGroupMember -Identity $group -Members $username -Confirm:$false -WhatIf:$check_mode @extra_args
                        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
                        $result.changed = $true
                    }
                }
            }
            "replace" {
                Foreach ($group in $assigned_groups) {
                    If (($group -ne $user_obj.PrimaryGroup) -and -not ($groups -Contains $group)) {
                        Remove-ADGroupMember -Identity $group -Members $username -Confirm:$false -WhatIf:$check_mode @extra_args
                        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
                        $result.changed = $true
                    }
                }
                Foreach ($group in $groups) {
                    If (-not ($assigned_groups -Contains $group)) {
                        Add-ADGroupMember -Identity $group -Members $username -WhatIf:$check_mode @extra_args
                        $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
                        $result.changed = $true
                    }
                }
            }
        }
    }
} ElseIf ($state -eq 'absent') {
    # Ensure user does not exist
    If ($user_obj) {
        Remove-ADUser $user_obj -Confirm:$false -WhatIf:$check_mode @extra_args
        $result.changed = $true
        If ($check_mode) {
            Exit-Json $result
        }
        $user_obj = $null
    }
}

If ($user_obj) {
    $user_obj = Get-ADUser -Identity $username -Properties * @extra_args
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
    Foreach ($group in (Get-ADPrincipalGroupMembership $username @extra_args)) {
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

Exit-Json $result
