#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$users = Get-AnsibleParam -obj $params -name "users" -type "list" -failifempty $true
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -default "set" -validateset "add","remove","set"

$result = @{
    changed = $false
    added = @()
    removed = @()
}

if ($diff_mode) {
    $result.diff = @{}
}

$sec_helper_util = @"
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;

namespace Ansible
{
    public class LsaRightHelper : IDisposable
    {
        // Code modified from https://gallery.technet.microsoft.com/scriptcenter/Grant-Revoke-Query-user-26e259b0

        enum Access : int
        {
            POLICY_READ = 0x20006,
            POLICY_ALL_ACCESS = 0x00F0FFF,
            POLICY_EXECUTE = 0X20801,
            POLICY_WRITE = 0X207F8
        }

        IntPtr lsaHandle;

        const string LSA_DLL = "advapi32.dll";
        const CharSet DEFAULT_CHAR_SET = CharSet.Unicode;

        const uint STATUS_NO_MORE_ENTRIES = 0x8000001a;
        const uint STATUS_NO_SUCH_PRIVILEGE = 0xc0000060;

        internal sealed class Sid : IDisposable
        {
            public IntPtr pSid = IntPtr.Zero;
            public SecurityIdentifier sid = null;

            public Sid(string sidString)
            {
                try
                {
                    sid = new SecurityIdentifier(sidString);
                } catch
                {
                    throw new ArgumentException(String.Format("SID string {0} could not be converted to SecurityIdentifier", sidString));
                }                    

                Byte[] buffer = new Byte[sid.BinaryLength];
                sid.GetBinaryForm(buffer, 0);

                pSid = Marshal.AllocHGlobal(sid.BinaryLength);
                Marshal.Copy(buffer, 0, pSid, sid.BinaryLength);
            }

            public void Dispose()
            {
                if (pSid != IntPtr.Zero)
                {
                    Marshal.FreeHGlobal(pSid);
                    pSid = IntPtr.Zero;
                }
                GC.SuppressFinalize(this);
            }
            ~Sid() { Dispose(); }
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct LSA_OBJECT_ATTRIBUTES
        {
            public int Length;
            public IntPtr RootDirectory;
            public IntPtr ObjectName;
            public int Attributes;
            public IntPtr SecurityDescriptor;
            public IntPtr SecurityQualityOfService;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = DEFAULT_CHAR_SET)]
        private struct LSA_UNICODE_STRING
        {
            public ushort Length;
            public ushort MaximumLength;
            [MarshalAs(UnmanagedType.LPWStr)]
            public string Buffer;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct LSA_ENUMERATION_INFORMATION
        {
            public IntPtr Sid;
        }

        [DllImport(LSA_DLL, CharSet = DEFAULT_CHAR_SET, SetLastError = true)]
        private static extern uint LsaOpenPolicy(
            LSA_UNICODE_STRING[] SystemName,
            ref LSA_OBJECT_ATTRIBUTES ObjectAttributes,
            int AccessMask,
            out IntPtr PolicyHandle
        );

        [DllImport(LSA_DLL, CharSet = DEFAULT_CHAR_SET, SetLastError = true)]
        private static extern uint LsaAddAccountRights(
            IntPtr PolicyHandle,
            IntPtr pSID,
            LSA_UNICODE_STRING[] UserRights,
            int CountOfRights
        );

        [DllImport(LSA_DLL, CharSet = DEFAULT_CHAR_SET, SetLastError = true)]
        private static extern uint LsaRemoveAccountRights(
            IntPtr PolicyHandle,
            IntPtr pSID,
            bool AllRights,
            LSA_UNICODE_STRING[] UserRights,
            int CountOfRights
        );

        [DllImport(LSA_DLL, CharSet = DEFAULT_CHAR_SET, SetLastError = true)]
        private static extern uint LsaEnumerateAccountsWithUserRight(
            IntPtr PolicyHandle,
            LSA_UNICODE_STRING[] UserRights,
            out IntPtr EnumerationBuffer,
            out ulong CountReturned
        );

        [DllImport(LSA_DLL)]
        private static extern int LsaNtStatusToWinError(int NTSTATUS);

        [DllImport(LSA_DLL)]
        private static extern int LsaClose(IntPtr PolicyHandle);

        [DllImport(LSA_DLL)]
        private static extern int LsaFreeMemory(IntPtr Buffer);

        public LsaRightHelper()
        {
            LSA_OBJECT_ATTRIBUTES lsaAttr;
            lsaAttr.RootDirectory = IntPtr.Zero;
            lsaAttr.ObjectName = IntPtr.Zero;
            lsaAttr.Attributes = 0;
            lsaAttr.SecurityDescriptor = IntPtr.Zero;
            lsaAttr.SecurityQualityOfService = IntPtr.Zero;
            lsaAttr.Length = Marshal.SizeOf(typeof(LSA_OBJECT_ATTRIBUTES));

            lsaHandle = IntPtr.Zero;

            LSA_UNICODE_STRING[] system = new LSA_UNICODE_STRING[1];
            system[0] = InitLsaString("");

            uint ret = LsaOpenPolicy(system, ref lsaAttr, (int)Access.POLICY_ALL_ACCESS, out lsaHandle);
            if (ret != 0)
                throw new Win32Exception(LsaNtStatusToWinError((int)ret));
        }

        public void AddPrivilege(string sidString, string privilege)
        {
            uint ret = 0;
            using (Sid sid = new Sid(sidString))
            {
                LSA_UNICODE_STRING[] privileges = new LSA_UNICODE_STRING[1];
                privileges[0] = InitLsaString(privilege);
                ret = LsaAddAccountRights(lsaHandle, sid.pSid, privileges, 1);
            }
            if (ret != 0)
                throw new Win32Exception(LsaNtStatusToWinError((int)ret));
        }

        public void RemovePrivilege(string sidString, string privilege)
        {
            uint ret = 0;
            using (Sid sid = new Sid(sidString))
            {
                LSA_UNICODE_STRING[] privileges = new LSA_UNICODE_STRING[1];
                privileges[0] = InitLsaString(privilege);
                ret = LsaRemoveAccountRights(lsaHandle, sid.pSid, false, privileges, 1);
            }
            if (ret != 0)
                throw new Win32Exception(LsaNtStatusToWinError((int)ret));
        }

        public string[] EnumerateAccountsWithUserRight(string privilege)
        {
            uint ret = 0;
            ulong count = 0;
            LSA_UNICODE_STRING[] rights = new LSA_UNICODE_STRING[1];
            rights[0] = InitLsaString(privilege);
            IntPtr buffer = IntPtr.Zero;

            ret = LsaEnumerateAccountsWithUserRight(lsaHandle, rights, out buffer, out count);
            switch (ret)
            {
                case 0:
                    string[] accounts = new string[count];
                    for (int i = 0; i < (int)count; i++)
                    {
                        LSA_ENUMERATION_INFORMATION LsaInfo = (LSA_ENUMERATION_INFORMATION)Marshal.PtrToStructure(
                            IntPtr.Add(buffer, i * Marshal.SizeOf(typeof(LSA_ENUMERATION_INFORMATION))),
                            typeof(LSA_ENUMERATION_INFORMATION));

                        accounts[i] = new SecurityIdentifier(LsaInfo.Sid).ToString();
                    }
                    LsaFreeMemory(buffer);
                    return accounts;

                case STATUS_NO_MORE_ENTRIES:
                    return new string[0];

                case STATUS_NO_SUCH_PRIVILEGE:
                    throw new ArgumentException(String.Format("Invalid privilege {0} not found in LSA database", privilege));

                default:
                    throw new Win32Exception(LsaNtStatusToWinError((int)ret));
            }
        }

        static LSA_UNICODE_STRING InitLsaString(string s)
        {
            // Unicode strings max. 32KB
            if (s.Length > 0x7ffe)
                throw new ArgumentException("String too long");

            LSA_UNICODE_STRING lus = new LSA_UNICODE_STRING();
            lus.Buffer = s;
            lus.Length = (ushort)(s.Length * sizeof(char));
            lus.MaximumLength = (ushort)(lus.Length + sizeof(char));

            return lus;
        }

        public void Dispose()
        {
            if (lsaHandle != IntPtr.Zero)
            {
                LsaClose(lsaHandle);
                lsaHandle = IntPtr.Zero;
            }
            GC.SuppressFinalize(this);
        }
        ~LsaRightHelper() { Dispose(); }
    }
}
"@

$original_tmp = $env:TMP
$original_temp = $env:TEMP
$env:TMP = $_remote_tmp
$env:TEMP = $_remote_tmp
Add-Type -TypeDefinition $sec_helper_util
$env:TMP = $original_tmp
$env:TEMP = $original_temp

Function Compare-UserList($existing_users, $new_users) {  
    $added_users = [String[]]@()
    $removed_users = [String[]]@()
    if ($action -eq "add") {
        $added_users = [Linq.Enumerable]::Except($new_users, $existing_users)
    } elseif ($action -eq "remove") {
        $removed_users = [Linq.Enumerable]::Intersect($new_users, $existing_users)
    } else {
        $added_users = [Linq.Enumerable]::Except($new_users, $existing_users)
        $removed_users = [Linq.Enumerable]::Except($existing_users, $new_users)
    }

    $change_result = @{
        added = $added_users
        removed = $removed_users
    }

    return $change_result
}

# C# class we can use to enumerate/add/remove rights
$lsa_helper = New-Object -TypeName Ansible.LsaRightHelper

$new_users = [System.Collections.ArrayList]@()
foreach ($user in $users) {
    $new_users.Add((Convert-ToSID -account_name $user))
}
$new_users = [String[]]$new_users.ToArray()
try {
    $existing_users = $lsa_helper.EnumerateAccountsWithUserRight($name)
} catch [ArgumentException] {
    Fail-Json -obj $result -message "the specified right $name is not a valid right"
} catch {
    Fail-Json -obj $result -message "failed to enumerate existing accounts with right: $($_.Exception.Message)"
}

$change_result = Compare-UserList -existing_users $existing_users -new_user $new_users
if (($change_result.added.Length -gt 0) -or ($change_result.removed.Length -gt 0)) {
    $result.changed = $true
    $diff_text = "[$name]`n"

    # used in diff mode calculation
    $new_user_list = [System.Collections.ArrayList]$existing_users
    foreach ($user in $change_result.removed) {
        if (-not $check_mode) {
            $lsa_helper.RemovePrivilege($user, $name)
        }
        $user_name = Convert-FromSID -sid $user
        $result.removed += $user_name
        $diff_text += "-$user_name`n"
        $new_user_list.Remove($user)
    }
    foreach ($user in $change_result.added) {
        if (-not $check_mode) {
            $lsa_helper.AddPrivilege($user, $name)
        }
        $user_name = Convert-FromSID -sid $user
        $result.added += $user_name
        $diff_text += "+$user_name`n"
        $new_user_list.Add($user)
    }
    
    if ($diff_mode) {
        if ($new_user_list.Count -eq 0) {
            $diff_text = "-$diff_text"
        } else {
            if ($existing_users.Count -eq 0) {
                $diff_text = "+$diff_text"
            }
        }
        $result.diff.prepared = $diff_text
    }
}

Exit-Json $result
