#!powershell

# Copyright: (c) 2014, Paul Durivage <paul.durivage@rackspace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

########
$ADS_UF_PASSWD_CANT_CHANGE = 64
$ADS_UF_DONT_EXPIRE_PASSWD = 65536
$LOGON32_LOGON_NETWORK = 3
$LOGON32_PROVIDER_DEFAULT = 0

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

Function Test-LocalCredential {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the Win32 call, also the source isn't a secure string to using that is just a waste of time/code")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    param([String]$Username, [String]$Password)

    $platform_util = @'
using System;
using System.Runtime.InteropServices;

namespace Ansible
{
    public class WinUserPInvoke
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool LogonUser(
            string lpszUsername,
            string lpszDomain,
            string lpszPassword,
            UInt32 dwLogonType,
            UInt32 dwLogonProvider,
            out IntPtr phToken);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);
    }
}
'@

    $original_tmp = $env:TMP
    $env:TMP = $_remote_tmp
    Add-Type -TypeDefinition $platform_util
    $env:TMP = $original_tmp

    $handle = [IntPtr]::Zero
    $logon_res = [Ansible.WinUserPInvoke]::LogonUser($Username, $null, $Password,
        $LOGON32_LOGON_NETWORK, $LOGON32_PROVIDER_DEFAULT, [Ref]$handle)

    if ($logon_res) {
        $valid_credentials = $true
        [Ansible.WinUserPInvoke]::CloseHandle($handle) > $null
    } else {
        $err_code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        # following errors indicate the creds are correct but the user was
        # unable to log on for other reasons, which we don't care about
        $success_codes = @(
            0x0000052F,  # ERROR_ACCOUNT_RESTRICTION
            0x00000530,  # ERROR_INVALID_LOGON_HOURS
            0x00000531,  # ERROR_INVALID_WORKSTATION
            0x00000569  # ERROR_LOGON_TYPE_GRANTED
        )

        if ($err_code -eq 0x0000052E) {
            # ERROR_LOGON_FAILURE - the user or pass was incorrect
            $valid_credentials = $false
        } elseif ($err_code -in $success_codes) {
            $valid_credentials = $true
        } else {
            # an unknown failure, raise an Exception for this
            $win32_exp = New-Object -TypeName System.ComponentModel.Win32Exception -ArgumentList $err_code
            $err_msg = "LogonUserW failed: $($win32_exp.Message) (Win32ErrorCode: $err_code)"
            throw New-Object -TypeName System.ComponentModel.Win32Exception -ArgumentList $err_code, $err_msg
        }
    }

    return $valid_credentials
}

########

$params = Parse-Args $args;
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

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
            # ValidateCredentials will fail if either of these are true- just force update...
            If($user_obj.AccountDisabled -or $user_obj.PasswordExpired) {
                $password_match = $false
            }
            Else {
                try {
                    $password_match = Test-LocalCredential -Username $username -Password $password
                } catch [System.ComponentModel.Win32Exception] {
                    Fail-Json -obj $result -message "Failed to validate the user's credentials: $($_.Exception.Message)"
                }
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
