#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CamelConversion

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$session_util = @'
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;

namespace Ansible
{
    public class SessionInfo
    {
        // SECURITY_LOGON_SESSION_DATA
        public UInt64 LogonId { get; internal set; }
        public Sid Account { get; internal set; }
        public string LoginDomain { get; internal set; }
        public string AuthenticationPackage { get; internal set; }
        public SECURITY_LOGON_TYPE LogonType { get; internal set; }
        public string LoginTime { get; internal set; }
        public string LogonServer { get; internal set; }
        public string DnsDomainName { get; internal set; }
        public string Upn { get; internal set; }
        public ArrayList UserFlags { get; internal set; }

        // TOKEN_STATISTICS
        public SECURITY_IMPERSONATION_LEVEL ImpersonationLevel { get; internal set; }
        public TOKEN_TYPE TokenType { get; internal set; }

        // TOKEN_GROUPS
        public ArrayList Groups { get; internal set; }
        public ArrayList Rights { get; internal set; }

        // TOKEN_MANDATORY_LABEL
        public Sid Label { get; internal set; }

        // TOKEN_PRIVILEGES
        public Hashtable Privileges { get; internal set; }
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

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct LSA_UNICODE_STRING
    {
        public UInt16 Length;
        public UInt16 MaximumLength;
        public IntPtr buffer;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct LUID
    {
        public UInt32 LowPart;
        public Int32 HighPart;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SECURITY_LOGON_SESSION_DATA
    {
        public UInt32 Size;
        public LUID LogonId;
        public LSA_UNICODE_STRING Username;
        public LSA_UNICODE_STRING LoginDomain;
        public LSA_UNICODE_STRING AuthenticationPackage;
        public SECURITY_LOGON_TYPE LogonType;
        public UInt32 Session;
        public IntPtr Sid;
        public UInt64 LoginTime;
        public LSA_UNICODE_STRING LogonServer;
        public LSA_UNICODE_STRING DnsDomainName;
        public LSA_UNICODE_STRING Upn;
        public UInt32 UserFlags;
        public LSA_LAST_INTER_LOGON_INFO LastLogonInfo;
        public LSA_UNICODE_STRING LogonScript;
        public LSA_UNICODE_STRING ProfilePath;
        public LSA_UNICODE_STRING HomeDirectory;
        public LSA_UNICODE_STRING HomeDirectoryDrive;
        public UInt64 LogoffTime;
        public UInt64 KickOffTime;
        public UInt64 PasswordLastSet;
        public UInt64 PasswordCanChange;
        public UInt64 PasswordMustChange;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct LSA_LAST_INTER_LOGON_INFO
    {
        public UInt64 LastSuccessfulLogon;
        public UInt64 LastFailedLogon;
        public UInt32 FailedAttemptCountSinceLastSuccessfulLogon;
    }

    public enum TOKEN_TYPE
    {
        TokenPrimary = 1,
        TokenImpersonation
    }

    public enum SECURITY_IMPERSONATION_LEVEL
    {
        SecurityAnonymous,
        SecurityIdentification,
        SecurityImpersonation,
        SecurityDelegation
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

    [Flags]
    public enum TokenGroupAttributes : uint
    {
        SE_GROUP_ENABLED = 0x00000004,
        SE_GROUP_ENABLED_BY_DEFAULT = 0x00000002,
        SE_GROUP_INTEGRITY = 0x00000020,
        SE_GROUP_INTEGRITY_ENABLED = 0x00000040,
        SE_GROUP_LOGON_ID = 0xC0000000,
        SE_GROUP_MANDATORY = 0x00000001,
        SE_GROUP_OWNER = 0x00000008,
        SE_GROUP_RESOURCE = 0x20000000,
        SE_GROUP_USE_FOR_DENY_ONLY = 0x00000010,
    }

    [Flags]
    public enum UserFlags : uint
    {
        LOGON_OPTIMIZED = 0x4000,
        LOGON_WINLOGON = 0x8000,
        LOGON_PKINIT = 0x10000,
        LOGON_NOT_OPTMIZED = 0x20000,
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SID_AND_ATTRIBUTES
    {
        public IntPtr Sid;
        public UInt32 Attributes;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct LUID_AND_ATTRIBUTES
    {
        public LUID Luid;
        public UInt32 Attributes;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TOKEN_GROUPS
    {
        public UInt32 GroupCount;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
        public SID_AND_ATTRIBUTES[] Groups;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TOKEN_MANDATORY_LABEL
    {
        public SID_AND_ATTRIBUTES Label;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TOKEN_STATISTICS
    {
        public LUID TokenId;
        public LUID AuthenticationId;
        public UInt64 ExpirationTime;
        public TOKEN_TYPE TokenType;
        public SECURITY_IMPERSONATION_LEVEL ImpersonationLevel;
        public UInt32 DynamicCharged;
        public UInt32 DynamicAvailable;
        public UInt32 GroupCount;
        public UInt32 PrivilegeCount;
        public LUID ModifiedId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TOKEN_PRIVILEGES
    {
        public UInt32 PrivilegeCount;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
        public LUID_AND_ATTRIBUTES[] Privileges;
    }

    public class AccessToken : IDisposable
    {
        public enum TOKEN_INFORMATION_CLASS
        {
            TokenUser = 1,
            TokenGroups,
            TokenPrivileges,
            TokenOwner,
            TokenPrimaryGroup,
            TokenDefaultDacl,
            TokenSource,
            TokenType,
            TokenImpersonationLevel,
            TokenStatistics,
            TokenRestrictedSids,
            TokenSessionId,
            TokenGroupsAndPrivileges,
            TokenSessionReference,
            TokenSandBoxInert,
            TokenAuditPolicy,
            TokenOrigin,
            TokenElevationType,
            TokenLinkedToken,
            TokenElevation,
            TokenHasRestrictions,
            TokenAccessInformation,
            TokenVirtualizationAllowed,
            TokenVirtualizationEnabled,
            TokenIntegrityLevel,
            TokenUIAccess,
            TokenMandatoryPolicy,
            TokenLogonSid,
            TokenIsAppContainer,
            TokenCapabilities,
            TokenAppContainerSid,
            TokenAppContainerNumber,
            TokenUserClaimAttributes,
            TokenDeviceClaimAttributes,
            TokenRestrictedUserClaimAttributes,
            TokenRestrictedDeviceClaimAttributes,
            TokenDeviceGroups,
            TokenRestrictedDeviceGroups,
            TokenSecurityAttributes,
            TokenIsRestricted,
            MaxTokenInfoClass
        }

        public IntPtr hToken = IntPtr.Zero;

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out IntPtr TokenHandle);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool GetTokenInformation(
            IntPtr TokenHandle,
            TOKEN_INFORMATION_CLASS TokenInformationClass,
            IntPtr TokenInformation,
            UInt32 TokenInformationLength,
            out UInt32 ReturnLength);

        public AccessToken(TokenAccessLevels tokenAccessLevels)
        {
            IntPtr currentProcess = GetCurrentProcess();
            if (!OpenProcessToken(currentProcess, tokenAccessLevels, out hToken))
                throw new Win32Exception("OpenProcessToken() for current process failed");
        }

        public IntPtr GetTokenInformation<T>(out T tokenInformation, TOKEN_INFORMATION_CLASS tokenClass)
        {
            UInt32 tokenLength = 0;
            GetTokenInformation(hToken, tokenClass, IntPtr.Zero, 0, out tokenLength);

            IntPtr infoPtr = Marshal.AllocHGlobal((int)tokenLength);

            if (!GetTokenInformation(hToken, tokenClass, infoPtr, tokenLength, out tokenLength))
                throw new Win32Exception(String.Format("GetTokenInformation() data for {0} failed", tokenClass.ToString()));

            tokenInformation = (T)Marshal.PtrToStructure(infoPtr, typeof(T));
            return infoPtr;
        }

        public void Dispose()
        {
            GC.SuppressFinalize(this);
        }

        ~AccessToken() { Dispose(); }
    }

    public class LsaHandle : IDisposable
    {
        [Flags]
        public enum DesiredAccess : uint
        {
            POLICY_VIEW_LOCAL_INFORMATION = 0x00000001,
            POLICY_VIEW_AUDIT_INFORMATION = 0x00000002,
            POLICY_GET_PRIVATE_INFORMATION = 0x00000004,
            POLICY_TRUST_ADMIN = 0x00000008,
            POLICY_CREATE_ACCOUNT = 0x00000010,
            POLICY_CREATE_SECRET = 0x00000020,
            POLICY_CREATE_PRIVILEGE = 0x00000040,
            POLICY_SET_DEFAULT_QUOTA_LIMITS = 0x00000080,
            POLICY_SET_AUDIT_REQUIREMENTS = 0x00000100,
            POLICY_AUDIT_LOG_ADMIN = 0x00000200,
            POLICY_SERVER_ADMIN = 0x00000400,
            POLICY_LOOKUP_NAMES = 0x00000800,
            POLICY_NOTIFICATION = 0x00001000
        }

        public IntPtr handle = IntPtr.Zero;

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern uint LsaOpenPolicy(
            LSA_UNICODE_STRING[] SystemName,
            ref LSA_OBJECT_ATTRIBUTES ObjectAttributes,
            DesiredAccess AccessMask,
            out IntPtr PolicyHandle);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern uint LsaClose(
            IntPtr ObjectHandle);

        [DllImport("advapi32.dll", SetLastError = false)]
        private static extern int LsaNtStatusToWinError(
            uint Status);

        [StructLayout(LayoutKind.Sequential)]
        public struct LSA_OBJECT_ATTRIBUTES
        {
            public int Length;
            public IntPtr RootDirectory;
            public IntPtr ObjectName;
            public int Attributes;
            public IntPtr SecurityDescriptor;
            public IntPtr SecurityQualityOfService;
        }

        public LsaHandle(DesiredAccess desiredAccess)
        {
            LSA_OBJECT_ATTRIBUTES lsaAttr;
            lsaAttr.RootDirectory = IntPtr.Zero;
            lsaAttr.ObjectName = IntPtr.Zero;
            lsaAttr.Attributes = 0;
            lsaAttr.SecurityDescriptor = IntPtr.Zero;
            lsaAttr.SecurityQualityOfService = IntPtr.Zero;
            lsaAttr.Length = Marshal.SizeOf(typeof(LSA_OBJECT_ATTRIBUTES));
            LSA_UNICODE_STRING[] system = new LSA_UNICODE_STRING[1];
            system[0].buffer = IntPtr.Zero;

            uint res = LsaOpenPolicy(system, ref lsaAttr, desiredAccess, out handle);
            if (res != 0)
                throw new Win32Exception(LsaNtStatusToWinError(res), "LsaOpenPolicy() failed");
        }

        public void Dispose()
        {
            if (handle != IntPtr.Zero)
            {
                LsaClose(handle);
                handle = IntPtr.Zero;
            }
            GC.SuppressFinalize(this);
        }

        ~LsaHandle() { Dispose(); }
    }

    public class Sid
    {
        public string SidString { get; internal set; }
        public string DomainName { get; internal set; }
        public string AccountName { get; internal set; }
        public SID_NAME_USE SidType { get; internal set; }

        public enum SID_NAME_USE
        {
            SidTypeUser = 1,
            SidTypeGroup,
            SidTypeDomain,
            SidTypeAlias,
            SidTypeWellKnownGroup,
            SidTypeDeletedAccount,
            SidTypeInvalid,
            SidTypeUnknown,
            SidTypeComputer,
            SidTypeLabel,
            SidTypeLogon,
        }

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool LookupAccountSid(
            string lpSystemName,
            [MarshalAs(UnmanagedType.LPArray)]
            byte[] Sid,
            StringBuilder lpName,
            ref UInt32 cchName,
            StringBuilder ReferencedDomainName,
            ref UInt32 cchReferencedDomainName,
            out SID_NAME_USE peUse);

        public Sid(IntPtr sidPtr)
        {
            SecurityIdentifier sid;
            try
            {
                sid = new SecurityIdentifier(sidPtr);
            }
            catch (Exception e)
            {
                throw new ArgumentException(String.Format("Failed to cast IntPtr to SecurityIdentifier: {0}", e));
            }

            SetSidInfo(sid);
        }

        public Sid(SecurityIdentifier sid)
        {
            SetSidInfo(sid);
        }

        public override string ToString()
        {
            return SidString;
        }

        private void SetSidInfo(SecurityIdentifier sid)
        {
            byte[] sidBytes = new byte[sid.BinaryLength];
            sid.GetBinaryForm(sidBytes, 0);

            StringBuilder lpName = new StringBuilder();
            UInt32 cchName = 0;
            StringBuilder referencedDomainName = new StringBuilder();
            UInt32 cchReferencedDomainName = 0;
            SID_NAME_USE peUse;
            LookupAccountSid(null, sidBytes, lpName, ref cchName, referencedDomainName, ref cchReferencedDomainName, out peUse);

            lpName.EnsureCapacity((int)cchName);
            referencedDomainName.EnsureCapacity((int)cchReferencedDomainName);

            SidString = sid.ToString();
            if (!LookupAccountSid(null, sidBytes, lpName, ref cchName, referencedDomainName, ref cchReferencedDomainName, out peUse))
            {
                int lastError = Marshal.GetLastWin32Error();

                if (lastError != 1332 && lastError != 1789) // Fails to lookup Logon Sid
                {
                    throw new Win32Exception(lastError, String.Format("LookupAccountSid() failed for SID: {0} {1}", sid.ToString(), lastError));
                }
                else if (SidString.StartsWith("S-1-5-5-"))
                {
                    AccountName = String.Format("LogonSessionId_{0}", SidString.Substring(8));
                    DomainName = "NT AUTHORITY";
                    SidType = SID_NAME_USE.SidTypeLogon;
                }
                else
                {
                    AccountName = null;
                    DomainName = null;
                    SidType = SID_NAME_USE.SidTypeUnknown;
                }
            }
            else
            {
                AccountName = lpName.ToString();
                DomainName = referencedDomainName.ToString();
                SidType = peUse;
            }
        }
    }

    public class SessionUtil
    {
        [DllImport("secur32.dll", SetLastError = false)]
        private static extern uint LsaFreeReturnBuffer(
            IntPtr Buffer);

        [DllImport("secur32.dll", SetLastError = false)]
        private static extern uint LsaEnumerateLogonSessions(
            out UInt64 LogonSessionCount,
            out IntPtr LogonSessionList);

        [DllImport("secur32.dll", SetLastError = false)]
        private static extern uint LsaGetLogonSessionData(
            IntPtr LogonId,
            out IntPtr ppLogonSessionData);

        [DllImport("advapi32.dll", SetLastError = false)]
        private static extern int LsaNtStatusToWinError(
            uint Status);

        [DllImport("advapi32", SetLastError = true)]
        private static extern uint LsaEnumerateAccountRights(
            IntPtr PolicyHandle,
            IntPtr AccountSid,
            out IntPtr UserRights,
            out UInt64 CountOfRights);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool LookupPrivilegeName(
            string lpSystemName,
            ref LUID lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        private const UInt32 SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001;
        private const UInt32 SE_PRIVILEGE_ENABLED = 0x00000002;
        private const UInt32 STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034;
        private const UInt32 STATUS_ACCESS_DENIED = 0xC0000022;

        public static SessionInfo GetSessionInfo()
        {
            AccessToken accessToken = new AccessToken(TokenAccessLevels.Query);

            // Get Privileges
            Hashtable privilegeInfo = new Hashtable();
            TOKEN_PRIVILEGES privileges;
            IntPtr privilegesPtr = accessToken.GetTokenInformation(out privileges, AccessToken.TOKEN_INFORMATION_CLASS.TokenPrivileges);
            LUID_AND_ATTRIBUTES[] luidAndAttributes = new LUID_AND_ATTRIBUTES[privileges.PrivilegeCount];
            try
            {
                PtrToStructureArray(luidAndAttributes, privilegesPtr.ToInt64() + Marshal.SizeOf(privileges.PrivilegeCount));
            }
            finally
            {
                Marshal.FreeHGlobal(privilegesPtr);
            }
            foreach (LUID_AND_ATTRIBUTES luidAndAttribute in luidAndAttributes)
            {
                LUID privLuid = luidAndAttribute.Luid;
                UInt32 privNameLen = 0;
                StringBuilder privName = new StringBuilder();
                LookupPrivilegeName(null, ref privLuid, null, ref privNameLen);
                privName.EnsureCapacity((int)(privNameLen + 1));
                if (!LookupPrivilegeName(null, ref privLuid, privName, ref privNameLen))
                    throw new Win32Exception("LookupPrivilegeName() failed");

                string state = "disabled";
                if ((luidAndAttribute.Attributes & SE_PRIVILEGE_ENABLED) == SE_PRIVILEGE_ENABLED)
                    state = "enabled";
                if ((luidAndAttribute.Attributes & SE_PRIVILEGE_ENABLED_BY_DEFAULT) == SE_PRIVILEGE_ENABLED_BY_DEFAULT)
                    state = "enabled-by-default";
                privilegeInfo.Add(privName.ToString(), state);
            }

            // Get Current Process LogonSID, User Rights and Groups
            ArrayList userRights = new ArrayList();
            ArrayList userGroups = new ArrayList();
            TOKEN_GROUPS groups;
            IntPtr groupsPtr = accessToken.GetTokenInformation(out groups, AccessToken.TOKEN_INFORMATION_CLASS.TokenGroups);
            SID_AND_ATTRIBUTES[] sidAndAttributes = new SID_AND_ATTRIBUTES[groups.GroupCount];
            LsaHandle lsaHandle = null;
            // We can only get rights if we are an admin
            if (new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator))
                lsaHandle = new LsaHandle(LsaHandle.DesiredAccess.POLICY_LOOKUP_NAMES);
            try
            {
                PtrToStructureArray(sidAndAttributes, groupsPtr.ToInt64() + IntPtr.Size);
                foreach (SID_AND_ATTRIBUTES sidAndAttribute in sidAndAttributes)
                {
                    TokenGroupAttributes attributes = (TokenGroupAttributes)sidAndAttribute.Attributes;
                    if (attributes.HasFlag(TokenGroupAttributes.SE_GROUP_ENABLED) && lsaHandle != null)
                    {
                        ArrayList rights = GetAccountRights(lsaHandle.handle, sidAndAttribute.Sid);
                        foreach (string right in rights)
                        {
                            // Includes both Privileges and Account Rights, only add the ones with Logon in the name
                            // https://msdn.microsoft.com/en-us/library/windows/desktop/bb545671(v=vs.85).aspx
                            if (!userRights.Contains(right) && right.Contains("Logon"))
                                userRights.Add(right);
                        }
                    }
                    // Do not include the Logon SID in the groups category
                    if (!attributes.HasFlag(TokenGroupAttributes.SE_GROUP_LOGON_ID))
                    {
                        Hashtable groupInfo = new Hashtable();
                        Sid group = new Sid(sidAndAttribute.Sid);
                        ArrayList groupAttributes = new ArrayList();
                        foreach (TokenGroupAttributes attribute in Enum.GetValues(typeof(TokenGroupAttributes)))
                        {
                            if (attributes.HasFlag(attribute))
                            {
                                string attributeName = attribute.ToString().Substring(9);
                                attributeName = attributeName.Replace('_', ' ');
                                attributeName = attributeName.First().ToString().ToUpper() + attributeName.Substring(1).ToLower();
                                groupAttributes.Add(attributeName);
                            }
                        }
                        // Using snake_case here as I can't generically convert all dict keys in PS (see Privileges)
                        groupInfo.Add("sid", group.SidString);
                        groupInfo.Add("domain_name", group.DomainName);
                        groupInfo.Add("account_name", group.AccountName);
                        groupInfo.Add("type", group.SidType);
                        groupInfo.Add("attributes", groupAttributes);
                        userGroups.Add(groupInfo);
                    }
                }
            }
            finally
            {
                Marshal.FreeHGlobal(groupsPtr);
                if (lsaHandle != null)
                    lsaHandle.Dispose();
            }

            // Get Integrity Level
            Sid integritySid = null;
            TOKEN_MANDATORY_LABEL mandatoryLabel;
            IntPtr mandatoryLabelPtr = accessToken.GetTokenInformation(out mandatoryLabel, AccessToken.TOKEN_INFORMATION_CLASS.TokenIntegrityLevel);
            Marshal.FreeHGlobal(mandatoryLabelPtr);
            integritySid = new Sid(mandatoryLabel.Label.Sid);

            // Get Token Statistics
            TOKEN_STATISTICS tokenStats;
            IntPtr tokenStatsPtr = accessToken.GetTokenInformation(out tokenStats, AccessToken.TOKEN_INFORMATION_CLASS.TokenStatistics);
            Marshal.FreeHGlobal(tokenStatsPtr);

            SessionInfo sessionInfo = GetSessionDataForLogonSession(tokenStats.AuthenticationId);
            sessionInfo.Groups = userGroups;
            sessionInfo.Label = integritySid;
            sessionInfo.ImpersonationLevel = tokenStats.ImpersonationLevel;
            sessionInfo.TokenType = tokenStats.TokenType;
            sessionInfo.Privileges = privilegeInfo;
            sessionInfo.Rights = userRights;
            return sessionInfo;
        }

        private static ArrayList GetAccountRights(IntPtr lsaHandle, IntPtr sid)
        {
            UInt32 res;
            ArrayList rights = new ArrayList();
            IntPtr userRightsPointer = IntPtr.Zero;
            UInt64 countOfRights = 0;

            res = LsaEnumerateAccountRights(lsaHandle, sid, out userRightsPointer, out countOfRights);
            if (res != 0 && res != STATUS_OBJECT_NAME_NOT_FOUND)
                throw new Win32Exception(LsaNtStatusToWinError(res), "LsaEnumerateAccountRights() failed");
            else if (res != STATUS_OBJECT_NAME_NOT_FOUND)
            {
                LSA_UNICODE_STRING[] userRights = new LSA_UNICODE_STRING[countOfRights];
                PtrToStructureArray(userRights, userRightsPointer.ToInt64());
                rights = new ArrayList();
                foreach (LSA_UNICODE_STRING right in userRights)
                    rights.Add(Marshal.PtrToStringUni(right.buffer));
            }

            return rights;
        }

        private static SessionInfo GetSessionDataForLogonSession(LUID logonSession)
        {
            uint res;
            UInt64 count = 0;
            IntPtr luidPtr = IntPtr.Zero;
            SessionInfo sessionInfo = null;
            UInt64 processDataId = ConvertLuidToUint(logonSession);

            res = LsaEnumerateLogonSessions(out count, out luidPtr);
            if (res != 0)
                throw new Win32Exception(LsaNtStatusToWinError(res), "LsaEnumerateLogonSessions() failed");
            Int64 luidAddr = luidPtr.ToInt64();

            try
            {
                for (UInt64 i = 0; i < count; i++)
                {
                    IntPtr dataPointer = IntPtr.Zero;
                    res = LsaGetLogonSessionData(luidPtr, out dataPointer);
                    if (res == STATUS_ACCESS_DENIED) // Non admins won't be able to get info for session's that are not their own
                    {
                        luidPtr = new IntPtr(luidPtr.ToInt64() + Marshal.SizeOf(typeof(LUID)));
                        continue;
                    }
                    else if (res != 0)
                        throw new Win32Exception(LsaNtStatusToWinError(res), String.Format("LsaGetLogonSessionData() failed {0}", res));

                    SECURITY_LOGON_SESSION_DATA sessionData = (SECURITY_LOGON_SESSION_DATA)Marshal.PtrToStructure(dataPointer, typeof(SECURITY_LOGON_SESSION_DATA));
                    UInt64 sessionDataid = ConvertLuidToUint(sessionData.LogonId);

                    if (sessionDataid == processDataId)
                    {
                        ArrayList userFlags = new ArrayList();
                        UserFlags flags = (UserFlags)sessionData.UserFlags;
                        foreach (UserFlags flag in Enum.GetValues(typeof(UserFlags)))
                        {
                            if (flags.HasFlag(flag))
                            {
                                string flagName = flag.ToString().Substring(6);
                                flagName = flagName.Replace('_', ' ');
                                flagName = flagName.First().ToString().ToUpper() + flagName.Substring(1).ToLower();
                                userFlags.Add(flagName);
                            }
                        }

                        sessionInfo = new SessionInfo()
                        {
                            AuthenticationPackage = Marshal.PtrToStringUni(sessionData.AuthenticationPackage.buffer),
                            DnsDomainName = Marshal.PtrToStringUni(sessionData.DnsDomainName.buffer),
                            LoginDomain = Marshal.PtrToStringUni(sessionData.LoginDomain.buffer),
                            LoginTime = ConvertIntegerToDateString(sessionData.LoginTime),
                            LogonId = ConvertLuidToUint(sessionData.LogonId),
                            LogonServer = Marshal.PtrToStringUni(sessionData.LogonServer.buffer),
                            LogonType = sessionData.LogonType,
                            Upn = Marshal.PtrToStringUni(sessionData.Upn.buffer),
                            UserFlags = userFlags,
                            Account = new Sid(sessionData.Sid)
                        };
                        break;
                    }
                    luidPtr = new IntPtr(luidPtr.ToInt64() + Marshal.SizeOf(typeof(LUID)));
                }
            }
            finally
            {
                LsaFreeReturnBuffer(new IntPtr(luidAddr));
            }

            if (sessionInfo == null)
                throw new Exception(String.Format("Could not find the data for logon session {0}", processDataId));
            return sessionInfo;
        }

        private static string ConvertIntegerToDateString(UInt64 time)
        {
            if (time == 0)
                return null;
            if (time > (UInt64)DateTime.MaxValue.ToFileTime())
                return null;

            DateTime dateTime = DateTime.FromFileTime((long)time);
            return dateTime.ToString("o");
        }

        private static UInt64 ConvertLuidToUint(LUID luid)
        {
            UInt32 low = luid.LowPart;
            UInt64 high = (UInt64)luid.HighPart;
            high = high << 32;
            UInt64 uintValue = (high | (UInt64)low);
            return uintValue;
        }

        private static void PtrToStructureArray<T>(T[] array, Int64 pointerAddress)
        {
            Int64 pointerOffset = pointerAddress;
            for (int i = 0; i < array.Length; i++, pointerOffset += Marshal.SizeOf(typeof(T)))
                array[i] = (T)Marshal.PtrToStructure(new IntPtr(pointerOffset), typeof(T));
        }

        public static IEnumerable<T> GetValues<T>()
        {
            return Enum.GetValues(typeof(T)).Cast<T>();
        }
    }
}
'@

$original_tmp = $env:TMP
$env:TMP = $_remote_tmp
Add-Type -TypeDefinition $session_util
$env:TMP = $original_tmp

$session_info = [Ansible.SessionUtil]::GetSessionInfo()

Function Convert-Value($value) {
    $new_value = $value
    if ($value -is [System.Collections.ArrayList]) {
        $new_value = [System.Collections.ArrayList]@()
        foreach ($list_value in $value) {
            $new_list_value = Convert-Value -value $list_value
            [void]$new_value.Add($new_list_value)
        }
    } elseif ($value -is [Hashtable]) {
        $new_value = @{}
        foreach ($entry in $value.GetEnumerator()) {
            $entry_value = Convert-Value -value $entry.Value
            # manually convert Sid type entry to remove the SidType prefix
            if ($entry.Name -eq "type") {
                $entry_value = $entry_value.Replace("SidType", "")
            }
            $new_value[$entry.Name] = $entry_value
        }
    } elseif ($value -is [Ansible.Sid]) {
        $new_value = @{
            sid = $value.SidString
            account_name = $value.AccountName
            domain_name = $value.DomainName
            type = $value.SidType.ToString().Replace("SidType", "")
        }
    } elseif ($value -is [Enum]) {
        $new_value = $value.ToString()
    }

    return ,$new_value
}

$result = @{
    changed = $false
}

$properties = [type][Ansible.SessionInfo]
foreach ($property in $properties.DeclaredProperties) {
    $property_name = $property.Name
    $property_value = $session_info.$property_name
    $snake_name = Convert-StringToSnakeCase -string $property_name

    $result.$snake_name = Convert-Value -value $property_value
}

Exit-Json -obj $result
