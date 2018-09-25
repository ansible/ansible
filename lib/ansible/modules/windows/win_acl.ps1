#!powershell

# Copyright: (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
# Copyright: (c) 2015, Trond Hindenes
# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.PrivilegeUtil
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

# win_acl module (File/Resources Permission Additions/Removal)

#Functions
function Get-UserSID {
    param(
        [String]$AccountName
    )

    $userSID = $null
    $searchAppPools = $false

    if ($AccountName.Split("\").Count -gt 1) {
        if ($AccountName.Split("\")[0] -eq "IIS APPPOOL") {
            $searchAppPools = $true
            $AccountName = $AccountName.Split("\")[1]
        }
    }

    if ($searchAppPools) {
        Import-Module -Name WebAdministration
        $testIISPath = Test-Path -Path "IIS:"
        if ($testIISPath) {
            $appPoolObj = Get-ItemProperty -Path "IIS:\AppPools\$AccountName"
            $userSID = $appPoolObj.applicationPoolSid
        }
    }
    else {
        $userSID = Convert-ToSID -account_name $AccountName
    }

    return $userSID
}

$params = Parse-Args $args

Function SetPrivilegeTokens() {
    # Set privilege tokens only if admin.
    # Admins would have these privs or be able to set these privs in the UI Anyway

    $adminRole=[System.Security.Principal.WindowsBuiltInRole]::Administrator
    $myWindowsID=[System.Security.Principal.WindowsIdentity]::GetCurrent()
    $myWindowsPrincipal=new-object System.Security.Principal.WindowsPrincipal($myWindowsID)


    if ($myWindowsPrincipal.IsInRole($adminRole)) {
        # Need to adjust token privs when executing Set-ACL in certain cases.
        # e.g. d:\testdir is owned by group in which current user is not a member and no perms are inherited from d:\
        # This also sets us up for setting the owner as a feature.
        # See the following for details of each privilege
        # https://msdn.microsoft.com/en-us/library/windows/desktop/bb530716(v=vs.85).aspx
        Import-PrivilegeUtil
        $privileges = @(
            "SeRestorePrivilege",  # Grants all write access control to any file, regardless of ACL.
            "SeBackupPrivilege",  # Grants all read access control to any file, regardless of ACL.
            "SeTakeOwnershipPrivilege"  # Grants ability to take owernship of an object w/out being granted discretionary access
        )
        foreach ($privilege in $privileges) {
            $state = Get-AnsiblePrivilege -Name $privilege
            if ($state -eq $false) {
                Set-AnsiblePrivilege -Name $privilege -Value $true
            }
        }
    }
}


$result = @{
    changed = $false
}

$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true
$user = Get-AnsibleParam -obj $params -name "user" -type "str" -failifempty $true
$rights = Get-AnsibleParam -obj $params -name "rights" -type "str" -failifempty $true

$type = Get-AnsibleParam -obj $params -name "type" -type "str" -failifempty $true -validateset "allow","deny"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"

$inherit = Get-AnsibleParam -obj $params -name "inherit" -type "str"
$propagation = Get-AnsibleParam -obj $params -name "propagation" -type "str" -default "None" -validateset "InheritOnly","None","NoPropagateInherit"

If (-Not (Test-Path -Path $path)) {
    Fail-Json -obj $result -message "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = Get-UserSID -AccountName $user
if (!$sid) {
    Fail-Json -obj $result -message "$user is not a valid user or group on the host machine or domain"
}

If (Test-Path -Path $path -PathType Leaf) {
    $inherit = "None"
}
ElseIf ($null -eq $inherit) {
    $inherit = "ContainerInherit, ObjectInherit"
}

Try {
    SetPrivilegeTokens
    If ($path -match "^HK(CC|CR|CU|LM|U):\\") {
        $colRights = [System.Security.AccessControl.RegistryRights]$rights
    }
    Else {
        $colRights = [System.Security.AccessControl.FileSystemRights]$rights
    }

    $InheritanceFlag = [System.Security.AccessControl.InheritanceFlags]$inherit
    $PropagationFlag = [System.Security.AccessControl.PropagationFlags]$propagation

    If ($type -eq "allow") {
        $objType =[System.Security.AccessControl.AccessControlType]::Allow
    }
    Else {
        $objType =[System.Security.AccessControl.AccessControlType]::Deny
    }

    $objUser = New-Object System.Security.Principal.SecurityIdentifier($sid)
    If ($path -match "^HK(CC|CR|CU|LM|U):\\") {
        $objACE = New-Object System.Security.AccessControl.RegistryAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    }
    Else {
        $objACE = New-Object System.Security.AccessControl.FileSystemAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    }
    $objACL = Get-ACL $path

    # Check if the ACE exists already in the objects ACL list
    $match = $false

    # Workaround to handle special use case 'APPLICATION PACKAGE AUTHORITY\ALL APPLICATION PACKAGES' and
    # 'APPLICATION PACKAGE AUTHORITY\ALL RESTRICTED APPLICATION PACKAGES'- can't translate fully qualified name (win32 API bug/oddity)
    # 'ALL APPLICATION PACKAGES' exists only on Win2k12 and Win2k16 and 'ALL RESTRICTED APPLICATION PACKAGES' exists only in Win2k16
    $specialIdRefs = "ALL APPLICATION PACKAGES","ALL RESTRICTED APPLICATION PACKAGES"
    ForEach($rule in $objACL.Access){
        $idRefShortValue = ($rule.IdentityReference.Value).split('\')[-1]

        if ( $idRefShortValue -in $specialIdRefs ) {
            $ruleIdentity = (New-Object Security.Principal.NTAccount $idRefShortValue).Translate([Security.Principal.SecurityIdentifier])
        }
        else {
            $ruleIdentity = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier])
        }

        If ($path -match "^HK(CC|CR|CU|LM|U):\\") {
            If (($rule.RegistryRights -eq $objACE.RegistryRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($ruleIdentity -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) {
                $match = $true
                Break
            }
        } else {
            If (($rule.FileSystemRights -eq $objACE.FileSystemRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($ruleIdentity -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) {
                $match = $true
                Break
            }
        }
    }

    If ($state -eq "present" -And $match -eq $false) {
        Try {
            $objACL.AddAccessRule($objACE)
            Set-ACL $path $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json -obj $result -message "an exception occurred when adding the specified rule - $($_.Exception.Message)"
        }
    }
    ElseIf ($state -eq "absent" -And $match -eq $true) {
        Try {
            $objACL.RemoveAccessRule($objACE)
            Set-ACL $path $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json -obj $result -message "an exception occurred when removing the specified rule - $($_.Exception.Message)"
        }
    }
    Else {
        # A rule was attempting to be added but already exists
        If ($match -eq $true) {
            Exit-Json -obj $result -message "the specified rule already exists"
        }
        # A rule didn't exist that was trying to be removed
        Else {
            Exit-Json -obj $result -message "the specified rule does not exist"
        }
    }
}
Catch {
    Fail-Json -obj $result -message "an error occurred when attempting to $state $rights permission(s) on $path for $user - $($_.Exception.Message)"
}

Exit-Json -obj $result
