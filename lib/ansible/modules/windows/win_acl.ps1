#!powershell
# Copyright 2015, Phil Schwartz <schwartzmx@gmail.com>
# Copyright 2015, Trond Hindenes
# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

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

# Need to adjust token privs when executing Set-ACL in certain cases.
# e.g. d:\testdir is owned by group in which current user is not a member and no perms are inherited from d:\
# This also sets us up for setting the owner as a feature.
$AdjustTokenPrivileges = @"
using System;
using System.Runtime.InteropServices;

namespace Ansible {
        public class TokenManipulator {

            [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
            internal static extern bool AdjustTokenPrivileges(IntPtr htok, bool disall,
                ref TokPriv1Luid newst, int len, IntPtr prev, IntPtr relen);

            [DllImport("kernel32.dll", ExactSpelling = true)]
            internal static extern IntPtr GetCurrentProcess();

            [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
            internal static extern bool OpenProcessToken(IntPtr h, int acc,
                ref IntPtr phtok);

            [DllImport("advapi32.dll", SetLastError = true)]
            internal static extern bool LookupPrivilegeValue(string host, string name,
                ref long pluid);

            [StructLayout(LayoutKind.Sequential, Pack = 1)]
            internal struct TokPriv1Luid
            {
                public int Count;
                public long Luid;
                public int Attr;
            }

            internal const int SE_PRIVILEGE_DISABLED = 0x00000000;
            internal const int SE_PRIVILEGE_ENABLED = 0x00000002;
            internal const int TOKEN_QUERY = 0x00000008;
            internal const int TOKEN_ADJUST_PRIVILEGES = 0x00000020;

            public static bool AddPrivilege(string privilege) {
                try {
                    bool retVal;
                    TokPriv1Luid tp;
                    IntPtr hproc = GetCurrentProcess();
                    IntPtr htok = IntPtr.Zero;
                    retVal = OpenProcessToken(hproc, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ref htok);
                    tp.Count = 1;
                    tp.Luid = 0;
                    tp.Attr = SE_PRIVILEGE_ENABLED;
                    retVal = LookupPrivilegeValue(null, privilege, ref tp.Luid);
                    retVal = AdjustTokenPrivileges(htok, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero);
                    return retVal;
                }
                catch (Exception ex) {
                    throw ex;
                }
            }

            public static bool RemovePrivilege(string privilege) {
                try {
                    bool retVal;
                    TokPriv1Luid tp;
                    IntPtr hproc = GetCurrentProcess();
                    IntPtr htok = IntPtr.Zero;
                    retVal = OpenProcessToken(hproc, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ref htok);
                    tp.Count = 1;
                    tp.Luid = 0;
                    tp.Attr = SE_PRIVILEGE_DISABLED;
                    retVal = LookupPrivilegeValue(null, privilege, ref tp.Luid);
                    retVal = AdjustTokenPrivileges(htok, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero);
                    return retVal;
                }

                catch (Exception ex) {
                    throw ex;
                }
            }
        }
}
"@

$params = Parse-Args $args;
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$original_tmp = $env:TMP
$original_temp = $env:TEMP
$env:TMP = $_remote_tmp
$env:TEMP = $_remote_tmp
add-type $AdjustTokenPrivileges
$env:TMP = $original_tmp
$env:TEMP = $original_temp

Function SetPrivilegeTokens() {
    # Set privilege tokens only if admin.
    # Admins would have these privs or be able to set these privs in the UI Anyway

    $adminRole=[System.Security.Principal.WindowsBuiltInRole]::Administrator
    $myWindowsID=[System.Security.Principal.WindowsIdentity]::GetCurrent()
    $myWindowsPrincipal=new-object System.Security.Principal.WindowsPrincipal($myWindowsID)


    if ($myWindowsPrincipal.IsInRole($adminRole)) {

        # See the following for details of each privilege
        # https://msdn.microsoft.com/en-us/library/windows/desktop/bb530716(v=vs.85).aspx

        [void][Ansible.TokenManipulator]::AddPrivilege("SeRestorePrivilege") #Grants all write access control to any file, regardless of ACL.
        [void][Ansible.TokenManipulator]::AddPrivilege("SeBackupPrivilege") #Grants all read access control to any file, regardless of ACL.
        [void][Ansible.TokenManipulator]::AddPrivilege("SeTakeOwnershipPrivilege") #Grants ability to take owernship of an object w/out being granted discretionary access
    }
}

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

$path = Get-Attr $params "path" -failifempty $true
$user = Get-Attr $params "user" -failifempty $true
$rights = Get-Attr $params "rights" -failifempty $true

$type = Get-Attr $params "type" -failifempty $true -validateSet "allow","deny" -resultobj $result
$state = Get-Attr $params "state" "present" -validateSet "present","absent" -resultobj $result

$inherit = Get-Attr $params "inherit" ""
$propagation = Get-Attr $params "propagation" "None" -validateSet "None","NoPropagateInherit","InheritOnly" -resultobj $result

# We mount the HKCR, HKU, and HKCC registry hives so PS can access them
$path_qualifier = Split-Path -Path $path -Qualifier
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
    Fail-Json $result "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = Get-UserSID -AccountName $user
if (!$sid) {
    Fail-Json $result "$user is not a valid user or group on the host machine or domain"
}

If (Test-Path -LiteralPath $path -PathType Leaf) {
    $inherit = "None"
}
ElseIf ($inherit -eq "") {
    $inherit = "ContainerInherit, ObjectInherit"
}

# Bug in Set-Acl, Get-Acl where -LiteralPath only works for the Registry provider if the location is in that root
# qualifier.
Push-Location -LiteralPath $path_qualifier

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

        If ($path_item.PSProvider.Name -eq "Registry") {
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
            Set-ACL -LiteralPath $path -AclObject $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json $result "an exception occurred when adding the specified rule - $($_.Exception.Message)"
        }
    }
    ElseIf ($state -eq "absent" -And $match -eq $true) {
        Try {
            $objACL.RemoveAccessRule($objACE)
            Set-ACL -LiteralPath $path -AclObject $objACL
            $result.changed = $true
        }
        Catch {
            Fail-Json $result "an exception occurred when removing the specified rule - $($_.Exception.Message)"
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
    Fail-Json -obj $result -message "an error occurred when attempting to $state $rights permission(s) on $path for $user - $($_.Exception.Message)"
}
Finally {
    # Make sure we revert the location stack to the original path just for cleanups sake
    Pop-Location
}

Exit-Json $result
