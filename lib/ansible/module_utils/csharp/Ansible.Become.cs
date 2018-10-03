using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;

// TODO: make some classes/structs private/internal before the next release

namespace Ansible.Become
{
    [StructLayout(LayoutKind.Sequential)]
    public class SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public bool bInheritHandle = false;
        public SECURITY_ATTRIBUTES()
        {
            nLength = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public class STARTUPINFO
    {
        public Int32 cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 28)]
        public byte[] _data1;
        public Int32 dwFlags;
        public Int16 wShowWindow;
        public Int16 cbReserved2;
        public IntPtr lpReserved2;
        public SafeFileHandle hStdInput;
        public SafeFileHandle hStdOutput;
        public SafeFileHandle hStdError;
        public STARTUPINFO()
        {
            cb = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public class STARTUPINFOEX
    {
        public STARTUPINFO startupInfo;
        public IntPtr lpAttributeList;
        public STARTUPINFOEX()
        {
            startupInfo = new STARTUPINFO();
            startupInfo.cb = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SID_AND_ATTRIBUTES
    {
        public IntPtr Sid;
        public int Attributes;
    }

    public struct TOKEN_USER
    {
        public SID_AND_ATTRIBUTES User;
    }

    [Flags]
    public enum StartupInfoFlags : uint
    {
        USESTDHANDLES = 0x00000100
    }

    [Flags]
    public enum CreationFlags : uint
    {
        CREATE_BREAKAWAY_FROM_JOB = 0x01000000,
        CREATE_DEFAULT_ERROR_MODE = 0x04000000,
        CREATE_NEW_CONSOLE = 0x00000010,
        CREATE_SUSPENDED = 0x00000004,
        CREATE_UNICODE_ENVIRONMENT = 0x00000400,
        EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    }

    public enum HandleFlags : uint
    {
        None = 0,
        INHERIT = 1
    }

    [Flags]
    public enum LogonFlags
    {
        LOGON_WITH_PROFILE = 0x00000001,
        LOGON_NETCREDENTIALS_ONLY = 0x00000002
    }

    public enum LogonType
    {
        LOGON32_LOGON_INTERACTIVE = 2,
        LOGON32_LOGON_NETWORK = 3,
        LOGON32_LOGON_BATCH = 4,
        LOGON32_LOGON_SERVICE = 5,
        LOGON32_LOGON_UNLOCK = 7,
        LOGON32_LOGON_NETWORK_CLEARTEXT = 8,
        LOGON32_LOGON_NEW_CREDENTIALS = 9
    }

    public enum LogonProvider
    {
        LOGON32_PROVIDER_DEFAULT = 0,
    }

    public enum TokenInformationClass
    {
        TokenUser = 1,
        TokenType = 8,
        TokenImpersonationLevel = 9,
        TokenElevationType = 18,
        TokenLinkedToken = 19,
    }

    public enum TokenElevationType
    {
        TokenElevationTypeDefault = 1,
        TokenElevationTypeFull,
        TokenElevationTypeLimited
    }

    [Flags]
    public enum ProcessAccessFlags : uint
    {
        PROCESS_QUERY_INFORMATION = 0x00000400,
    }

    public enum SECURITY_IMPERSONATION_LEVEL
    {
        SecurityImpersonation,
    }

    public enum TOKEN_TYPE
    {
        TokenPrimary = 1,
        TokenImpersonation
    }

    class NativeWaitHandle : WaitHandle
    {
        public NativeWaitHandle(IntPtr handle)
        {
            this.SafeWaitHandle = new SafeWaitHandle(handle, false);
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

    public class CommandResult
    {
        public string StandardOut { get; internal set; }
        public string StandardError { get; internal set; }
        public uint ExitCode { get; internal set; }
    }

    public class BecomeUtil
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool LogonUser(
            string lpszUsername,
            string lpszDomain,
            string lpszPassword,
            LogonType dwLogonType,
            LogonProvider dwLogonProvider,
            out IntPtr phToken);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool CreateProcessWithTokenW(
            IntPtr hToken,
            LogonFlags dwLogonFlags,
            [MarshalAs(UnmanagedType.LPTStr)]
            string lpApplicationName,
            StringBuilder lpCommandLine,
            CreationFlags dwCreationFlags,
            IntPtr lpEnvironment,
            [MarshalAs(UnmanagedType.LPTStr)]
            string lpCurrentDirectory,
            STARTUPINFOEX lpStartupInfo,
            out PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll")]
        private static extern bool CreatePipe(
            out SafeFileHandle hReadPipe,
            out SafeFileHandle hWritePipe,
            SECURITY_ATTRIBUTES lpPipeAttributes,
            uint nSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetHandleInformation(
            SafeFileHandle hObject,
            HandleFlags dwMask,
            int dwFlags);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetExitCodeProcess(
            IntPtr hProcess,
            out uint lpExitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr GetProcessWindowStation();

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr GetThreadDesktop(
            int dwThreadId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern int GetCurrentThreadId();

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool GetTokenInformation(
            IntPtr TokenHandle,
            TokenInformationClass TokenInformationClass,
            IntPtr TokenInformation,
            uint TokenInformationLength,
            out uint ReturnLength);

        [DllImport("psapi.dll", SetLastError = true)]
        private static extern bool EnumProcesses(
            [MarshalAs(UnmanagedType.LPArray, ArraySubType = UnmanagedType.U4)]
                [In][Out] IntPtr[] processIds,
            uint cb,
            [MarshalAs(UnmanagedType.U4)]
                out uint pBytesReturned);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(
            ProcessAccessFlags processAccess,
            bool bInheritHandle,
            IntPtr processId);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out IntPtr TokenHandle);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool ConvertSidToStringSidW(
            IntPtr pSID,
            [MarshalAs(UnmanagedType.LPTStr)]
            out string StringSid);

        [DllImport("advapi32", SetLastError = true)]
        private static extern bool DuplicateTokenEx(
            IntPtr hExistingToken,
            TokenAccessLevels dwDesiredAccess,
            IntPtr lpTokenAttributes,
            SECURITY_IMPERSONATION_LEVEL ImpersonationLevel,
            TOKEN_TYPE TokenType,
            out IntPtr phNewToken);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool ImpersonateLoggedOnUser(
            IntPtr hToken);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool RevertToSelf();

        public static CommandResult RunAsUser(string username, string password, string lpCommandLine,
            string lpCurrentDirectory, string stdinInput, LogonFlags logonFlags, LogonType logonType)
        {
            SecurityIdentifier account = null;
            if (logonType != LogonType.LOGON32_LOGON_NEW_CREDENTIALS)
            {
                account = GetBecomeSid(username);
            }

            STARTUPINFOEX si = new STARTUPINFOEX();
            si.startupInfo.dwFlags = (int)StartupInfoFlags.USESTDHANDLES;

            SECURITY_ATTRIBUTES pipesec = new SECURITY_ATTRIBUTES();
            pipesec.bInheritHandle = true;

            // Create the stdout, stderr and stdin pipes used in the process and add to the startupInfo
            SafeFileHandle stdout_read, stdout_write, stderr_read, stderr_write, stdin_read, stdin_write;
            if (!CreatePipe(out stdout_read, out stdout_write, pipesec, 0))
                throw new Win32Exception("STDOUT pipe setup failed");
            if (!SetHandleInformation(stdout_read, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDOUT pipe handle setup failed");

            if (!CreatePipe(out stderr_read, out stderr_write, pipesec, 0))
                throw new Win32Exception("STDERR pipe setup failed");
            if (!SetHandleInformation(stderr_read, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDERR pipe handle setup failed");

            if (!CreatePipe(out stdin_read, out stdin_write, pipesec, 0))
                throw new Win32Exception("STDIN pipe setup failed");
            if (!SetHandleInformation(stdin_write, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDIN pipe handle setup failed");

            si.startupInfo.hStdOutput = stdout_write;
            si.startupInfo.hStdError = stderr_write;
            si.startupInfo.hStdInput = stdin_read;

            // Setup the stdin buffer
            UTF8Encoding utf8_encoding = new UTF8Encoding(false);
            FileStream stdin_fs = new FileStream(stdin_write, FileAccess.Write, 32768);
            StreamWriter stdin = new StreamWriter(stdin_fs, utf8_encoding, 32768);

            // Create the environment block if set
            IntPtr lpEnvironment = IntPtr.Zero;

            CreationFlags startup_flags = CreationFlags.CREATE_UNICODE_ENVIRONMENT;

            PROCESS_INFORMATION pi = new PROCESS_INFORMATION();

            // Get the user tokens to try running processes with
            List<IntPtr> tokens = GetUserTokens(account, username, password, logonType);

            bool launch_success = false;
            foreach (IntPtr token in tokens)
            {
                if (CreateProcessWithTokenW(
                    token,
                    logonFlags,
                    null,
                    new StringBuilder(lpCommandLine),
                    startup_flags,
                    lpEnvironment,
                    lpCurrentDirectory,
                    si,
                    out pi))
                {
                    launch_success = true;
                    break;
                }
            }

            if (!launch_success)
                throw new Win32Exception("Failed to start become process");

            CommandResult result = new CommandResult();
            // Setup the output buffers and get stdout/stderr
            FileStream stdout_fs = new FileStream(stdout_read, FileAccess.Read, 4096);
            StreamReader stdout = new StreamReader(stdout_fs, utf8_encoding, true, 4096);
            stdout_write.Close();

            FileStream stderr_fs = new FileStream(stderr_read, FileAccess.Read, 4096);
            StreamReader stderr = new StreamReader(stderr_fs, utf8_encoding, true, 4096);
            stderr_write.Close();

            stdin.WriteLine(stdinInput);
            stdin.Close();

            string stdout_str, stderr_str = null;
            GetProcessOutput(stdout, stderr, out stdout_str, out stderr_str);
            UInt32 rc = GetProcessExitCode(pi.hProcess);

            result.StandardOut = stdout_str;
            result.StandardError = stderr_str;
            result.ExitCode = rc;

            return result;
        }

        private static SecurityIdentifier GetBecomeSid(string username)
        {
            NTAccount account = new NTAccount(username);
            try
            {
                SecurityIdentifier security_identifier = (SecurityIdentifier)account.Translate(typeof(SecurityIdentifier));
                return security_identifier;
            }
            catch (IdentityNotMappedException ex)
            {
                throw new Exception(String.Format("Unable to find become user {0}: {1}", username, ex.Message));
            }
        }

        private static List<IntPtr> GetUserTokens(SecurityIdentifier account, string username, string password, LogonType logonType)
        {
            List<IntPtr> tokens = new List<IntPtr>();
            List<String> service_sids = new List<String>()
            {
                "S-1-5-18", // NT AUTHORITY\SYSTEM
                "S-1-5-19", // NT AUTHORITY\LocalService
                "S-1-5-20"  // NT AUTHORITY\NetworkService
            };

            IntPtr hSystemToken = IntPtr.Zero;
            string account_sid = "";
            if (logonType != LogonType.LOGON32_LOGON_NEW_CREDENTIALS)
            {
                GrantAccessToWindowStationAndDesktop(account);
                // Try to get SYSTEM token handle so we can impersonate to get full admin token
                hSystemToken = GetSystemUserHandle();
                account_sid = account.ToString();
            }
            bool impersonated = false;

            try
            {
                IntPtr hSystemTokenDup = IntPtr.Zero;
                if (hSystemToken == IntPtr.Zero && service_sids.Contains(account_sid))
                {
                    // We need the SYSTEM token if we want to become one of those accounts, fail here
                    throw new Win32Exception("Failed to get token for NT AUTHORITY\\SYSTEM");
                }
                else if (hSystemToken != IntPtr.Zero)
                {
                    // We have the token, need to duplicate and impersonate
                    bool dupResult = DuplicateTokenEx(
                        hSystemToken,
                        TokenAccessLevels.MaximumAllowed,
                        IntPtr.Zero,
                        SECURITY_IMPERSONATION_LEVEL.SecurityImpersonation,
                        TOKEN_TYPE.TokenPrimary,
                        out hSystemTokenDup);
                    int lastError = Marshal.GetLastWin32Error();
                    CloseHandle(hSystemToken);

                    if (!dupResult && service_sids.Contains(account_sid))
                        throw new Win32Exception(lastError, "Failed to duplicate token for NT AUTHORITY\\SYSTEM");
                    else if (dupResult && account_sid != "S-1-5-18")
                    {
                        if (ImpersonateLoggedOnUser(hSystemTokenDup))
                            impersonated = true;
                        else if (service_sids.Contains(account_sid))
                            throw new Win32Exception("Failed to impersonate as SYSTEM account");
                    }
                    // If SYSTEM impersonation failed but we're trying to become a regular user, just proceed;
                    // might get a limited token in UAC-enabled cases, but better than nothing...
                }

                string domain = null;

                if (service_sids.Contains(account_sid))
                {
                    // We're using a well-known service account, do a service logon instead of the actual flag set
                    logonType = LogonType.LOGON32_LOGON_SERVICE;
                    domain = "NT AUTHORITY";
                    password = null;
                    switch (account_sid)
                    {
                        case "S-1-5-18":
                            tokens.Add(hSystemTokenDup);
                            return tokens;
                        case "S-1-5-19":
                            username = "LocalService";
                            break;
                        case "S-1-5-20":
                            username = "NetworkService";
                            break;
                    }
                }
                else
                {
                    // We are trying to become a local or domain account
                    if (username.Contains(@"\"))
                    {
                        var user_split = username.Split(Convert.ToChar(@"\"));
                        domain = user_split[0];
                        username = user_split[1];
                    }
                    else if (username.Contains("@"))
                        domain = null;
                    else
                        domain = ".";
                }

                IntPtr hToken = IntPtr.Zero;
                if (!LogonUser(
                    username,
                    domain,
                    password,
                    logonType,
                    LogonProvider.LOGON32_PROVIDER_DEFAULT,
                    out hToken))
                {
                    throw new Win32Exception("LogonUser failed");
                }

                if (!service_sids.Contains(account_sid))
                {
                    // Try and get the elevated token for local/domain account
                    IntPtr hTokenElevated = GetElevatedToken(hToken);
                    tokens.Add(hTokenElevated);
                }

                // add the original token as a fallback
                tokens.Add(hToken);
            }
            finally
            {
                if (impersonated)
                    RevertToSelf();
            }

            return tokens;
        }

        private static IntPtr GetSystemUserHandle()
        {
            uint array_byte_size = 1024 * sizeof(uint);
            IntPtr[] pids = new IntPtr[1024];
            uint bytes_copied;

            if (!EnumProcesses(pids, array_byte_size, out bytes_copied))
            {
                throw new Win32Exception("Failed to enumerate processes");
            }
            // TODO: Handle if bytes_copied is larger than the array size and rerun EnumProcesses with larger array
            uint num_processes = bytes_copied / sizeof(uint);

            for (uint i = 0; i < num_processes; i++)
            {
                IntPtr hProcess = OpenProcess(ProcessAccessFlags.PROCESS_QUERY_INFORMATION, false, pids[i]);
                if (hProcess != IntPtr.Zero)
                {
                    IntPtr hToken = IntPtr.Zero;
                    // According to CreateProcessWithTokenW we require a token with
                    //  TOKEN_QUERY, TOKEN_DUPLICATE and TOKEN_ASSIGN_PRIMARY
                    // Also add in TOKEN_IMPERSONATE so we can get an impersontated token
                    TokenAccessLevels desired_access = TokenAccessLevels.Query |
                        TokenAccessLevels.Duplicate |
                        TokenAccessLevels.AssignPrimary |
                        TokenAccessLevels.Impersonate;

                    if (OpenProcessToken(hProcess, desired_access, out hToken))
                    {
                        string sid = GetTokenUserSID(hToken);
                        if (sid == "S-1-5-18")
                        {
                            CloseHandle(hProcess);
                            return hToken;
                        }
                    }

                    CloseHandle(hToken);
                }
                CloseHandle(hProcess);
            }

            return IntPtr.Zero;
        }

        private static string GetTokenUserSID(IntPtr hToken)
        {
            uint token_length;
            string sid;

            if (!GetTokenInformation(hToken, TokenInformationClass.TokenUser, IntPtr.Zero, 0, out token_length))
            {
                int last_err = Marshal.GetLastWin32Error();
                if (last_err != 122) // ERROR_INSUFFICIENT_BUFFER
                    throw new Win32Exception(last_err, "Failed to get TokenUser length");
            }

            IntPtr token_information = Marshal.AllocHGlobal((int)token_length);
            try
            {
                if (!GetTokenInformation(hToken, TokenInformationClass.TokenUser, token_information, token_length, out token_length))
                    throw new Win32Exception("Failed to get TokenUser information");

                TOKEN_USER token_user = (TOKEN_USER)Marshal.PtrToStructure(token_information, typeof(TOKEN_USER));

                if (!ConvertSidToStringSidW(token_user.User.Sid, out sid))
                    throw new Win32Exception("Failed to get user SID");
            }
            finally
            {
                Marshal.FreeHGlobal(token_information);
            }

            return sid;
        }

        private static void GetProcessOutput(StreamReader stdoutStream, StreamReader stderrStream, out string stdout, out string stderr)
        {
            var sowait = new EventWaitHandle(false, EventResetMode.ManualReset);
            var sewait = new EventWaitHandle(false, EventResetMode.ManualReset);
            string so = null, se = null;
            ThreadPool.QueueUserWorkItem((s) =>
            {
                so = stdoutStream.ReadToEnd();
                sowait.Set();
            });
            ThreadPool.QueueUserWorkItem((s) =>
            {
                se = stderrStream.ReadToEnd();
                sewait.Set();
            });
            foreach (var wh in new WaitHandle[] { sowait, sewait })
                wh.WaitOne();
            stdout = so;
            stderr = se;
        }

        private static uint GetProcessExitCode(IntPtr processHandle)
        {
            new NativeWaitHandle(processHandle).WaitOne();
            uint exitCode;
            if (!GetExitCodeProcess(processHandle, out exitCode))
                throw new Win32Exception("Error getting process exit code");
            return exitCode;
        }

        private static IntPtr GetElevatedToken(IntPtr hToken)
        {
            uint requestedLength;

            IntPtr pTokenInfo = Marshal.AllocHGlobal(sizeof(int));

            try
            {
                if (!GetTokenInformation(hToken, TokenInformationClass.TokenElevationType, pTokenInfo, sizeof(int), out requestedLength))
                    throw new Win32Exception("Unable to get TokenElevationType");

                var tet = (TokenElevationType)Marshal.ReadInt32(pTokenInfo);

                // we already have the best token we can get, just use it
                if (tet != TokenElevationType.TokenElevationTypeLimited)
                    return hToken;

                GetTokenInformation(hToken, TokenInformationClass.TokenLinkedToken, IntPtr.Zero, 0, out requestedLength);

                IntPtr pLinkedToken = Marshal.AllocHGlobal((int)requestedLength);

                if (!GetTokenInformation(hToken, TokenInformationClass.TokenLinkedToken, pLinkedToken, requestedLength, out requestedLength))
                    throw new Win32Exception("Unable to get linked token");

                IntPtr linkedToken = Marshal.ReadIntPtr(pLinkedToken);

                Marshal.FreeHGlobal(pLinkedToken);

                return linkedToken;
            }
            finally
            {
                Marshal.FreeHGlobal(pTokenInfo);
            }
        }

        private static void GrantAccessToWindowStationAndDesktop(SecurityIdentifier account)
        {
            const int WindowStationAllAccess = 0x000f037f;
            GrantAccess(account, GetProcessWindowStation(), WindowStationAllAccess);
            const int DesktopRightsAllAccess = 0x000f01ff;
            GrantAccess(account, GetThreadDesktop(GetCurrentThreadId()), DesktopRightsAllAccess);
        }

        private static void GrantAccess(SecurityIdentifier account, IntPtr handle, int accessMask)
        {
            SafeHandle safeHandle = new NoopSafeHandle(handle);
            GenericSecurity security =
                new GenericSecurity(false, ResourceType.WindowObject, safeHandle, AccessControlSections.Access);
            security.AddAccessRule(
                new GenericAccessRule(account, accessMask, AccessControlType.Allow));
            security.Persist(safeHandle, AccessControlSections.Access);
        }

        private class GenericSecurity : NativeObjectSecurity
        {
            public GenericSecurity(bool isContainer, ResourceType resType, SafeHandle objectHandle, AccessControlSections sectionsRequested)
                : base(isContainer, resType, objectHandle, sectionsRequested) { }
            public new void Persist(SafeHandle handle, AccessControlSections includeSections) { base.Persist(handle, includeSections); }
            public new void AddAccessRule(AccessRule rule) { base.AddAccessRule(rule); }
            public override Type AccessRightType { get { throw new NotImplementedException(); } }
            public override AccessRule AccessRuleFactory(System.Security.Principal.IdentityReference identityReference, int accessMask, bool isInherited,
                InheritanceFlags inheritanceFlags, PropagationFlags propagationFlags, AccessControlType type)
            { throw new NotImplementedException(); }
            public override Type AccessRuleType { get { return typeof(AccessRule); } }
            public override AuditRule AuditRuleFactory(System.Security.Principal.IdentityReference identityReference, int accessMask, bool isInherited,
                InheritanceFlags inheritanceFlags, PropagationFlags propagationFlags, AuditFlags flags)
            { throw new NotImplementedException(); }
            public override Type AuditRuleType { get { return typeof(AuditRule); } }
        }

        private class NoopSafeHandle : SafeHandle
        {
            public NoopSafeHandle(IntPtr handle) : base(handle, false) { }
            public override bool IsInvalid { get { return false; } }
            protected override bool ReleaseHandle() { return true; }
        }

        private class GenericAccessRule : AccessRule
        {
            public GenericAccessRule(IdentityReference identity, int accessMask, AccessControlType type) :
                base(identity, accessMask, false, InheritanceFlags.None, PropagationFlags.None, type)
            { }
        }
    }
}
