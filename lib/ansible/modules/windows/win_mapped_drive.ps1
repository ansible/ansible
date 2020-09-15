#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.AccessToken
#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        letter = @{ type = "str"; required = $true }
        path = @{ type = "path"; }
        state = @{ type = "str"; default = "present"; choices = @("absent", "present") }
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

if ($letter -notmatch "^[a-zA-z]{1}$") {
    $module.FailJson("letter must be a single letter from A-Z, was: $letter")
}
$letter_root = "$($letter):"

$module.Diff.before = ""
$module.Diff.after = ""

Add-CSharpType -AnsibleModule $module -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;

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
            public UInt32 dwUsage;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpLocalName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpRemoteName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpComment;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpProvider;
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool ImpersonateLoggedOnUser(
            IntPtr hToken);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool RevertToSelf();

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
            SafeMemoryBuffer lpBuffer,
            ref UInt32 lpBufferSize);

        [DllImport("Mpr.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 WNetOpenEnumW(
            NativeHelpers.ResourceScope dwScope,
            NativeHelpers.ResourceType dwType,
            UInt32 dwUsage,
            IntPtr lpNetResource,
            out IntPtr lphEnum);
    }

    internal class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeMemoryBuffer() : base(true) { }
        public SafeMemoryBuffer(int cb) : base(true)
        {
            base.SetHandle(Marshal.AllocHGlobal(cb));
        }
        public SafeMemoryBuffer(IntPtr handle) : base(true)
        {
            base.SetHandle(handle);
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    internal class Impersonation : IDisposable
    {
        private IntPtr hToken = IntPtr.Zero;

        public Impersonation(IntPtr token)
        {
            hToken = token;
            if (token != IntPtr.Zero)
                if (!NativeMethods.ImpersonateLoggedOnUser(hToken))
                    throw new Win32Exception("Failed to impersonate token with ImpersonateLoggedOnUser()");
        }

        public void Dispose()
        {
            if (hToken != null)
                NativeMethods.RevertToSelf();
            GC.SuppressFinalize(this);
        }
        ~Impersonation() { Dispose(); }
    }

    public class DriveInfo
    {
        public string Drive;
        public string Path;
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

    public class Utils
    {
        private const UInt32 ERROR_SUCCESS = 0x00000000;
        private const UInt32 ERROR_NO_MORE_ITEMS = 0x0000103;

        public static void AddMappedDrive(string drive, string path, IntPtr iToken, string username = null, string password = null)
        {
            NativeHelpers.NETRESOURCEW resource = new NativeHelpers.NETRESOURCEW
            {
                dwType = NativeHelpers.ResourceType.Disk,
                lpLocalName = drive,
                lpRemoteName = path,
            };
            NativeHelpers.AddFlags dwFlags = NativeHelpers.AddFlags.UpdateProfile;
            // While WNetAddConnection2W supports user/pass, this is only used for the first connection and the
            // password is not remembered. We will delete the username mapping afterwards as it interferes with
            // the implicit credential cache used in Windows
            using (Impersonation imp = new Impersonation(iToken))
            {
                UInt32 res = NativeMethods.WNetAddConnection2W(resource, password, username, dwFlags);
                if (res != ERROR_SUCCESS)
                    throw new Win32Exception((int)res, String.Format("Failed to map {0} to '{1}' with WNetAddConnection2W()", drive, path));
            }
        }

        public static List<DriveInfo> GetMappedDrives(IntPtr iToken)
        {
            using (Impersonation imp = new Impersonation(iToken))
            {
                IntPtr enumPtr = IntPtr.Zero;
                UInt32 res = NativeMethods.WNetOpenEnumW(NativeHelpers.ResourceScope.Remembered, NativeHelpers.ResourceType.Disk,
                    0, IntPtr.Zero, out enumPtr);
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
                        using (SafeMemoryBuffer buffer = new SafeMemoryBuffer((int)bufferSize))
                        {
                            res = NativeMethods.WNetEnumResourceW(enumPtr, ref lpcCount, buffer, ref bufferSize);
                            if (res == ERROR_NO_MORE_ITEMS)
                                continue;
                            else if (res != ERROR_SUCCESS)
                                throw new Win32Exception((int)res, "WNetEnumResourceW()");
                            lpcCount = lpcCount < 0 ? 0 : lpcCount;

                            NativeHelpers.NETRESOURCEW[] rawResources = new NativeHelpers.NETRESOURCEW[lpcCount];
                            PtrToStructureArray(rawResources, buffer.DangerousGetHandle());
                            foreach (NativeHelpers.NETRESOURCEW resource in rawResources)
                            {
                                DriveInfo currentDrive = new DriveInfo
                                {
                                    Drive = resource.lpLocalName,
                                    Path = resource.lpRemoteName,
                                };
                                resources.Add(currentDrive);
                            }
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
        }

        public static void RemoveMappedDrive(string drive, IntPtr iToken)
        {
            using (Impersonation imp = new Impersonation(iToken))
            {
                UInt32 res = NativeMethods.WNetCancelConnection2W(drive, NativeHelpers.CloseFlags.UpdateProfile, true);
                if (res != ERROR_SUCCESS)
                    throw new Win32Exception((int)res, String.Format("Failed to remove mapped drive {0} with WNetCancelConnection2W()", drive));
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

Function Get-LimitedToken {
    $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
    $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Duplicate, Query")

    try {
        # If we don't have a Full token, we don't need to get the limited one to set a mapped drive
        $tet = [Ansible.AccessToken.TokenUtil]::GetTokenElevationType($h_token)
        if ($tet -ne [Ansible.AccessToken.TokenElevationType]::Full) {
            return
        }

        foreach ($system_token in [Ansible.AccessToken.TokenUtil]::EnumerateUserTokens("S-1-5-18", "Duplicate")) {
            # To get the TokenLinkedToken we need the SeTcbPrivilege, not all SYSTEM tokens have this assigned so
            # we need to check before impersonating that token
            $token_privileges = [Ansible.AccessToken.TokenUtil]::GetTokenPrivileges($system_token)
            if ($null -eq ($token_privileges | Where-Object { $_.Name -eq "SeTcbPrivilege" })) {
                continue
            }

            [Ansible.AccessToken.TokenUtil]::ImpersonateToken($system_token)
            try {
                return [Ansible.AccessToken.TokenUtil]::GetTokenLinkedToken($h_token)
            } finally {
                [Ansible.AccessToken.TokenUtil]::RevertToSelf()
            }
        }
    } finally {
        $h_token.Dispose()
    }
}

<#
When we run with become and UAC is enabled, the become process will most likely be the Admin/Full token. This is
an issue with the WNetConnection APIs as the Full token is unable to add/enumerate/remove connections due to
Windows storing the connection details on each token session ID. Unless EnabledLinkedConnections (reg key) is
set to 1, the Full token is unable to manage connections in a persisted way whereas the Limited token is. This
is similar to running 'net use' normally and an admin process is unable to see those and vice versa.

To overcome this problem, we attempt to get a handle on the Limited token for the current logon and impersonate
that before making any WNetConnection calls. If the token is not split, or we are already running on the Limited
token then no impersonatoin is used/required. This allows the module to run with become (required to access the
credential store) but still be able to manage the mapped connections.

These are the following scenarios we have to handle;

    1. Run without become
        A network logon is usually not split so GetLimitedToken() will return $null and no impersonation is needed
    2. Run with become on admin user with admin priv
        We will have a Full token, GetLimitedToken() will return the limited token and impersonation is used
    3. Run with become on admin user without admin priv
        We are already running with a Limited token, GetLimitedToken() return $nul and no impersonation is needed
    4. Run with become on standard user
        There's no split token, GetLimitedToken() will return $null and no impersonation is needed
#>
$impersonation_token = Get-LimitedToken

try {
    $i_token_ptr = [System.IntPtr]::Zero
    if ($null -ne $impersonation_token) {
        $i_token_ptr = $impersonation_token.DangerousGetHandle()
    }

    $existing_targets = [Ansible.MappedDrive.Utils]::GetMappedDrives($i_token_ptr)
    $existing_target = $existing_targets | Where-Object { $_.Drive -eq $letter_root }

    if ($existing_target) {
        $module.Diff.before = @{
            letter = $letter
            path = $existing_target.Path
        }
    }

    if ($state -eq "absent") {
        if ($null -ne $existing_target) {
            if ($null -ne $path -and $existing_target.Path -ne $path) {
                $module.FailJson("did not delete mapped drive $letter, the target path is pointing to a different location at $( $existing_target.Path )")
            }
            if (-not $module.CheckMode) {
                [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root, $i_token_ptr)
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
                    [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root, $i_token_ptr)
                    $add_method.Invoke($null, [Object[]]@($letter_root, $path, $i_token_ptr, $input_username, $input_password))
                }
                $module.Result.changed = $true
            }
        } else  {
            if (-not $module.CheckMode)  {
                $add_method.Invoke($null, [Object[]]@($letter_root, $path, $i_token_ptr, $input_username, $input_password))
            }

            $module.Result.changed = $true
        }

        # If username was set and we made a change, remove the UserName value so Windows will continue to use the cred
        # cache. If we don't do this then the drive will fail to map in the future as WNetAddConnection does not cache
        # the password and relies on the credential store.
        if ($null -ne $username -and $module.Result.changed -and -not $module.CheckMode) {
            Set-ItemProperty -Path HKCU:\Network\$letter -Name UserName -Value "" -WhatIf:$module.CheckMode
        }

        $module.Diff.after = @{
            letter = $letter
            path = $path
        }
    }
} finally {
    if ($null -ne $impersonation_token) {
        $impersonation_token.Dispose()
    }
}

$module.ExitJson()
