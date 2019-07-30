#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
using System.Linq;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.Principal;
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

        public enum TokenElevationType
        {
            TokenElevationTypeDefault = 1,
            TokenElevationTypeFull,
            TokenElevationTypeLimited
        }

        public enum TokenInformationClass
        {
            TokenUser = 1,
            TokenPrivileges = 3,
            TokenElevationType = 18,
            TokenLinkedToken = 19,
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct LUID
        {
            public UInt32 LowPart;
            public Int32 HighPart;

            public static explicit operator UInt64(LUID l)
            {
                return (UInt64)((UInt64)l.HighPart << 32) | (UInt64)l.LowPart;
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct LUID_AND_ATTRIBUTES
        {
            public LUID Luid;
            public UInt32 Attributes;
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

        [StructLayout(LayoutKind.Sequential)]
        public struct SID_AND_ATTRIBUTES
        {
            public IntPtr Sid;
            public UInt32 Attributes;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
            public LUID_AND_ATTRIBUTES[] Privileges;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_USER
        {
            public SID_AND_ATTRIBUTES User;
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool GetTokenInformation(
            SafeNativeHandle TokenHandle,
            NativeHelpers.TokenInformationClass TokenInformationClass,
            SafeMemoryBuffer TokenInformation,
            UInt32 TokenInformationLength,
            out UInt32 ReturnLength);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool ImpersonateLoggedOnUser(
            SafeNativeHandle hToken);

        [DllImport("kernel32.dll")]
        public static extern SafeNativeHandle GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupPrivilegeNameW(
            string lpSystemName,
            ref NativeHelpers.LUID lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern SafeNativeHandle OpenProcess(
            UInt32 dwDesiredAccess,
            bool bInheritHandle,
            UInt32 dwProcessId);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool OpenProcessToken(
            SafeNativeHandle ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out SafeNativeHandle TokenHandle);

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
        private SafeNativeHandle hToken = null;

        public Impersonation(SafeNativeHandle token)
        {
            hToken = token;
            if (token != null)
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

    public class SafeNativeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeNativeHandle() : base(true) { }
        public SafeNativeHandle(IntPtr handle) : base(true) { this.handle = handle; }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            return NativeMethods.CloseHandle(handle);
        }
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
        private const TokenAccessLevels IMPERSONATE_ACCESS = TokenAccessLevels.Query | TokenAccessLevels.Duplicate;
        private const UInt32 ERROR_SUCCESS = 0x00000000;
        private const UInt32 ERROR_NO_MORE_ITEMS = 0x0000103;

        public static void AddMappedDrive(string drive, string path, SafeNativeHandle iToken, string username = null, string password = null)
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

        public static List<DriveInfo> GetMappedDrives(SafeNativeHandle iToken)
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

        public static void RemoveMappedDrive(string drive, SafeNativeHandle iToken)
        {
            using (Impersonation imp = new Impersonation(iToken))
            {
                UInt32 res = NativeMethods.WNetCancelConnection2W(drive, NativeHelpers.CloseFlags.UpdateProfile, true);
                if (res != ERROR_SUCCESS)
                    throw new Win32Exception((int)res, String.Format("Failed to remove mapped drive {0} with WNetCancelConnection2W()", drive));
            }
        }

        public static SafeNativeHandle GetLimitedToken()
        {
            SafeNativeHandle hToken = null;
            if (!NativeMethods.OpenProcessToken(NativeMethods.GetCurrentProcess(), IMPERSONATE_ACCESS, out hToken))
                throw new Win32Exception("Failed to open current process token with OpenProcessToken()");

            using (hToken)
            {
                // Check the elevation type of the current token, only need to impersonate if it's a Full token
                using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenElevationType))
                {
                    NativeHelpers.TokenElevationType tet = (NativeHelpers.TokenElevationType)Marshal.ReadInt32(tokenInfo.DangerousGetHandle());

                    // If we don't have a Full token, we don't need to get the limited one to set a mapped drive
                    if (tet != NativeHelpers.TokenElevationType.TokenElevationTypeFull)
                        return null;
                }

                // We have a full token, need to get the TokenLinkedToken, this requires the SeTcbPrivilege privilege
                // and we can get that from impersonating a SYSTEM account token. Without this privilege we only get
                // an SecurityIdentification token which won't work for what we need
                using (SafeNativeHandle systemToken = GetSystemToken())
                using (Impersonation systemImpersonation = new Impersonation(systemToken))
                using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenLinkedToken))
                    return new SafeNativeHandle(Marshal.ReadIntPtr(tokenInfo.DangerousGetHandle()));
            }
        }

        private static SafeNativeHandle GetSystemToken()
        {
            foreach (System.Diagnostics.Process process in System.Diagnostics.Process.GetProcesses())
            {
                using (process)
                {
                    // 0x00000400 == PROCESS_QUERY_INFORMATION
                    using (SafeNativeHandle hProcess = NativeMethods.OpenProcess(0x00000400, false, (UInt32)process.Id))
                    {
                        if (hProcess.IsInvalid)
                            continue;

                        SafeNativeHandle hToken;
                        NativeMethods.OpenProcessToken(hProcess, IMPERSONATE_ACCESS, out hToken);
                        if (hToken.IsInvalid)
                            continue;

                        if ("S-1-5-18" == GetTokenUserSID(hToken))
                        {
                            // To get the TokenLinkedToken we need the SeTcbPrivilege, not all SYSTEM tokens have this
                            // assigned so we check before trying again
                            List<string> actualPrivileges = GetTokenPrivileges(hToken);
                            if (actualPrivileges.Contains("SeTcbPrivilege"))
                                return hToken;
                        }

                        hToken.Dispose();
                    }
                }
            }
            throw new InvalidOperationException("Failed to get a copy of the SYSTEM token required to de-elevate the current user's token");
        }

        private static List<string> GetTokenPrivileges(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenPrivileges))
            {
                NativeHelpers.TOKEN_PRIVILEGES tokenPrivileges = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(
                    tokenInfo.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_PRIVILEGES));

                NativeHelpers.LUID_AND_ATTRIBUTES[] luidAndAttributes = new NativeHelpers.LUID_AND_ATTRIBUTES[tokenPrivileges.PrivilegeCount];
                PtrToStructureArray(luidAndAttributes, IntPtr.Add(tokenInfo.DangerousGetHandle(), Marshal.SizeOf(tokenPrivileges.PrivilegeCount)));

                return luidAndAttributes.Select(x => GetPrivilegeName(x.Luid)).ToList();
            }
        }

        private static string GetTokenUserSID(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenUser))
            {
                NativeHelpers.TOKEN_USER tokenUser = (NativeHelpers.TOKEN_USER)Marshal.PtrToStructure(tokenInfo.DangerousGetHandle(),
                    typeof(NativeHelpers.TOKEN_USER));
                return new SecurityIdentifier(tokenUser.User.Sid).Value;
            }
        }

        private static SafeMemoryBuffer GetTokenInformation(SafeNativeHandle hToken, NativeHelpers.TokenInformationClass tokenClass)
        {
            UInt32 tokenLength;
            bool res = NativeMethods.GetTokenInformation(hToken, tokenClass, new SafeMemoryBuffer(IntPtr.Zero), 0, out tokenLength);
            if (!res && tokenLength == 0)  // res will be false due to insufficient buffer size, we ignore if we got the buffer length
                throw new Win32Exception(String.Format("GetTokenInformation({0}) failed to get buffer length", tokenClass.ToString()));

            SafeMemoryBuffer tokenInfo = new SafeMemoryBuffer((int)tokenLength);
            if (!NativeMethods.GetTokenInformation(hToken, tokenClass, tokenInfo, tokenLength, out tokenLength))
                throw new Win32Exception(String.Format("GetTokenInformation({0}) failed", tokenClass.ToString()));

            return tokenInfo;
        }

        private static string GetPrivilegeName(NativeHelpers.LUID luid)
        {
            UInt32 nameLen = 0;
            NativeMethods.LookupPrivilegeNameW(null, ref luid, null, ref nameLen);

            StringBuilder name = new StringBuilder((int)(nameLen + 1));
            if (!NativeMethods.LookupPrivilegeNameW(null, ref luid, name, ref nameLen))
                throw new Win32Exception("LookupPrivilegeNameW() failed");

            return name.ToString();
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
$impersonation_token = [Ansible.MappedDrive.Utils]::GetLimitedToken()

try {
    $existing_targets = [Ansible.MappedDrive.Utils]::GetMappedDrives($impersonation_token)
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
                [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root, $impersonation_token)
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
                    [Ansible.MappedDrive.Utils]::RemoveMappedDrive($letter_root, $impersonation_token)
                    $add_method.Invoke($null, [Object[]]@($letter_root, $path, $impersonation_token, $input_username, $input_password))
                }
                $module.Result.changed = $true
            }
        } else  {
            if (-not $module.CheckMode)  {
                $add_method.Invoke($null, [Object[]]@($letter_root, $path, $impersonation_token, $input_username, $input_password))
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
