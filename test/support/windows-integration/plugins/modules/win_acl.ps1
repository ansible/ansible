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
        $testIISPath = Test-Path -LiteralPath "IIS:"
        if ($testIISPath) {
            $appPoolObj = Get-ItemProperty -LiteralPath "IIS:\AppPools\$AccountName"
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

# We mount the HKCR, HKU, and HKCC registry hives so PS can access them.
# Network paths have no qualifiers so we use -EA SilentlyContinue to ignore that
$path_qualifier = Split-Path -Path $path -Qualifier -ErrorAction SilentlyContinue
if ($path_qualifier -eq "HKCR:" -and (-not (Test-Path -LiteralPath HKCR:\))) {
    New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT > $null
}
if ($path_qualifier -eq "HKU:" -and (-not (Test-Path -LiteralPath HKU:\))) {
    New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS > $null
}
if ($path_qualifier -eq "HKCC:" -and (-not (Test-Path -LiteralPath HKCC:\))) {
    New-PSDrive -Name HKCC -PSProvider Registry -Root HKEY_CURRENT_CONFIG > $null
}

If (-Not (Test-Path -LiteralPath $path)) {
    Fail-Json -obj $result -message "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = Get-UserSID -AccountName $user
if (!$sid) {
    Fail-Json -obj $result -message "$user is not a valid user or group on the host machine or domain"
}

If (Test-Path -LiteralPath $path -PathType Leaf) {
    $inherit = "None"
}
ElseIf ($null -eq $inherit) {
    $inherit = "ContainerInherit, ObjectInherit"
}

# Bug in Set-Acl, Get-Acl where -LiteralPath only works for the Registry provider if the location is in that root
# qualifier. We also don't have a qualifier for a network path so only change if not null
if ($null -ne $path_qualifier) {
    Push-Location -LiteralPath $path_qualifier
}

Try {
    SetPrivilegeTokens
    $path_item = Get-Item -LiteralPath $path -Force
    If ($path_item.PSProvider.Name -eq "Registry") {
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
    If ($path_item.PSProvider.Name -eq "Registry") {
        $objACE = New-Object System.Security.AccessControl.RegistryAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    }
    Else {
        $objACE = New-Object System.Security.AccessControl.FileSystemAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    }
    $objACL = Get-ACL -LiteralPath $path

    # Check if the ACE exists already in the objects ACL list
    $match = $false

    ForEach($rule in $objACL.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])){

        If ($path_item.PSProvider.Name -eq "Registry") {
            If (($rule.RegistryRights -eq $objACE.RegistryRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($rule.IdentityReference -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) {
                $match = $true
                Break
            }
        } else {
            If (($rule.FileSystemRights -eq $objACE.FileSystemRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($rule.IdentityReference -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) {
                $match = $true
                Break
            }
        }
    }

    If ($state -eq "present" -And $match -eq $false) {
        Try {
            $objACL.AddAccessRule($objACE)
            If ($path_item.PSProvider.Name -eq "Registry") {
                Set-ACL -LiteralPath $path -AclObject $objACL
            } else {
                (Get-Item -LiteralPath $path).SetAccessControl($objACL)
            }
            $result.changed = $true
        }
        Catch {
            Fail-Json -obj $result -message "an exception occurred when adding the specified rule - $($_.Exception.Message)"
        }
    }
    ElseIf ($state -eq "absent" -And $match -eq $true) {
        Try {
            $objACL.RemoveAccessRule($objACE)
            If ($path_item.PSProvider.Name -eq "Registry") {
                Set-ACL -LiteralPath $path -AclObject $objACL
            } else {
                (Get-Item -LiteralPath $path).SetAccessControl($objACL)
            }
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
Finally {
    # Make sure we revert the location stack to the original path just for cleanups sake
    if ($null -ne $path_qualifier) {
        Pop-Location
    }
}

Exit-Json -obj $result
