using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using Ansible.Process;
using System.Linq;

namespace Ansible.Become
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct KERB_S4U_LOGON
        {
            public UInt32 MessageType;
            public UInt32 Flags;
            public LSA_UNICODE_STRING ClientUpn;
            public LSA_UNICODE_STRING ClientRealm;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
        public struct LSA_STRING
        {
            public UInt16 Length;
            public UInt16 MaximumLength;
            [MarshalAs(UnmanagedType.LPStr)] public string Buffer;

            public static implicit operator string(LSA_STRING s)
            {
                return s.Buffer;
            }

            public static implicit operator LSA_STRING(string s)
            {
                if (s == null)
                    s = "";

                LSA_STRING lsaStr = new LSA_STRING
                {
                    Buffer = s,
                    Length = (UInt16)s.Length,
                    MaximumLength = (UInt16)(s.Length + 1),
                };
                return lsaStr;
            }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct LSA_UNICODE_STRING
        {
            public UInt16 Length;
            public UInt16 MaximumLength;
            public IntPtr Buffer;
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

        [StructLayout(LayoutKind.Sequential)]
        public struct SECURITY_LOGON_SESSION_DATA
        {
            public UInt32 Size;
            public LUID LogonId;
            public LSA_UNICODE_STRING UserName;
            public LSA_UNICODE_STRING LogonDomain;
            public LSA_UNICODE_STRING AuthenticationPackage;
            public SECURITY_LOGON_TYPE LogonType;
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
        public struct TOKEN_SOURCE
        {
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)] public char[] SourceName;
            public LUID SourceIdentifier;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_STATISTICS
        {
            public LUID TokenId;
            public LUID AuthenticationId;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_USER
        {
            public SID_AND_ATTRIBUTES User;
        }

        public enum LogonProvider
        {
            LOGON32_PROVIDER_DEFAULT = 0,
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

        public enum SECURITY_LOGON_TYPE
        {
            System = 0, // Used only by the Sytem account
            Interactive = 2,
            Network,
            Batch,
            Service,
            Proxy,
            Unlock,
            NetworkCleartext,
            NewCredentials,
            RemoteInteractive,
            CachedInteractive,
            CachedRemoteInteractive,
            CachedUnlock
        }

        public enum TOKEN_TYPE
        {
            TokenPrimary = 1,
            TokenImpersonation
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
            TokenStatistics = 10,
            TokenElevationType = 18,
            TokenLinkedToken = 19,
        }
    }

    internal class NativeMethods
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool AllocateLocallyUniqueId(
            out NativeHelpers.LUID Luid);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CreateProcessWithTokenW(
            SafeNativeHandle hToken,
            LogonFlags dwLogonFlags,
            [MarshalAs(UnmanagedType.LPWStr)] string lpApplicationName,
            StringBuilder lpCommandLine,
            Process.NativeHelpers.ProcessCreationFlags dwCreationFlags,
            SafeMemoryBuffer lpEnvironment,
            [MarshalAs(UnmanagedType.LPWStr)] string lpCurrentDirectory,
            Process.NativeHelpers.STARTUPINFOEX lpStartupInfo,
            out Process.NativeHelpers.PROCESS_INFORMATION lpProcessInformation);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool DuplicateTokenEx(
            SafeNativeHandle hExistingToken,
            TokenAccessLevels dwDesiredAccess,
            IntPtr lpTokenAttributes,
            NativeHelpers.SECURITY_IMPERSONATION_LEVEL ImpersonationLevel,
            NativeHelpers.TOKEN_TYPE TokenType,
            out SafeNativeHandle phNewToken);

        [DllImport("kernel32.dll")]
        public static extern UInt32 GetCurrentThreadId();

        [DllImport("user32.dll", SetLastError = true)]
        public static extern NoopSafeHandle GetProcessWindowStation();

        [DllImport("user32.dll", SetLastError = true)]
        public static extern NoopSafeHandle GetThreadDesktop(
            UInt32 dwThreadId);

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
            NativeHelpers.LogonProvider dwLogonProvider,
            out SafeNativeHandle phToken);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupPrivilegeNameW(
            string lpSystemName,
            ref NativeHelpers.LUID lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        [DllImport("secur32.dll", SetLastError = true)]
        public static extern UInt32 LsaDeregisterLogonProcess(
            IntPtr LsaHandle);

        [DllImport("secur32.dll", SetLastError = true)]
        public static extern UInt32 LsaEnumerateLogonSessions(
            out UInt32 LogonSessionCount,
            out SafeLsaMemoryBuffer LogonSessionList);

        [DllImport("secur32.dll", SetLastError = true)]
        public static extern UInt32 LsaFreeReturnBuffer(
            IntPtr Buffer);

        [DllImport("secur32.dll", SetLastError = true)]
        public static extern UInt32 LsaGetLogonSessionData(
            IntPtr LogonId,
            out SafeLsaMemoryBuffer ppLogonSessionData);

        [DllImport("secur32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern UInt32 LsaLogonUser(
            SafeLsaHandle LsaHandle,
            NativeHelpers.LSA_STRING OriginName,
            LogonType LogonType,
            UInt32 AuthenticationPackage,
            IntPtr AuthenticationInformation,
            UInt32 AuthenticationInformationLength,
            IntPtr LocalGroups,
            NativeHelpers.TOKEN_SOURCE SourceContext,
            out SafeLsaMemoryBuffer ProfileBuffer,
            out UInt32 ProfileBufferLength,
            out NativeHelpers.LUID LogonId,
            out SafeNativeHandle Token,
            out IntPtr Quotas,
            out UInt32 SubStatus);

        [DllImport("secur32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern UInt32 LsaLookupAuthenticationPackage(
            SafeLsaHandle LsaHandle,
            NativeHelpers.LSA_STRING PackageName,
            out UInt32 AuthenticationPackage);

        [DllImport("advapi32.dll")]
        public static extern UInt32 LsaNtStatusToWinError(
            UInt32 Status);

        [DllImport("secur32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern UInt32 LsaRegisterLogonProcess(
            NativeHelpers.LSA_STRING LogonProcessName,
            out SafeLsaHandle LsaHandle,
            out IntPtr SecurityMode);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern SafeNativeHandle OpenProcess(
            NativeHelpers.ProcessAccessFlags dwDesiredAccess,
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

    internal class SafeLsaHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeLsaHandle() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            UInt32 res = NativeMethods.LsaDeregisterLogonProcess(handle);
            return res == 0;
        }
    }

    internal class SafeLsaMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeLsaMemoryBuffer() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            UInt32 res = NativeMethods.LsaFreeReturnBuffer(handle);
            return res == 0;
        }
    }

    internal class SafeNativeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeNativeHandle() : base(true) { }
        public SafeNativeHandle(IntPtr handle) : base(true) { this.handle = handle; }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            return NativeMethods.CloseHandle(handle);
        }
    }

    internal class NoopSafeHandle : SafeHandle
    {
        public NoopSafeHandle() : base(IntPtr.Zero, false) { }
        public override bool IsInvalid { get { return false; } }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle() { return true; }
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

    public class BecomeUtil
    {
        private static List<string> SERVICE_SIDS = new List<string>()
        {
            "S-1-5-18", // NT AUTHORITY\SYSTEM
            "S-1-5-19", // NT AUTHORITY\LocalService
            "S-1-5-20"  // NT AUTHORITY\NetworkService
        };
        private static int WINDOWS_STATION_ALL_ACCESS = 0x000F037F;
        private static int DESKTOP_RIGHTS_ALL_ACCESS = 0x000F01FF;

        public static Result CreateProcessAsUser(string username, string password, string command)
        {
            return CreateProcessAsUser(username, password, LogonFlags.LOGON_WITH_PROFILE, LogonType.LOGON32_LOGON_INTERACTIVE,
                 null, command, null, null, "");
        }

        public static Result CreateProcessAsUser(string username, string password, LogonFlags logonFlags, LogonType logonType,
            string lpApplicationName, string lpCommandLine, string lpCurrentDirectory, IDictionary environment,
            string stdin)
        {
            byte[] stdinBytes;
            if (String.IsNullOrEmpty(stdin))
                stdinBytes = new byte[0];
            else
            {
                if (!stdin.EndsWith(Environment.NewLine))
                    stdin += Environment.NewLine;
                stdinBytes = new UTF8Encoding(false).GetBytes(stdin);
            }
            return CreateProcessAsUser(username, password, logonFlags, logonType, lpApplicationName, lpCommandLine,
                lpCurrentDirectory, environment, stdinBytes);
        }

        /// <summary>
        /// Creates a process as another user account. This method will attempt to run as another user with the
        /// highest possible permissions available. The main privilege required is the SeDebugPrivilege, without
        /// this privilege you can only run as a local or domain user if the username and password is specified.
        /// </summary>
        /// <param name="username">The username of the runas user</param>
        /// <param name="password">The password of the runas user</param>
        /// <param name="logonFlags">LogonFlags to control how to logon a user when the password is specified</param>
        /// <param name="logonType">Controls what type of logon is used, this only applies when the password is specified</param>
        /// <param name="lpApplicationName">The name of the executable or batch file to executable</param>
        /// <param name="lpCommandLine">The command line to execute, typically this includes lpApplication as the first argument</param>
        /// <param name="lpCurrentDirectory">The full path to the current directory for the process, null will have the same cwd as the calling process</param>
        /// <param name="environment">A dictionary of key/value pairs to define the new process environment</param>
        /// <param name="stdin">Bytes sent to the stdin pipe</param>
        /// <returns>Ansible.Process.Result object that contains the command output and return code</returns>
        public static Result CreateProcessAsUser(string username, string password, LogonFlags logonFlags, LogonType logonType,
            string lpApplicationName, string lpCommandLine, string lpCurrentDirectory, IDictionary environment, byte[] stdin)
        {
            // While we use STARTUPINFOEX having EXTENDED_STARTUPINFO_PRESENT causes a parameter validation error
            Process.NativeHelpers.ProcessCreationFlags creationFlags = Process.NativeHelpers.ProcessCreationFlags.CREATE_UNICODE_ENVIRONMENT;
            Process.NativeHelpers.PROCESS_INFORMATION pi = new Process.NativeHelpers.PROCESS_INFORMATION();
            Process.NativeHelpers.STARTUPINFOEX si = new Process.NativeHelpers.STARTUPINFOEX();
            si.startupInfo.dwFlags = Process.NativeHelpers.StartupInfoFlags.USESTDHANDLES;

            SafeFileHandle stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinRead, stdinWrite;
            ProcessUtil.CreateStdioPipes(si, out stdoutRead, out stdoutWrite, out stderrRead, out stderrWrite,
                out stdinRead, out stdinWrite);
            FileStream stdinStream = new FileStream(stdinWrite, FileAccess.Write);

            // $null from PowerShell ends up as an empty string, we need to convert back as an empty string doesn't
            // make sense for these parameters
            if (lpApplicationName == "")
                lpApplicationName = null;

            if (lpCurrentDirectory == "")
                lpCurrentDirectory = null;

            using (SafeMemoryBuffer lpEnvironment = ProcessUtil.CreateEnvironmentPointer(environment))
            {
                // A user may have 2 tokens, 1 limited and 1 elevated. GetUserToken will try and get both but we will
                // only find out if the elevated token is valid when running here.
                List<SafeNativeHandle> userTokens = GetUserTokens(username, password, logonType);

                bool launchSuccess = false;
                StringBuilder commandLine = new StringBuilder(lpCommandLine);
                foreach (SafeNativeHandle token in userTokens)
                {
                    if (NativeMethods.CreateProcessWithTokenW(token, logonFlags, lpApplicationName, commandLine,
                        creationFlags, lpEnvironment, lpCurrentDirectory, si, out pi))
                    {
                        launchSuccess = true;
                        break;
                    }
                }

                if (!launchSuccess)
                    throw new Win32Exception("CreateProcessWithTokenW() failed");
            }
            return ProcessUtil.WaitProcess(stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinStream, stdin, pi.hProcess);
        }

        private static List<SafeNativeHandle> GetUserTokens(string username, string password, LogonType logonType)
        {
            List<SafeNativeHandle> userTokens = new List<SafeNativeHandle>();

            SafeNativeHandle systemToken = null;
            bool impersonated = false;
            string becomeSid = username;
            if (logonType != LogonType.LOGON32_LOGON_NEW_CREDENTIALS)
            {
                // If prefixed with .\, we are becoming a local account, strip the prefix
                if (username.StartsWith(".\\"))
                    username = username.Substring(2);

                NTAccount account = new NTAccount(username);
                becomeSid = ((SecurityIdentifier)account.Translate(typeof(SecurityIdentifier))).Value;

                // Grant access to the current Windows Station and Desktop to the become user
                GrantAccessToWindowStationAndDesktop(account);

                // Try and impersonate a SYSTEM token, we need a SYSTEM token to either become a well known service
                // account or have administrative rights on the become access token.
                systemToken = GetPrimaryTokenForUser(new SecurityIdentifier("S-1-5-18"), new List<string>() { "SeTcbPrivilege" });
                if (systemToken != null)
                    impersonated = NativeMethods.ImpersonateLoggedOnUser(systemToken);
            }

            // We require impersonation if becoming a service sid or becoming a user without a password
            if (!impersonated && (SERVICE_SIDS.Contains(becomeSid) || String.IsNullOrEmpty(password)))
                throw new Exception("Failed to get token for NT AUTHORITY\\SYSTEM required for become as a service account or an account without a password");

            try
            {
                if (becomeSid == "S-1-5-18")
                    userTokens.Add(systemToken);
                // Cannot use String.IsEmptyOrNull() as an empty string is an account that doesn't have a pass.
                // We only use S4U if no password was defined or it was null
                else if (!SERVICE_SIDS.Contains(becomeSid) && password == null && logonType != LogonType.LOGON32_LOGON_NEW_CREDENTIALS)
                {
                    // If no password was specified, try and duplicate an existing token for that user or use S4U to
                    // generate one without network credentials
                    SecurityIdentifier sid = new SecurityIdentifier(becomeSid);
                    SafeNativeHandle becomeToken = GetPrimaryTokenForUser(sid);
                    if (becomeToken != null)
                    {
                        userTokens.Add(GetElevatedToken(becomeToken));
                        userTokens.Add(becomeToken);
                    }
                    else
                    {
                        becomeToken = GetS4UTokenForUser(sid, logonType);
                        userTokens.Add(becomeToken);
                    }
                }
                else
                {
                    string domain = null;
                    switch (becomeSid)
                    {
                        case "S-1-5-19":
                            logonType = LogonType.LOGON32_LOGON_SERVICE;
                            domain = "NT AUTHORITY";
                            username = "LocalService";
                            break;
                        case "S-1-5-20":
                            logonType = LogonType.LOGON32_LOGON_SERVICE;
                            domain = "NT AUTHORITY";
                            username = "NetworkService";
                            break;
                        default:
                            // Trying to become a local or domain account
                            if (username.Contains(@"\"))
                            {
                                string[] userSplit = username.Split(new char[1] { '\\' }, 2);
                                domain = userSplit[0];
                                username = userSplit[1];
                            }
                            else if (!username.Contains("@"))
                                domain = ".";
                            break;
                    }

                    SafeNativeHandle hToken;
                    if (!NativeMethods.LogonUserW(username, domain, password, logonType,
                        NativeHelpers.LogonProvider.LOGON32_PROVIDER_DEFAULT, out hToken))
                    {
                        throw new Win32Exception("LogonUserW() failed");
                    }

                    // Get the elevated token for a local/domain accounts only
                    if (!SERVICE_SIDS.Contains(becomeSid))
                        userTokens.Add(GetElevatedToken(hToken));
                    userTokens.Add(hToken);
                }
            }
            finally
            {
                if (impersonated)
                    NativeMethods.RevertToSelf();
            }

            return userTokens;
        }

        private static SafeNativeHandle GetPrimaryTokenForUser(SecurityIdentifier sid, List<string> requiredPrivileges = null)
        {
            NativeHelpers.ProcessAccessFlags accessFlags = NativeHelpers.ProcessAccessFlags.PROCESS_QUERY_INFORMATION;
            // According to CreateProcessWithTokenW we require a token with
            //  TOKEN_QUERY, TOKEN_DUPLICATE and TOKEN_ASSIGN_PRIMARY
            // Also add in TOKEN_IMPERSONATE so we can get an impersonated token
            TokenAccessLevels dwAccess = TokenAccessLevels.Query |
                TokenAccessLevels.Duplicate |
                TokenAccessLevels.AssignPrimary |
                TokenAccessLevels.Impersonate;

            foreach (System.Diagnostics.Process process in System.Diagnostics.Process.GetProcesses())
            {
                using (process)
                {
                    using (SafeNativeHandle hProcess = NativeMethods.OpenProcess(accessFlags, false, (UInt32)process.Id))
                    {
                        if (hProcess.IsInvalid)
                            continue;

                        SafeNativeHandle hToken;
                        NativeMethods.OpenProcessToken(hProcess, dwAccess, out hToken);
                        if (hToken.IsInvalid)
                            continue;

                        using (hToken)
                        {
                            if (!sid.Equals(GetTokenUserSID(hToken)))
                                continue;

                            // Filter out any Network logon tokens, using become with that is useless when S4U
                            // can give us a Batch logon
                            NativeHelpers.SECURITY_LOGON_TYPE tokenLogonType = GetTokenLogonType(hToken);
                            if (tokenLogonType == NativeHelpers.SECURITY_LOGON_TYPE.Network)
                                continue;

                            // Check that the required privileges are on the token
                            if (requiredPrivileges != null)
                            {
                                List<string> actualPrivileges = GetTokenPrivileges(hToken);
                                int missing = requiredPrivileges.Where(x => !actualPrivileges.Contains(x)).Count();
                                if (missing > 0)
                                    continue;
                            }

                            SafeNativeHandle dupToken;
                            if (!NativeMethods.DuplicateTokenEx(hToken, TokenAccessLevels.MaximumAllowed,
                                IntPtr.Zero, NativeHelpers.SECURITY_IMPERSONATION_LEVEL.SecurityImpersonation,
                                NativeHelpers.TOKEN_TYPE.TokenPrimary, out dupToken))
                            {
                                continue;
                            }

                            return dupToken;
                        }
                    }
                }
            }

            return null;
        }

        private static SafeNativeHandle GetS4UTokenForUser(SecurityIdentifier sid, LogonType logonType)
        {
            NTAccount becomeAccount = (NTAccount)sid.Translate(typeof(NTAccount));
            string[] userSplit = becomeAccount.Value.Split(new char[1] { '\\' }, 2);
            string domainName = userSplit[0];
            string username = userSplit[1];
            bool domainUser = domainName.ToLowerInvariant() != Environment.MachineName.ToLowerInvariant();

            NativeHelpers.LSA_STRING logonProcessName = "ansible";
            SafeLsaHandle lsaHandle;
            IntPtr securityMode;
            UInt32 res = NativeMethods.LsaRegisterLogonProcess(logonProcessName, out lsaHandle, out securityMode);
            if (res != 0)
                throw new Win32Exception((int)NativeMethods.LsaNtStatusToWinError(res), "LsaRegisterLogonProcess() failed");

            using (lsaHandle)
            {
                NativeHelpers.LSA_STRING packageName = domainUser ? "Kerberos" : "MICROSOFT_AUTHENTICATION_PACKAGE_V1_0";
                UInt32 authPackage;
                res = NativeMethods.LsaLookupAuthenticationPackage(lsaHandle, packageName, out authPackage);
                if (res != 0)
                    throw new Win32Exception((int)NativeMethods.LsaNtStatusToWinError(res),
                        String.Format("LsaLookupAuthenticationPackage({0}) failed", (string)packageName));

                int usernameLength = username.Length * sizeof(char);
                int domainLength = domainName.Length * sizeof(char);
                int authInfoLength = (Marshal.SizeOf(typeof(NativeHelpers.KERB_S4U_LOGON)) + usernameLength + domainLength);
                IntPtr authInfo = Marshal.AllocHGlobal((int)authInfoLength);
                try
                {
                    IntPtr usernamePtr = IntPtr.Add(authInfo, Marshal.SizeOf(typeof(NativeHelpers.KERB_S4U_LOGON)));
                    IntPtr domainPtr = IntPtr.Add(usernamePtr, usernameLength);

                    // KERB_S4U_LOGON has the same structure as MSV1_0_S4U_LOGON (local accounts)
                    NativeHelpers.KERB_S4U_LOGON s4uLogon = new NativeHelpers.KERB_S4U_LOGON
                    {
                        MessageType = 12,  // KerbS4ULogon
                        Flags = 0,
                        ClientUpn = new NativeHelpers.LSA_UNICODE_STRING
                        {
                            Length = (UInt16)usernameLength,
                            MaximumLength = (UInt16)usernameLength,
                            Buffer = usernamePtr,
                        },
                        ClientRealm = new NativeHelpers.LSA_UNICODE_STRING
                        {
                            Length = (UInt16)domainLength,
                            MaximumLength = (UInt16)domainLength,
                            Buffer = domainPtr,
                        },
                    };
                    Marshal.StructureToPtr(s4uLogon, authInfo, false);
                    Marshal.Copy(username.ToCharArray(), 0, usernamePtr, username.Length);
                    Marshal.Copy(domainName.ToCharArray(), 0, domainPtr, domainName.Length);

                    NativeHelpers.LUID sourceLuid;
                    if (!NativeMethods.AllocateLocallyUniqueId(out sourceLuid))
                        throw new Win32Exception("AllocateLocallyUniqueId() failed");

                    NativeHelpers.TOKEN_SOURCE tokenSource = new NativeHelpers.TOKEN_SOURCE
                    {
                        SourceName = "ansible\0".ToCharArray(),
                        SourceIdentifier = sourceLuid,
                    };

                    // Only Batch or Network will work with S4U, prefer Batch but use Network if asked
                    LogonType lsaLogonType = logonType == LogonType.LOGON32_LOGON_NETWORK
                        ? LogonType.LOGON32_LOGON_NETWORK
                        : LogonType.LOGON32_LOGON_BATCH;
                    SafeLsaMemoryBuffer profileBuffer;
                    UInt32 profileBufferLength;
                    NativeHelpers.LUID logonId;
                    SafeNativeHandle hToken;
                    IntPtr quotas;
                    UInt32 subStatus;

                    res = NativeMethods.LsaLogonUser(lsaHandle, logonProcessName, lsaLogonType, authPackage,
                        authInfo, (UInt32)authInfoLength, IntPtr.Zero, tokenSource, out profileBuffer, out profileBufferLength,
                        out logonId, out hToken, out quotas, out subStatus);
                    if (res != 0)
                        throw new Win32Exception((int)NativeMethods.LsaNtStatusToWinError(res),
                            String.Format("LsaLogonUser() failed with substatus {0}", subStatus));

                    profileBuffer.Dispose();
                    return hToken;
                }
                finally
                {
                    Marshal.FreeHGlobal(authInfo);
                }
            }
        }

        private static SafeNativeHandle GetElevatedToken(SafeNativeHandle hToken)
        {
            // First determine if the current token is a limited token
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenElevationType))
            {
                NativeHelpers.TokenElevationType tet = (NativeHelpers.TokenElevationType)Marshal.ReadInt32(tokenInfo.DangerousGetHandle());
                // We already have the best token we can get, just use it
                if (tet != NativeHelpers.TokenElevationType.TokenElevationTypeLimited)
                    return hToken;
            }

            // We have a limited token, get the linked elevated token
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenLinkedToken))
                return new SafeNativeHandle(Marshal.ReadIntPtr(tokenInfo.DangerousGetHandle()));
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

        private static SecurityIdentifier GetTokenUserSID(SafeNativeHandle hToken)
        {
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenUser))
            {
                NativeHelpers.TOKEN_USER tokenUser = (NativeHelpers.TOKEN_USER)Marshal.PtrToStructure(tokenInfo.DangerousGetHandle(),
                    typeof(NativeHelpers.TOKEN_USER));
                return new SecurityIdentifier(tokenUser.User.Sid);
            }
        }

        private static NativeHelpers.SECURITY_LOGON_TYPE GetTokenLogonType(SafeNativeHandle hToken)
        {
            UInt64 tokenLuidId;
            using (SafeMemoryBuffer tokenInfo = GetTokenInformation(hToken, NativeHelpers.TokenInformationClass.TokenStatistics))
            {
                NativeHelpers.TOKEN_STATISTICS stats = (NativeHelpers.TOKEN_STATISTICS)Marshal.PtrToStructure(
                    tokenInfo.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_STATISTICS));
                tokenLuidId = (UInt64)stats.AuthenticationId;
            }

            // Default to Network, if we weren't able to get the actual type treat it as an error and assume
            // we don't want to run a process with the token
            NativeHelpers.SECURITY_LOGON_TYPE logonType = NativeHelpers.SECURITY_LOGON_TYPE.Network;
            UInt32 sessionCount;
            SafeLsaMemoryBuffer sessionPtr;
            UInt32 res = NativeMethods.LsaEnumerateLogonSessions(out sessionCount, out sessionPtr);
            if (res != 0)
                throw new Win32Exception((int)NativeMethods.LsaNtStatusToWinError(res), "LsaEnumerateLogonSession() failed");
            using (sessionPtr)
            {
                for (IntPtr p = sessionPtr.DangerousGetHandle();
                    p != IntPtr.Add(sessionPtr.DangerousGetHandle(), (int)(Marshal.SizeOf(typeof(NativeHelpers.LUID)) * sessionCount));
                    p = IntPtr.Add(p, Marshal.SizeOf(typeof(NativeHelpers.LUID))))
                {
                    SafeLsaMemoryBuffer sessionDataPtr;
                    res = NativeMethods.LsaGetLogonSessionData(p, out sessionDataPtr);
                    if (res != 0)
                        continue;

                    using (sessionDataPtr)
                    {
                        NativeHelpers.SECURITY_LOGON_SESSION_DATA sessionData = (NativeHelpers.SECURITY_LOGON_SESSION_DATA)Marshal.PtrToStructure(
                            sessionDataPtr.DangerousGetHandle(), typeof(NativeHelpers.SECURITY_LOGON_SESSION_DATA));
                        UInt64 sessionId = (UInt64)sessionData.LogonId;
                        if (sessionId == tokenLuidId)
                        {
                            logonType = sessionData.LogonType;
                            break;
                        }
                    }
                }
            }

            return logonType;
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

        private static void GrantAccessToWindowStationAndDesktop(IdentityReference account)
        {
            GrantAccess(account, NativeMethods.GetProcessWindowStation(), WINDOWS_STATION_ALL_ACCESS);
            GrantAccess(account, NativeMethods.GetThreadDesktop(NativeMethods.GetCurrentThreadId()), DESKTOP_RIGHTS_ALL_ACCESS);
        }

        private static void GrantAccess(IdentityReference account, NoopSafeHandle handle, int accessMask)
        {
            GenericSecurity security = new GenericSecurity(false, ResourceType.WindowObject, handle, AccessControlSections.Access);
            security.AddAccessRule(new GenericAccessRule(account, accessMask, AccessControlType.Allow));
            security.Persist(handle, AccessControlSections.Access);
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

        private class GenericAccessRule : AccessRule
        {
            public GenericAccessRule(IdentityReference identity, int accessMask, AccessControlType type) :
                base(identity, accessMask, false, InheritanceFlags.None, PropagationFlags.None, type)
            { }
        }
    }
}
