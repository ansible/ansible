using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;

namespace Ansible.AccessToken
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct LUID_AND_ATTRIBUTES
        {
            public Luid Luid;
            public UInt32 Attributes;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SID_AND_ATTRIBUTES
        {
            public IntPtr Sid;
            public int Attributes;
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

        public enum TokenInformationClass : uint
        {
            TokenUser = 1,
            TokenPrivileges = 3,
            TokenStatistics = 10,
            TokenElevationType = 18,
            TokenLinkedToken = 19,
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool DuplicateTokenEx(
            SafeNativeHandle hExistingToken,
            TokenAccessLevels dwDesiredAccess,
            IntPtr lpTokenAttributes,
            SecurityImpersonationLevel ImpersonationLevel,
            TokenType TokenType,
            out SafeNativeHandle phNewToken);

        [DllImport("kernel32.dll")]
        public static extern SafeNativeHandle GetCurrentProcess();

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

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LogonUserW(
            string lpszUsername,
            string lpszDomain,
            string lpszPassword,
            LogonType dwLogonType,
            LogonProvider dwLogonProvider,
            out SafeNativeHandle phToken);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupPrivilegeNameW(
            string lpSystemName,
            ref Luid lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern SafeNativeHandle OpenProcess(
            ProcessAccessFlags dwDesiredAccess,
            bool bInheritHandle,
            UInt32 dwProcessId);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool OpenProcessToken(
            SafeNativeHandle ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out SafeNativeHandle TokenHandle);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool RevertToSelf();
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

    public enum LogonProvider
    {
        Default,
    }

    public enum LogonType
    {
        Interactive = 2,
        Network = 3,
        Batch = 4,
        Service = 5,
        Unlock = 7,
        NetworkCleartext = 8,
        NewCredentials = 9,
    }

    [Flags]
    public enum PrivilegeAttributes : uint
    {
        Disabled = 0x00000000,
        EnabledByDefault = 0x00000001,
        Enabled = 0x00000002,
        Removed = 0x00000004,
        UsedForAccess = 0x80000000,
    }

    [Flags]
    public enum ProcessAccessFlags : uint
    {
        Terminate = 0x00000001,
        CreateThread = 0x00000002,
        VmOperation = 0x00000008,
        VmRead = 0x00000010,
        VmWrite = 0x00000020,
        DupHandle = 0x00000040,
        CreateProcess = 0x00000080,
        SetQuota = 0x00000100,
        SetInformation = 0x00000200,
        QueryInformation = 0x00000400,
        SuspendResume = 0x00000800,
        QueryLimitedInformation = 0x00001000,
        Delete = 0x00010000,
        ReadControl = 0x00020000,
        WriteDac = 0x00040000,
        WriteOwner = 0x00080000,
        Synchronize = 0x00100000,
    }

    public enum SecurityImpersonationLevel
    {
        Anonymous,
        Identification,
        Impersonation,
        Delegation,
    }

    public enum TokenElevationType
    {
        Default = 1,
        Full,
        Limited,
    }

    public enum TokenType
    {
        Primary = 1,
        Impersonation,
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct Luid
    {
        public UInt32 LowPart;
        public Int32 HighPart;

        public static explicit operator UInt64(Luid l)
        {
            return (UInt64)((UInt64)l.HighPart << 32) | (UInt64)l.LowPart;
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TokenStatistics
    {
        public Luid TokenId;
        public Luid AuthenticationId;
        public Int64 ExpirationTime;
        public TokenType TokenType;
        public SecurityImpersonationLevel ImpersonationLevel;
        public UInt32 DynamicCharged;
        public UInt32 DynamicAvailable;
        public UInt32 GroupCount;
        public UInt32 PrivilegeCount;
        public Luid ModifiedId;
    }

    public class PrivilegeInfo
    {
        public string Name;
        public PrivilegeAttributes Attributes;

        internal PrivilegeInfo(NativeHelpers.LUID_AND_ATTRIBUTES la)
        {
            Name = TokenUtil.GetPrivilegeName(la.Luid);
            Attributes = (PrivilegeAttributes)la.Attributes;
        }
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
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2} - 0x{2:X8})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public class TokenUtil
    {
        public static SafeNativeHandle DuplicateToken(SafeNativeHandle hToken, TokenAccessLevels access,
            SecurityImpersonationLevel impersonationLevel, TokenType tokenType)
        {
            SafeNativeHandle dupToken;
            if (!NativeMethods.DuplicateTokenEx(hToken, access, IntPtr.Zero, impersonationLevel, tokenType, out dupToken))
                throw new Win32Exception("Failed to duplicate token");
            return dupToken;
        }

        public static SecurityIdentifier GetTokenUser(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken,
                NativeHelpers.TokenInformationClass.TokenUser))
            {
                NativeHelpers.TOKEN_USER tokenUser = (NativeHelpers.TOKEN_USER)Marshal.PtrToStructure(
                    tokenInfo.DangerousGetHandle(),
                    typeof(NativeHelpers.TOKEN_USER));
                return new SecurityIdentifier(tokenUser.User.Sid);
            }
        }

        public static List<PrivilegeInfo> GetTokenPrivileges(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken,
                NativeHelpers.TokenInformationClass.TokenPrivileges))
            {
                NativeHelpers.TOKEN_PRIVILEGES tokenPrivs = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(
                    tokenInfo.DangerousGetHandle(),
                    typeof(NativeHelpers.TOKEN_PRIVILEGES));

                NativeHelpers.LUID_AND_ATTRIBUTES[] luidAttrs =
                    new NativeHelpers.LUID_AND_ATTRIBUTES[tokenPrivs.PrivilegeCount];
                PtrToStructureArray(luidAttrs, IntPtr.Add(tokenInfo.DangerousGetHandle(),
                    Marshal.SizeOf(tokenPrivs.PrivilegeCount)));

                return luidAttrs.Select(la => new PrivilegeInfo(la)).ToList();
            }
        }

        public static TokenStatistics GetTokenStatistics(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken,
                NativeHelpers.TokenInformationClass.TokenStatistics))
            {
                TokenStatistics tokenStats = (TokenStatistics)Marshal.PtrToStructure(
                    tokenInfo.DangerousGetHandle(),
                    typeof(TokenStatistics));
                return tokenStats;
            }
        }

        public static TokenElevationType GetTokenElevationType(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken,
                NativeHelpers.TokenInformationClass.TokenElevationType))
            {
                return (TokenElevationType)Marshal.ReadInt32(tokenInfo.DangerousGetHandle());
            }
        }

        public static SafeNativeHandle GetTokenLinkedToken(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken,
                NativeHelpers.TokenInformationClass.TokenLinkedToken))
            {
                return new SafeNativeHandle(Marshal.ReadIntPtr(tokenInfo.DangerousGetHandle()));
            }
        }

        public static IEnumerable<SafeNativeHandle> EnumerateUserTokens(SecurityIdentifier sid,
            TokenAccessLevels access = TokenAccessLevels.Query)
        {
            foreach (System.Diagnostics.Process process in System.Diagnostics.Process.GetProcesses())
            {
                // We always need the Query access level so we can query the TokenUser
                using (process)
                using (SafeNativeHandle hToken = TryOpenAccessToken(process, access | TokenAccessLevels.Query))
                {
                    if (hToken == null)
                        continue;

                    if (!sid.Equals(GetTokenUser(hToken)))
                        continue;

                    yield return hToken;
                }
            }
        }

        public static void ImpersonateToken(SafeNativeHandle hToken)
        {
            if (!NativeMethods.ImpersonateLoggedOnUser(hToken))
                throw new Win32Exception("Failed to impersonate token");
        }

        public static SafeNativeHandle LogonUser(string username, string domain, string password, LogonType logonType,
            LogonProvider logonProvider)
        {
            SafeNativeHandle hToken;
            if (!NativeMethods.LogonUserW(username, domain, password, logonType, logonProvider, out hToken))
                throw new Win32Exception(String.Format("Failed to logon {0}",
                    String.IsNullOrEmpty(domain) ? username : domain + "\\" + username));

            return hToken;
        }

        public static SafeNativeHandle OpenProcess()
        {
            return NativeMethods.GetCurrentProcess();
        }

        public static SafeNativeHandle OpenProcess(Int32 pid, ProcessAccessFlags access, bool inherit)
        {
            SafeNativeHandle hProcess = NativeMethods.OpenProcess(access, inherit, (UInt32)pid);
            if (hProcess.IsInvalid)
                throw new Win32Exception(String.Format("Failed to open process {0} with access {1}",
                    pid, access.ToString()));

            return hProcess;
        }

        public static SafeNativeHandle OpenProcessToken(SafeNativeHandle hProcess, TokenAccessLevels access)
        {
            SafeNativeHandle hToken;
            if (!NativeMethods.OpenProcessToken(hProcess, access, out hToken))
                throw new Win32Exception(String.Format("Failed to open proces token with access {0}",
                    access.ToString()));

            return hToken;
        }

        public static void RevertToSelf()
        {
            if (!NativeMethods.RevertToSelf())
                throw new Win32Exception("Failed to revert thread impersonation");
        }

        internal static string GetPrivilegeName(Luid luid)
        {
            UInt32 nameLen = 0;
            NativeMethods.LookupPrivilegeNameW(null, ref luid, null, ref nameLen);

            StringBuilder name = new StringBuilder((int)(nameLen + 1));
            if (!NativeMethods.LookupPrivilegeNameW(null, ref luid, name, ref nameLen))
                throw new Win32Exception("LookupPrivilegeName() failed");

            return name.ToString();
        }

        private static SafeMemoryBuffer GetTokenInformation(SafeNativeHandle hToken,
            NativeHelpers.TokenInformationClass infoClass)
        {
            UInt32 tokenLength;
            bool res = NativeMethods.GetTokenInformation(hToken, infoClass, new SafeMemoryBuffer(IntPtr.Zero), 0,
                out tokenLength);
            int errCode = Marshal.GetLastWin32Error();
            if (!res && errCode != 24 && errCode != 122)  // ERROR_INSUFFICIENT_BUFFER, ERROR_BAD_LENGTH
                throw new Win32Exception(errCode, String.Format("GetTokenInformation({0}) failed to get buffer length",
                    infoClass.ToString()));

            SafeMemoryBuffer tokenInfo = new SafeMemoryBuffer((int)tokenLength);
            if (!NativeMethods.GetTokenInformation(hToken, infoClass, tokenInfo, tokenLength, out tokenLength))
                throw new Win32Exception(String.Format("GetTokenInformation({0}) failed", infoClass.ToString()));

            return tokenInfo;
        }

        private static void PtrToStructureArray<T>(T[] array, IntPtr ptr)
        {
            IntPtr ptrOffset = ptr;
            for (int i = 0; i < array.Length; i++, ptrOffset = IntPtr.Add(ptrOffset, Marshal.SizeOf(typeof(T))))
                array[i] = (T)Marshal.PtrToStructure(ptrOffset, typeof(T));
        }

        private static SafeNativeHandle TryOpenAccessToken(System.Diagnostics.Process process, TokenAccessLevels access)
        {
            try
            {
                using (SafeNativeHandle hProcess = OpenProcess(process.Id, ProcessAccessFlags.QueryInformation, false))
                    return OpenProcessToken(hProcess, access);
            }
            catch (Win32Exception)
            {
                return null;
            }
        }
    }
}