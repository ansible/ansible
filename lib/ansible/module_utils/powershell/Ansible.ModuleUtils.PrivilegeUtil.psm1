# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# store in separate variables to make it easier for other module_utils to
# share this code in their own c# code
$ansible_privilege_util_namespaces = @(
    "Microsoft.Win32.SafeHandles",
    "System",
    "System.Collections.Generic",
    "System.Runtime.InteropServices",
    "System.Security.Principal",
    "System.Text"
)

$ansible_privilege_util_code = @'
namespace Ansible.PrivilegeUtil
{
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

    public class NativeHelpers
    {
        [Flags]
        public enum PrivilegeAttributes : uint
        {
            Disabled = 0x00000000,
            EnabledByDefault = 0x00000001,
            Enabled = 0x00000002,
            Removed = 0x00000004,
            UsedForAccess = 0x80000000,
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct LUID
        {
            public UInt32 LowPart;
            public Int32 HighPart;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct LUID_AND_ATTRIBUTES
        {
            public LUID Luid;
            public PrivilegeAttributes Attributes;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
            public LUID_AND_ATTRIBUTES[] Privileges;
        }
    }

    internal class NativeMethods
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool AdjustTokenPrivileges(
            IntPtr TokenHandle,
            [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
            IntPtr NewState,
            UInt32 BufferLength,
            IntPtr PreviousState,
            out UInt32 ReturnLength);

        [DllImport("kernel32.dll")]
        internal static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("kernel32")]
        internal static extern SafeWaitHandle GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetTokenInformation(
            IntPtr TokenHandle,
            UInt32 TokenInformationClass,
            IntPtr TokenInformation,
            UInt32 TokenInformationLength,
            out UInt32 ReturnLength);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool LookupPrivilegeName(
            string lpSystemName,
            ref NativeHelpers.LUID lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool LookupPrivilegeValue(
            string lpSystemName,
            string lpName,
            out NativeHelpers.LUID lpLuid);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool OpenProcessToken(
            SafeHandle ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out IntPtr TokenHandle);
    }

    public class Helpers
    {
        private static readonly UInt32 TOKEN_PRIVILEGES = 3;

        public static bool CheckPrivilegeName(string name)
        {
            NativeHelpers.LUID luid;
            if (!NativeMethods.LookupPrivilegeValue(null, name, out luid))
            {
                int errCode = Marshal.GetLastWin32Error();
                if (errCode != 1313)  // ERROR_NO_SUCH_PRIVILEGE
                    throw new Win32Exception(errCode, String.Format("LookupPrivilegeValue({0}) failed", name));
                return false;
            }
            else
            {
                return true;
            }
        }

        public static Dictionary<string, bool?> DisablePrivilege(SafeHandle token, string privilege)
        {
            return SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, false } });
        }

        public static Dictionary<string, bool?> DisableAllPrivileges(SafeHandle token)
        {
            return AdjustTokenPrivileges(token, null);
        }

        public static Dictionary<string, bool?> EnablePrivilege(SafeHandle token, string privilege)
        {
            return SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, true } });
        }

        public static Dictionary<String, NativeHelpers.PrivilegeAttributes> GetAllPrivilegeInfo(SafeHandle token)
        {
            IntPtr hToken = IntPtr.Zero;
            if (!NativeMethods.OpenProcessToken(token, TokenAccessLevels.Query, out hToken))
                throw new Win32Exception("OpenProcessToken() failed");

            Dictionary<String, NativeHelpers.PrivilegeAttributes> info = new Dictionary<String, NativeHelpers.PrivilegeAttributes>();
            try
            {
                UInt32 tokenLength = 0;
                NativeMethods.GetTokenInformation(hToken, TOKEN_PRIVILEGES, IntPtr.Zero, 0, out tokenLength);
                IntPtr privilegesPtr = Marshal.AllocHGlobal((int)tokenLength);

                if (!NativeMethods.GetTokenInformation(hToken, TOKEN_PRIVILEGES, privilegesPtr, tokenLength, out tokenLength))
                    throw new Win32Exception("GetTokenInformation() for TOKEN_PRIVILEGES failed");

                NativeHelpers.TOKEN_PRIVILEGES privilegeInfo = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(privilegesPtr, typeof(NativeHelpers.TOKEN_PRIVILEGES));
                NativeHelpers.LUID_AND_ATTRIBUTES[] privileges = new NativeHelpers.LUID_AND_ATTRIBUTES[privilegeInfo.PrivilegeCount];
                try
                {
                    PtrToStructureArray(privileges, privilegesPtr.ToInt64() + Marshal.SizeOf(privilegeInfo.PrivilegeCount));
                }
                finally
                {
                    Marshal.FreeHGlobal(privilegesPtr);
                }

                foreach (NativeHelpers.LUID_AND_ATTRIBUTES privilege in privileges)
                {
                    string name = GetPrivilegeName(privilege.Luid);
                    info.Add(name, privilege.Attributes);
                }
            }
            finally
            {
                NativeMethods.CloseHandle(hToken);
            }
            return info;
        }

        public static SafeWaitHandle GetCurrentProcess()
        {
            return NativeMethods.GetCurrentProcess();
        }

        public static void RemovePrivilege(SafeHandle token, string privilege)
        {
            SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, null } });
        }

        public static Dictionary<string, bool?> SetTokenPrivileges(SafeHandle token, Dictionary<string, bool?> state)
        {
            NativeHelpers.LUID_AND_ATTRIBUTES[] privilegeAttr = new NativeHelpers.LUID_AND_ATTRIBUTES[state.Count];
            int i = 0;

            foreach (KeyValuePair<string, bool?> entry in state)
            {
                NativeHelpers.LUID luid;
                if (!NativeMethods.LookupPrivilegeValue(null, entry.Key, out luid))
                    throw new Win32Exception(String.Format("LookupPrivilegeValue({0}) failed", entry.Key));

                NativeHelpers.PrivilegeAttributes attributes;
                switch (entry.Value)
                {
                    case true:
                        attributes = NativeHelpers.PrivilegeAttributes.Enabled;
                        break;
                    case false:
                        attributes = NativeHelpers.PrivilegeAttributes.Disabled;
                        break;
                    default:
                        attributes = NativeHelpers.PrivilegeAttributes.Removed;
                        break;
                }

                privilegeAttr[i].Luid = luid;
                privilegeAttr[i].Attributes = attributes;

                i++;
            }

            return AdjustTokenPrivileges(token, privilegeAttr);
        }

        private static Dictionary<string, bool?> AdjustTokenPrivileges(SafeHandle token, NativeHelpers.LUID_AND_ATTRIBUTES[] newState)
        {
            Dictionary<string, bool?> previousState = new Dictionary<string, bool?>();

            bool disableAllPrivileges;
            IntPtr newStatePtr;
            NativeHelpers.TOKEN_PRIVILEGES oldState;
            NativeHelpers.LUID_AND_ATTRIBUTES[] oldStatePrivileges;
            UInt32 returnLength;

            if (newState == null)
            {
                disableAllPrivileges = true;
                newStatePtr = IntPtr.Zero;
            }
            else
            {
                disableAllPrivileges = false;

                // Need to manually marshal the bytes requires for newState as the constant size
                // of LUID_AND_ATTRIBUTES is set to 1 and can't be overridden at runtime
                int luidAttrSize = Marshal.SizeOf(typeof(NativeHelpers.LUID_AND_ATTRIBUTES)) * newState.Length;
                int totalSize = luidAttrSize + sizeof(UInt32);

                byte[] newStateBytes = new byte[totalSize];

                // get the first entry that includes the struct details
                NativeHelpers.TOKEN_PRIVILEGES tokenPrivileges = new NativeHelpers.TOKEN_PRIVILEGES()
                {
                    PrivilegeCount = (UInt32)newState.Length,
                    Privileges = newState,
                };
                int offset = StructureToBytes(tokenPrivileges, newStateBytes, 0);

                // copy the remaining LUID_AND_ATTRIBUTES (if any)
                for (int i = 1; i < newState.Length; i++)
                    offset += StructureToBytes(newState[i], newStateBytes, offset);

                // finally create the pointer to the byte array we just created
                newStatePtr = Marshal.AllocHGlobal(newStateBytes.Length);
                Marshal.Copy(newStateBytes, 0, newStatePtr, newStateBytes.Length);
            }

            IntPtr hToken = IntPtr.Zero;
            if (!NativeMethods.OpenProcessToken(token, TokenAccessLevels.Query | TokenAccessLevels.AdjustPrivileges, out hToken))
                throw new Win32Exception("OpenProcessToken() failed with Query and AdjustPrivileges");
            try
            {
                IntPtr oldStatePtr = Marshal.AllocHGlobal(0);
                if (!NativeMethods.AdjustTokenPrivileges(hToken, disableAllPrivileges, newStatePtr, 0, oldStatePtr, out returnLength))
                {
                    int errCode = Marshal.GetLastWin32Error();
                    if (errCode != 122) // ERROR_INSUFFICIENT_BUFFER
                        throw new Win32Exception(errCode, "AdjustTokenPrivileges() failed to get old state size");
                }

                // resize the oldStatePtr based on the length returned from Windows
                Marshal.FreeHGlobal(oldStatePtr);
                oldStatePtr = Marshal.AllocHGlobal((int)returnLength);
                try
                {
                    if (!NativeMethods.AdjustTokenPrivileges(hToken, disableAllPrivileges, newStatePtr, returnLength, oldStatePtr, out returnLength))
                        throw new Win32Exception("AdjustTokenPrivileges() failed");

                    // Marshal the oldStatePtr to the struct
                    oldState = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(oldStatePtr, typeof(NativeHelpers.TOKEN_PRIVILEGES));
                    oldStatePrivileges = new NativeHelpers.LUID_AND_ATTRIBUTES[oldState.PrivilegeCount];
                    PtrToStructureArray(oldStatePrivileges, oldStatePtr.ToInt64() + Marshal.SizeOf(oldState.PrivilegeCount));
                }
                finally
                {
                    Marshal.FreeHGlobal(oldStatePtr);
                }
            }
            finally
            {
                if (newStatePtr != IntPtr.Zero)
                    Marshal.FreeHGlobal(newStatePtr);
                NativeMethods.CloseHandle(hToken);
            }

            foreach (NativeHelpers.LUID_AND_ATTRIBUTES privilege in oldStatePrivileges)
            {
                string name = GetPrivilegeName(privilege.Luid);
                previousState.Add(name, privilege.Attributes.HasFlag(NativeHelpers.PrivilegeAttributes.Enabled));
            }

            return previousState;
        }

        private static string GetPrivilegeName(NativeHelpers.LUID luid)
        {
            UInt32 nameLen = 0;
            NativeMethods.LookupPrivilegeName(null, ref luid, null, ref nameLen);

            StringBuilder name = new StringBuilder((int)(nameLen + 1));
            if (!NativeMethods.LookupPrivilegeName(null, ref luid, name, ref nameLen))
                throw new Win32Exception("LookupPrivilegeName() failed");

            return name.ToString();
        }

        private static void PtrToStructureArray<T>(T[] array, Int64 pointerAddress)
        {
            Int64 pointerOffset = pointerAddress;
            for (int i = 0; i < array.Length; i++, pointerOffset += Marshal.SizeOf(typeof(T)))
                array[i] = (T)Marshal.PtrToStructure(new IntPtr(pointerOffset), typeof(T));
        }

        private static int StructureToBytes<T>(T structure, byte[] array, int offset)
        {
            int size = Marshal.SizeOf(typeof(T));
            IntPtr structPtr = Marshal.AllocHGlobal(size);
            try
            {
                Marshal.StructureToPtr(structure, structPtr, false);
                Marshal.Copy(structPtr, array, offset, size);
            }
            finally
            {
                Marshal.FreeHGlobal(structPtr);
            }

            return size;
        }
    }
}
'@

Function Import-PrivilegeUtil {
    <#
    .SYNOPSIS
    Compiles the C# code that can be used to manage Windows privileges from an
    Ansible module. Once this function is called, the following PowerShell
    cmdlets can be used;

        Get-AnsiblePrivilege
        Remove-AnsiblePrivilege
        Set-AnsiblePrivilege

    The above cmdlets give the ability to manage permissions on the current
    process token but the underlying .NET classes are also exposes for greater
    control. The following functions can be used by calling the .NET class

    [Ansible.PrivilegeUtil.Helpers]::CheckPrivilegeName($name)
    [Ansible.PrivilegeUtil.Helpers]::DisablePrivilege($process, $name)
    [Ansible.PrivilegeUtil.Helpers]::DisableAllPrivileges($process)
    [Ansible.PrivilegeUtil.Helpers]::EnablePrivilege($process, $name)
    [Ansible.PrivilegeUtil.Helpers]::GetAllPrivilegeInfo($process)
    [Ansible.PrivilegeUtil.Helpers]::RemovePrivilege($process, $name)
    [Ansible.PrivilegeUtil.Helpers]::SetTokenPrivileges($process, $new_state)

    Here is a brief explanation of each type of arg
    $process = The process handle to manipulate, use '[Ansible.PrivilegeUtils.Helpers]::GetCurrentProcess() to get the current process handle
    $name = The name of the privilege, this is the constant value from https://docs.microsoft.com/en-us/windows/desktop/SecAuthZ/privilege-constants, e.g. SeAuditPrivilege
    $new_state = 'System.Collections.Generic.Dictionary`2[[System.String], [System.Nullable`1[System.Boolean]]]'
        The key is the constant name as a string, the value is a ternary boolean where
            true - will enable the privilege
            false - will disable the privilege
            null - will remove the privilege

    Each method that changes the privilege state will return a dictionary that
    can be used as the $new_state arg of SetTokenPrivileges to undo and revert
    back to the original state. If you remove a privilege then this is
    irreversible and won't be part of the returned dict
    #>
    [CmdletBinding()]
    # build the C# code to compile
    $namespace_import = ($ansible_privilege_util_namespaces | ForEach-Object { "using $_;" }) -join "`r`n"
    $platform_util = "$namespace_import`r`n`r`n$ansible_privilege_util_code"

    # FUTURE: find a better way to get the _ansible_remote_tmp variable
    # this is used to force csc to compile the C# code in the remote tmp
    # specified
    $original_tmp = $env:TMP

    $remote_tmp = $original_tmp
    $module_params = Get-Variable -Name complex_args -ErrorAction SilentlyContinue
    if ($module_params) {
        if ($module_params.Value.ContainsKey("_ansible_remote_tmp") ) {
            $remote_tmp = $module_params.Value["_ansible_remote_tmp"]
            $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
        }
    }

    $env:TMP = $remote_tmp
    Add-Type -TypeDefinition $platform_util
    $env:TMP = $original_tmp
}

Function Get-AnsiblePrivilege {
    <#
    .SYNOPSIS
    Get the status of a privilege for the current process. This returns
        $true - the privilege is eanbled
        $false - the privilege is disabled
        $null - the privilege is removed from the token

    If Name is not a valid privilege name, this will throw an
    ArgumentException.

    .EXAMPLE
    Get-AnsiblePrivilege -Name SeDebugPrivilege
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$Name
    )

    if (-not [Ansible.PrivilegeUtil.Helpers]::CheckPrivilegeName($Name)) {
        throw [System.ArgumentException] "Invalid privilege name '$Name'"
    }

    $process_token = [Ansible.PrivilegeUtil.Helpers]::GetCurrentProcess()
    $privilege_info = [Ansible.PrivilegeUtil.Helpers]::GetAllPrivilegeInfo($process_token)
    if ($privilege_info.ContainsKey($Name)) {
        $status = $privilege_info.$Name
        return $status.HasFlag([Ansible.PrivilegeUtil.NativeHelpers+PrivilegeAttributes]::Enabled)
    } else {
        return $null
    }
}

Function Remove-AnsiblePrivilege {
    <#
    .SYNOPSIS
    Remove a privilege from the current process' token. Once removed, the
    privilege cannot be re-added.

    If Name is not a valid privilege name, this will throw an
    ArgumentException.

    .EXAMPLE
    Remove-AnsiblePrivilege -Name SeBackupPrivilege
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory=$true)][String]$Name
    )

    $current_state = Get-AnsiblePrivilege -Name $Name
    if ($null -eq $current_state) {
        return  # no change need to occur
    }

    $process_token = [Ansible.PrivilegeUtil.Helpers]::GetCurrentProcess()
    if ($PSCmdlet.ShouldProcess($Name, "Remove the privilege $Name")) {
        $new_state = New-Object -TypeName 'System.Collections.Generic.Dictionary`2[[System.String], [System.Nullable`1[System.Boolean]]]'
        $new_state.Add($Name, $null)
        [Ansible.PrivilegeUtil.Helpers]::SetTokenPrivileges($process_token, $new_state) > $null
    }
}

Function Set-AnsiblePrivilege {
    <#
    .SYNOPSIS
    Enables/Disables a privilege on the current process' token. If a privilege
    has been removed from the process token, this will throw an
    InvalidOperationException.

    .EXAMPLE
    # enable a privilege
    Set-AnsiblePrivilege -Name SeCreateSymbolicLinkPrivilege -Value $true

    # disable a privilege
    Set-AnsiblePrivilege -Name SeCreateSymbolicLinkPrivilege -Value $false
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory=$true)][String]$Name,
        [Parameter(Mandatory=$true)][bool]$Value
    )

    $action = switch($Value) {
        $true { "Enable" }
        $false { "Disable" }
    }

    $current_state = Get-AnsiblePrivilege -Name $Name
    if ($current_state -eq $Value) {
        return  # no change needs to occur
    } elseif ($null -eq $current_state) {
        # once a privilege is removed from a token we cannot do anything with it
        throw [System.InvalidOperationException] "Cannot $($action.ToLower()) the privilege '$Name' as it has been removed from the token"
    }

    $process_token = [Ansible.PrivilegeUtil.Helpers]::GetCurrentProcess()
    if ($PSCmdlet.ShouldProcess($Name, "$action the privilege $Name")) {
        $new_state = New-Object -TypeName 'System.Collections.Generic.Dictionary`2[[System.String], [System.Nullable`1[System.Boolean]]]'
        $new_state.Add($Name, $Value)
        [Ansible.PrivilegeUtil.Helpers]::SetTokenPrivileges($process_token, $new_state) > $null
    }
}

Export-ModuleMember -Function Import-PrivilegeUtil, Get-AnsiblePrivilege, Remove-AnsiblePrivilege, Set-AnsiblePrivilege `
    -Variable ansible_privilege_util_namespaces, ansible_privilege_util_code
