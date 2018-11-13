#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        letter = @{ type = "str"; required = $true }
        path = @{ type = "path"; }
        state = @{ type = "str"; default = "present"; choices = "absent", "present" }
        username = @{ type = "str" }
        password = @{ type = "str"; no_log = $true }
    }
    required_if = @(
        ,@("state", "present", @("path"))
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$letter = $module.Params.letter
$path = $module.Params.path
$state = $module.Params.state
$username = $module.Params.username
$password = $module.Params.password

$result = @{
    changed = $false
}

if ($letter -notmatch "^[a-zA-z]{1}$") {
    $module.FailJson("letter must be a single letter from A-Z, was: $letter")
}

Add-CSharpType -AnsibleModule $module -References @'
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.MappedDrive
{
    internal class NativeHelpers
    {
        public enum ResourceScope : uint
        {
            Connected = 0x00000001,
            GlobalNet = 0x00000002,
            Remembered = 0x00000003,
            Recent = 0x00000004,
            Context = 0x00000005,
        }

        [Flags]
        public enum ResourceType : uint
        {
            Any = 0x0000000,
            Disk = 0x00000001,
            Print = 0x00000002,
            Reserved = 0x00000008,
            Unknown = 0xFFFFFFFF,
        }

        public enum CloseFlags : uint
        {
            None = 0x00000000,
            UpdateProfile = 0x00000001,
        }

        [Flags]
        public enum ResourceUsage : uint
        {
            All = 0x00000000,
            Connectable = 0x00000001,
            Container = 0x00000002,
            NoLocalDevice = 0x00000004,
            Sibling = 0x00000008,
            Attached = 0x00000010,
        }

        [Flags]
        public enum AddFlags : uint
        {
            UpdateProfile = 0x00000001,
            UpdateRecent = 0x00000002,
            Temporary = 0x00000004,
            Interactive = 0x00000008,
            Prompt = 0x00000010,
            Redirect = 0x00000080,
            CurrentMedia = 0x00000200,
            CommandLine = 0x00000800,
            CmdSaveCred = 0x00001000,
            CredReset = 0x00002000,
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct NETRESOURCEW
        {
            public ResourceScope dwScope;
            public ResourceType dwType;
            public UInt32 dwDisplayType;
            public ResourceUsage dwUsage;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpLocalName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpRemoteName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpComment;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpProvider;
        }
    }

    internal class NativeMethods
    {
        [DllImport("Mpr.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 WNetAddConnection2W(
            NativeHelpers.NETRESOURCEW lpNetResource,
            [MarshalAs(UnmanagedType.LPWStr)] string lpPassword,
            [MarshalAs(UnmanagedType.LPWStr)] string lpUserName,
            NativeHelpers.AddFlags dwFlags);

        [DllImport("Mpr.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 WNetCancelConnection2W(
            [MarshalAs(UnmanagedType.LPWStr)] string lpName,
            NativeHelpers.CloseFlags dwFlags,
            bool fForce);

        [DllImport("Mpr.dll")]
        public static extern UInt32 WNetCloseEnum(
            IntPtr hEnum);

        [DllImport("Mpr.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 WNetEnumResourceW(
            IntPtr hEnum,
            ref Int32 lpcCount,
            IntPtr lpBuffer,
            ref UInt32 lpBufferSize);

        [DllImport("Mpr.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 WNetOpenEnumW(
            NativeHelpers.ResourceScope dwScope,
            NativeHelpers.ResourceType dwType,
            NativeHelpers.ResourceUsage dwUsage,
            IntPtr lpNetResource,
            out IntPtr lphEnum);
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;
        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2})", message, base.Message, errorCode);
        }
        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public class DriveInfo
    {
        public string Drive;
        public string Path;
        public string Username;
    }

    public class Utils
    {
        private const UInt32 ERROR_SUCCESS = 0x00000000;
        private const UInt32 ERROR_NO_MORE_ITEMS = 0x0000103;

        public static void AddMappedDrive(string drive, string path, string username = null, string password = null)
        {
            NativeHelpers.NETRESOURCEW resource = new NativeHelpers.NETRESOURCEW
            {
                dwType = NativeHelpers.ResourceType.Disk,
                lpLocalName = drive,
                lpRemoteName = path,
            };
            NativeHelpers.AddFlags dwFlags = NativeHelpers.AddFlags.UpdateProfile;
            UInt32 res = NativeMethods.WNetAddConnection2W(resource, password, username, dwFlags);
            if (res != ERROR_SUCCESS)
                throw new Win32Exception((int)res, String.Format("Failed to map {0} to '{1}' with WNetAddConnection2W()", drive, path));
        }

        public static List<DriveInfo> GetMappedDrives()
        {
            IntPtr enumPtr = IntPtr.Zero;
            UInt32 res = NativeMethods.WNetOpenEnumW(NativeHelpers.ResourceScope.Remembered, NativeHelpers.ResourceType.Disk,
                NativeHelpers.ResourceUsage.All, IntPtr.Zero, out enumPtr);
            if (res != ERROR_SUCCESS)
                throw new Win32Exception((int)res, "WNetOpenEnumW()");

            List<DriveInfo> resources = new List<DriveInfo>();
            try
            {
                // MS recommend a buffer size of 16 KiB
                UInt32 bufferSize = 16384;
                int lpcCount = -1;

                // keep iterating the enum until ERROR_NO_MORE_ITEMS is returned
                do
                {
                    IntPtr buffer = Marshal.AllocHGlobal((int)bufferSize);
                    try
                    {
                        res = NativeMethods.WNetEnumResourceW(enumPtr, ref lpcCount, buffer, ref bufferSize);
                        if (res != ERROR_SUCCESS && res != ERROR_NO_MORE_ITEMS)
                            throw new Win32Exception((int)res, "WNetEnumResourceW()");

                        NativeHelpers.NETRESOURCEW[] rawResources = new NativeHelpers.NETRESOURCEW[lpcCount];
                        PtrToStructureArray(rawResources, buffer);
                        foreach (NativeHelpers.NETRESOURCEW resource in rawResources)
                        {
                            DriveInfo currentDrive = new DriveInfo
                            {
                                Drive = resource.lpLocalName,
                                Path = resource.lpRemoteName,
                                Username = GetUsernameForDrive(resource.lpLocalName),
                            };
                            resources.Add(currentDrive);
                        }
                    }
                    finally
                    {
                        Marshal.FreeHGlobal(buffer);
                    }
                }
                while (res != ERROR_NO_MORE_ITEMS);
            }
            finally
            {
                NativeMethods.WNetCloseEnum(enumPtr);
            }

            return resources;
        }

        public static void RemoveMappedDrive(string drive)
        {
            UInt32 res = NativeMethods.WNetCancelConnection2W(drive, NativeHelpers.CloseFlags.UpdateProfile, true);
            if (res != ERROR_SUCCESS)
                throw new Win32Exception((int)res, String.Format("Failed to remove mapped drive {0} with WNetCancelConnection2W()", drive));
        }

        private static string GetUsernameForDrive(string drive)
        {
            // WNetGetUser only get's the user the provider will use and not what was configured, we will just
            // go straight to the source to get the UserName that's configured.
            using (RegistryKey key = Registry.CurrentUser.OpenSubKey(String.Format("Network\\{0}", drive.Substring(0, 1))))
            {
                string username = (string)key.GetValue("UserName", "");
                // An empty string means no username is set, return null for PS comparison
                return username == "" ? null : username;
            }
        }

        private static void PtrToStructureArray<T>(T[] array, IntPtr ptr)
        {
            IntPtr ptrOffset = ptr;
            for (int i = 0; i < array.Length; i++, ptrOffset = IntPtr.Add(ptrOffset, Marshal.SizeOf(typeof(T))))
                array[i] = (T)Marshal.PtrToStructure(ptrOffset, typeof(T));
        }
    }
}
'@

$letter_root = "$($letter):"
$existing_targets = [Ansible.MappedDrive.Utils]::GetMappedDrives()
$existing_target = $existing_targets | Where-Object { $_.Drive -eq $letter_root }

$module.Diff.before = ""
$module.Diff.after = ""
if ($existing_target) {
    $module.Diff.before = @{
        letter = $letter
        path = $existing_target.Path
        username = $existing_target.Username
    }
}

if ($state -eq "absent") {
    if ($existing_target -ne $null) {
        if ($null -ne $path) {
            if ($existing_target.Path -eq $path) {
                if (-not $module.CheckMode) {
                    [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root)
                }
            } else {
                $module.FailJson("did not delete mapped drive $letter, the target path is pointing to a different location at $($existing_target.Path)")
            }
        } else {
            if (-not $module.CheckMode) {
                [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root)
            }
        }

        $module.Result.changed = $true
    }
} else {
    $physical_drives = Get-PSDrive -PSProvider "FileSystem"
    if ($letter -in $physical_drives.Name) {
        $module.FailJson("failed to create mapped drive $letter, this letter is in use and is pointing to a non UNC path")
    }

    # PowerShell converts a $null value to "" when crossing the .NET marshaler, we need to convert the input
    # to a missing value so it uses the defaults. We also need to Invoke it with MethodInfo.Invoke so the defaults
    # are still used
    $input_username = $username
    if ($null -eq $username) {
        $input_username = [Type]::Missing
    }
    $input_password = $password
    if ($null -eq $password) {
        $input_password = [Type]::Missing
    }
    $add_method = [Ansible.MappedDrive.Utils].GetMethod("AddMappedDrive")

    if ($null -ne $existing_target) {
        if ($existing_target.Path -ne $path) {
            if (-not $module.CheckMode) {
                [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root)
            }
            $module.Result.changed = $true

            if (-not $module.CheckMode) {
                $add_method.Invoke($null, [Object[]]@($letter_root, $path, $input_username, $input_password) )
            }
        } elseif ($username -ne $existing_target.Username) {
            Set-ItemProperty -Path HKCU:\Network\$letter -Name UserName -Value $username -WhatIf:$module.CheckMode
            $module.Result.changed = $true
        }
    } else {
        if (-not $module.CheckMode) {
            $add_method.Invoke($null, [Object[]]@($letter_root, $path, $input_username, $input_password) )
        }

        $module.Result.changed = $true
    }
    $module.Diff.after = @{
        letter = $letter
        path = $path
        username = $username
    }
}

$module.ExitJson()
