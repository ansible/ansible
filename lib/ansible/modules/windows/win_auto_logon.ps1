#!powershell

# Copyright: (c) 2019, Prasoon Karunan V (@prasoonkarunan) <kvprasoon@Live.in>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# All helper methods are written in a binary module and has to be loaded for consuming them.
#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

Set-StrictMode -Version 2.0

$spec = @{
    options = @{
        logon_count = @{type = "int"}
        password = @{type = "str"; no_log = $true}
        state = @{type = "str"; choices = "absent", "present"; default = "present"}
        username = @{type = "str"}
    }
    required_if = @(
        ,@("state", "present", @("username", "password"))
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$logonCount = $module.Params.logon_count
$password = $module.Params.password
$state = $module.Params.state
$username = $module.Params.username
$domain = $null

if ($username) {
    # Try and get the Netlogon form of the username specified. Translating to and from a SID gives us an NTAccount
    # in the Netlogon form that we desire.
    $ntAccount = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $username
    try {
        $accountSid = $ntAccount.Translate([System.Security.Principal.SecurityIdentifier])
    } catch [System.Security.Principal.IdentityNotMappedException] {
        $module.FailJson("Failed to find a local or domain user with the name '$username'", $_)
    }
    $ntAccount = $accountSid.Translate([System.Security.Principal.NTAccount])

    $domain, $username = $ntAccount.Value -split '\\'
}

# Make sure $null regardless of any input value if state: absent
if ($state -eq 'absent') {
    $password = $null
}

Add-CSharpType -AnsibleModule $module -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.WinAutoLogon
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public class LSA_OBJECT_ATTRIBUTES
        {
            public UInt32 Length = 0;
            public IntPtr RootDirectory = IntPtr.Zero;
            public IntPtr ObjectName = IntPtr.Zero;
            public UInt32 Attributes = 0;
            public IntPtr SecurityDescriptor = IntPtr.Zero;
            public IntPtr SecurityQualityOfService = IntPtr.Zero;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        internal struct LSA_UNICODE_STRING
        {
            public UInt16 Length;
            public UInt16 MaximumLength;
            public IntPtr Buffer;

            public static explicit operator string(LSA_UNICODE_STRING s)
            {
                byte[] strBytes = new byte[s.Length];
                Marshal.Copy(s.Buffer, strBytes, 0, s.Length);
                return Encoding.Unicode.GetString(strBytes);
            }

            public static SafeMemoryBuffer CreateSafeBuffer(string s)
            {
                if (s == null)
                    return new SafeMemoryBuffer(IntPtr.Zero);

                byte[] stringBytes = Encoding.Unicode.GetBytes(s);
                int structSize = Marshal.SizeOf(typeof(LSA_UNICODE_STRING));
                IntPtr buffer = Marshal.AllocHGlobal(structSize + stringBytes.Length);
                try
                {
                    LSA_UNICODE_STRING lsaString = new LSA_UNICODE_STRING()
                    {
                        Length = (UInt16)(stringBytes.Length),
                        MaximumLength = (UInt16)(stringBytes.Length),
                        Buffer = IntPtr.Add(buffer, structSize),
                    };
                    Marshal.StructureToPtr(lsaString, buffer, false);
                    Marshal.Copy(stringBytes, 0, lsaString.Buffer, stringBytes.Length);
                    return new SafeMemoryBuffer(buffer);
                }
                catch
                {
                    // Make sure we free the pointer before raising the exception.
                    Marshal.FreeHGlobal(buffer);
                    throw;
                }
            }
        }
    }

    internal class NativeMethods
    {
        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaClose(
            IntPtr ObjectHandle);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaFreeMemory(
            IntPtr Buffer);

        [DllImport("Advapi32.dll")]
        internal static extern Int32 LsaNtStatusToWinError(
            UInt32 Status);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaOpenPolicy(
            IntPtr SystemName,
            NativeHelpers.LSA_OBJECT_ATTRIBUTES ObjectAttributes,
            LsaPolicyAccessMask AccessMask,
            out SafeLsaHandle PolicyHandle);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaRetrievePrivateData(
            SafeLsaHandle PolicyHandle,
            SafeMemoryBuffer KeyName,
            out SafeLsaMemory PrivateData);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaStorePrivateData(
            SafeLsaHandle PolicyHandle,
            SafeMemoryBuffer KeyName,
            SafeMemoryBuffer PrivateData);
    }

    internal class SafeLsaMemory : SafeBuffer
    {
        internal SafeLsaMemory() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            return NativeMethods.LsaFreeMemory(handle) == 0;
        }
    }

    internal class SafeMemoryBuffer : SafeBuffer
    {
        internal SafeMemoryBuffer() : base(true) { }

        internal SafeMemoryBuffer(IntPtr ptr) : base(true)
        {
            base.SetHandle(ptr);
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            if (handle != IntPtr.Zero)
                Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    public class SafeLsaHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        internal SafeLsaHandle() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            return NativeMethods.LsaClose(handle) == 0;
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _exception_msg;
        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _exception_msg = String.Format("{0} - {1} (Win32 Error Code {2}: 0x{3})", message, base.Message, errorCode, errorCode.ToString("X8"));
        }
        public override string Message { get { return _exception_msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    [Flags]
    public enum LsaPolicyAccessMask : uint
    {
        ViewLocalInformation = 0x00000001,
        ViewAuditInformation = 0x00000002,
        GetPrivateInformation = 0x00000004,
        TrustAdmin = 0x00000008,
        CreateAccount = 0x00000010,
        CreateSecret = 0x00000020,
        CreatePrivilege = 0x00000040,
        SetDefaultQuotaLimits = 0x00000080,
        SetAuditRequirements = 0x00000100,
        AuditLogAdmin = 0x00000200,
        ServerAdmin = 0x00000400,
        LookupNames = 0x00000800,
        Read = 0x00020006,
        Write = 0x000207F8,
        Execute = 0x00020801,
        AllAccess = 0x000F0FFF,
    }

    public class LsaUtil
    {
        public static SafeLsaHandle OpenPolicy(LsaPolicyAccessMask access)
        {
            NativeHelpers.LSA_OBJECT_ATTRIBUTES oa = new NativeHelpers.LSA_OBJECT_ATTRIBUTES();
            SafeLsaHandle lsaHandle;
            UInt32 res = NativeMethods.LsaOpenPolicy(IntPtr.Zero, oa, access, out lsaHandle);
            if (res != 0)
                throw new Win32Exception(NativeMethods.LsaNtStatusToWinError(res),
                    String.Format("LsaOpenPolicy({0}) failed", access.ToString()));
            return lsaHandle;
        }

        public static string RetrievePrivateData(SafeLsaHandle handle, string key)
        {
            using (SafeMemoryBuffer keyBuffer = NativeHelpers.LSA_UNICODE_STRING.CreateSafeBuffer(key))
            {
                SafeLsaMemory buffer;
                UInt32 res = NativeMethods.LsaRetrievePrivateData(handle, keyBuffer, out buffer);
                using (buffer)
                {
                    if (res != 0)
                    {
                        // If the data object was not found we return null to indicate it isn't set.
                        if (res == 0xC0000034)  // STATUS_OBJECT_NAME_NOT_FOUND
                            return null;

                        throw new Win32Exception(NativeMethods.LsaNtStatusToWinError(res),
                            String.Format("LsaRetrievePrivateData({0}) failed", key));
                    }

                    NativeHelpers.LSA_UNICODE_STRING lsaString = (NativeHelpers.LSA_UNICODE_STRING)
                        Marshal.PtrToStructure(buffer.DangerousGetHandle(),
                        typeof(NativeHelpers.LSA_UNICODE_STRING));
                    return (string)lsaString;
                }
            }
        }

        public static void StorePrivateData(SafeLsaHandle handle, string key, string data)
        {
            using (SafeMemoryBuffer keyBuffer = NativeHelpers.LSA_UNICODE_STRING.CreateSafeBuffer(key))
            using (SafeMemoryBuffer dataBuffer = NativeHelpers.LSA_UNICODE_STRING.CreateSafeBuffer(data))
            {
                UInt32 res = NativeMethods.LsaStorePrivateData(handle, keyBuffer, dataBuffer);
                if (res != 0)
                {
                    // When clearing the private data with null it may return this error which we can ignore.
                    if (data == null && res == 0xC0000034)  // STATUS_OBJECT_NAME_NOT_FOUND
                        return;

                    throw new Win32Exception(NativeMethods.LsaNtStatusToWinError(res),
                        String.Format("LsaStorePrivateData({0}) failed", key));
                }
            }
        }
    }
}
'@

$autoLogonRegPath = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
$logonDetails = Get-ItemProperty -LiteralPath $autoLogonRegPath

$before = @{
    state = 'absent'
}
if ('AutoAdminLogon' -in $logonDetails.PSObject.Properties.Name -and $logonDetails.AutoAdminLogon -eq 1) {
    $before.state = 'present'
}

$mapping = @{
    DefaultUserName = 'username'
    DefaultDomainName = 'domain'
    AutoLogonCount = 'logon_count'
}
foreach ($map_detail in $mapping.GetEnumerator()) {
    if ($map_detail.Key -in $logonDetails.PSObject.Properties.Name) {
        $before."$($map_detail.Value)" = $logonDetails."$($map_detail.Key)"
    }
}

$module.Diff.before = $before

$propParams = @{
    LiteralPath = $autoLogonRegPath
    WhatIf = $module.CheckMode
    Force = $true
}

# First set the registry information
# The DefaultPassword reg key should never be set, we use LSA to store the password in a more secure way.
if ('DefaultPassword' -in (Get-Item -LiteralPath $autoLogonRegPath).Property) {
    # Bug on older Windows hosts where -WhatIf causes it fail to find the property
    if (-not $module.CheckMode) {
        Remove-ItemProperty -Name 'DefaultPassword' @propParams
    }
    $module.Result.changed = $true
}

$autoLogonKeyList = @{
    DefaultUserName = @{
        before = if ($before.ContainsKey('username')) { $before.username } else { $null }
        after = $username
    }
    DefaultDomainName = @{
        before = if ($before.ContainsKey('domain')) { $before.domain } else { $null }
        after = $domain
    }
    AutoLogonCount = @{
        before = if ($before.ContainsKey('logon_count')) { $before.logon_count } else { $null }
        after = $logonCount
    }
}

# Check AutoAdminLogon separately as it has different logic (key must exist)
if ($state -ne $before.state) {
    $newValue = if ($state -eq 'present') { 1 } else { 0 }
    $null = New-ItemProperty -Name 'AutoAdminLogon' -Value $newValue -PropertyType DWord @propParams
    $module.Result.changed = $true
}

foreach ($key in $autoLogonKeyList.GetEnumerator()) {
    $beforeVal = $key.Value.before
    $after = $key.Value.after

    if ($state -eq 'present' -and $beforeVal -cne $after) {
        if ($null -ne $after) {
            $null = New-ItemProperty -Name $key.Key -Value $after @propParams
        }
        elseif (-not $module.CheckMode) {
            Remove-ItemProperty -Name $key.Key @propParams
        }
        $module.Result.changed = $true
    }
    elseif ($state -eq 'absent' -and $null -ne $beforeVal) {
        if (-not $module.CheckMode) {
            Remove-ItemProperty -Name $key.Key @propParams
        }
        $module.Result.changed = $true
    }
}

# Finally update the password in the LSA private store.
$lsaHandle = [Ansible.WinAutoLogon.LsaUtil]::OpenPolicy('CreateSecret, GetPrivateInformation')
try {
    $beforePass = [Ansible.WinAutoLogon.LsaUtil]::RetrievePrivateData($lsaHandle, 'DefaultPassword')

    if ($beforePass -cne $password) {
        # Due to .NET marshaling we need to pass in $null as NullString.Value so it's truly a null value.
        if ($null -eq $password) {
            $password = [NullString]::Value
        }
        if (-not $module.CheckMode) {
            [Ansible.WinAutoLogon.LsaUtil]::StorePrivateData($lsaHandle, 'DefaultPassword', $password)
        }
        $module.Result.changed = $true
    }
}
finally {
    $lsaHandle.Dispose()
}

# Need to manually craft the after diff in case we are running in check mode
$module.Diff.after = @{
    state = $state
}
if ($state -eq 'present') {
    $module.Diff.after.username = $username
    $module.Diff.after.domain = $domain
    if ($null -ne $logonCount) {
        $module.Diff.after.logon_count = $logonCount
    }
}

$module.ExitJson()

