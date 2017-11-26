#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CamelConversion

# TODO: Remove this when win_whoami is in as this is a cut-down version
# https://github.com/ansible/ansible/pull/33295

$ErrorActionPreference = "Stop"

$session_util = @'
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;

namespace Ansible
{
    public class SessionInfo
    {
        public Sid Account { get; internal set; }
        public SECURITY_LOGON_TYPE LogonType { get; internal set; }
        public Sid Label { get; internal set; }
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

    [StructLayout(LayoutKind.Sequential)]
    public struct SID_AND_ATTRIBUTES
    {
        public IntPtr Sid;
        public UInt32 Attributes;
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
        public int TokenType;
        public int ImpersonationLevel;
        public UInt32 DynamicCharged;
        public UInt32 DynamicAvailable;
        public UInt32 GroupCount;
        public UInt32 PrivilegeCount;
        public LUID ModifiedId;
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

                if (lastError != 1332) // Fails to lookup Logon Sid
                {
                    throw new Win32Exception(lastError, String.Format("LookupAccountSid() failed for SID: {0}", sid.ToString()));
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

        private const UInt32 STATUS_ACCESS_DENIED = 0xC0000022;

        public static SessionInfo GetSessionInfo()
        {
            AccessToken accessToken = new AccessToken(TokenAccessLevels.Query);

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
            sessionInfo.Label = integritySid;
            return sessionInfo;
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
                        sessionInfo = new SessionInfo()
                        {
                            LogonType = sessionData.LogonType,
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

        private static UInt64 ConvertLuidToUint(LUID luid)
        {
            UInt32 low = luid.LowPart;
            UInt64 high = (UInt64)luid.HighPart;
            high = high << 32;
            UInt64 uintValue = (high | (UInt64)low);
            return uintValue;
        }
    }
}
'@

Add-Type -TypeDefinition $session_util
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
