#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Become

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

Function Assert-Equals {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)][AllowNull()]$Actual,
        [Parameter(Mandatory=$true, Position=0)][AllowNull()]$Expected
    )

    $matched = $false
    if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array]) {
        $Actual.Count | Assert-Equals -Expected $Expected.Count
        for ($i = 0; $i -lt $Actual.Count; $i++) {
            $actual_value = $Actual[$i]
            $expected_value = $Expected[$i]
            Assert-Equals -Actual $actual_value -Expected $expected_value
        }
        $matched = $true
    } else {
        $matched = $Actual -ceq $Expected
    }

    if (-not $matched) {
        if ($Actual -is [PSObject]) {
            $Actual = $Actual.ToString()
        }

        $call_stack = (Get-PSCallStack)[1]
        $module.Result.test = $test
        $module.Result.actual = $Actual
        $module.Result.expected = $Expected
        $module.Result.line = $call_stack.ScriptLineNumber
        $module.Result.method = $call_stack.Position.Text
        $module.FailJson("AssertionError: actual != expected")
    }
}

# Would be great to move win_whomai out into it's own module util and share the
# code here, for now just rely on a cut down version
$test_whoami = {
    Add-Type -TypeDefinition @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;

namespace Ansible
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct LSA_UNICODE_STRING
        {
            public UInt16 Length;
            public UInt16 MaximumLength;
            public IntPtr Buffer;

            public override string ToString()
            {
                return Marshal.PtrToStringUni(Buffer, Length / sizeof(char));
            }
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
        public struct TOKEN_MANDATORY_LABEL
        {
            public SID_AND_ATTRIBUTES Label;
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

        public enum TokenInformationClass
        {
            TokenUser = 1,
            TokenSource = 7,
            TokenStatistics = 10,
            TokenIntegrityLevel = 25,
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("kernel32.dll")]
        public static extern SafeNativeHandle GetCurrentProcess();

        [DllImport("userenv.dll", SetLastError = true)]
        public static extern bool GetProfileType(
            out UInt32 dwFlags);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool GetTokenInformation(
            SafeNativeHandle TokenHandle,
            NativeHelpers.TokenInformationClass TokenInformationClass,
            SafeMemoryBuffer TokenInformation,
            UInt32 TokenInformationLength,
            out UInt32 ReturnLength);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupAccountSid(
            string lpSystemName,
            IntPtr Sid,
            StringBuilder lpName,
            ref UInt32 cchName,
            StringBuilder ReferencedDomainName,
            ref UInt32 cchReferencedDomainName,
            out UInt32 peUse);

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

        [DllImport("advapi32.dll")]
        public static extern UInt32 LsaNtStatusToWinError(
            UInt32 Status);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool OpenProcessToken(
            SafeNativeHandle ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out SafeNativeHandle TokenHandle);
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

    public class Logon
    {
        public string AuthenticationPackage { get; internal set; }
        public string LogonType { get; internal set; }
        public string MandatoryLabelName { get; internal set; }
        public SecurityIdentifier MandatoryLabelSid { get; internal set; }
        public bool ProfileLoaded { get; internal set; }
        public string SourceName { get; internal set; }
        public string UserName { get; internal set; }
        public SecurityIdentifier UserSid { get; internal set; }

        public Logon()
        {
            using (SafeNativeHandle process = NativeMethods.GetCurrentProcess())
            {
                TokenAccessLevels dwAccess = TokenAccessLevels.Query | TokenAccessLevels.QuerySource;

                SafeNativeHandle hToken;
                NativeMethods.OpenProcessToken(process, dwAccess, out hToken);
                using (hToken)
                {
                    SetLogonSessionData(hToken);
                    SetTokenMandatoryLabel(hToken);
                    SetTokenSource(hToken);
                    SetTokenUser(hToken);
                }
            }
            SetProfileLoaded();
        }

        private void SetLogonSessionData(SafeNativeHandle hToken)
        {
            NativeHelpers.TokenInformationClass tokenClass = NativeHelpers.TokenInformationClass.TokenStatistics;
            UInt32 returnLength;
            NativeMethods.GetTokenInformation(hToken, tokenClass, new SafeMemoryBuffer(IntPtr.Zero), 0, out returnLength);

            UInt64 tokenLuidId;
            using (SafeMemoryBuffer infoPtr = new SafeMemoryBuffer((int)returnLength))
            {
                if (!NativeMethods.GetTokenInformation(hToken, tokenClass, infoPtr, returnLength, out returnLength))
                    throw new Win32Exception("GetTokenInformation(TokenStatistics) failed");

                NativeHelpers.TOKEN_STATISTICS stats = (NativeHelpers.TOKEN_STATISTICS)Marshal.PtrToStructure(
                    infoPtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_STATISTICS));
                tokenLuidId = (UInt64)stats.AuthenticationId;
            }

            UInt32 sessionCount;
            SafeLsaMemoryBuffer sessionPtr;
            UInt32 res = NativeMethods.LsaEnumerateLogonSessions(out sessionCount, out sessionPtr);
            if (res != 0)
                throw new Win32Exception((int)NativeMethods.LsaNtStatusToWinError(res), "LsaEnumerateLogonSession() failed");
            using (sessionPtr)
            {
                IntPtr currentSession = sessionPtr.DangerousGetHandle();
                for (UInt32 i = 0; i < sessionCount; i++)
                {
                    SafeLsaMemoryBuffer sessionDataPtr;
                    res = NativeMethods.LsaGetLogonSessionData(currentSession, out sessionDataPtr);
                    if (res != 0)
                    {
                        currentSession = IntPtr.Add(currentSession, Marshal.SizeOf(typeof(NativeHelpers.LUID)));
                        continue;
                    }
                    using (sessionDataPtr)
                    {
                        NativeHelpers.SECURITY_LOGON_SESSION_DATA sessionData = (NativeHelpers.SECURITY_LOGON_SESSION_DATA)Marshal.PtrToStructure(
                            sessionDataPtr.DangerousGetHandle(), typeof(NativeHelpers.SECURITY_LOGON_SESSION_DATA));
                        UInt64 sessionId = (UInt64)sessionData.LogonId;
                        if (sessionId == tokenLuidId)
                        {
                            AuthenticationPackage = sessionData.AuthenticationPackage.ToString();
                            LogonType = sessionData.LogonType.ToString();
                            break;
                        }
                    }

                    currentSession = IntPtr.Add(currentSession, Marshal.SizeOf(typeof(NativeHelpers.LUID)));
                }
            }
        }

        private void SetTokenMandatoryLabel(SafeNativeHandle hToken)
        {
            NativeHelpers.TokenInformationClass tokenClass = NativeHelpers.TokenInformationClass.TokenIntegrityLevel;
            UInt32 returnLength;
            NativeMethods.GetTokenInformation(hToken, tokenClass, new SafeMemoryBuffer(IntPtr.Zero), 0, out returnLength);
            using (SafeMemoryBuffer infoPtr = new SafeMemoryBuffer((int)returnLength))
            {
                if (!NativeMethods.GetTokenInformation(hToken, tokenClass, infoPtr, returnLength, out returnLength))
                    throw new Win32Exception("GetTokenInformation(TokenIntegrityLevel) failed");
                NativeHelpers.TOKEN_MANDATORY_LABEL label = (NativeHelpers.TOKEN_MANDATORY_LABEL)Marshal.PtrToStructure(
                    infoPtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_MANDATORY_LABEL));
                MandatoryLabelName = LookupSidName(label.Label.Sid);
                MandatoryLabelSid = new SecurityIdentifier(label.Label.Sid);
            }
        }

        private void SetTokenSource(SafeNativeHandle hToken)
        {
            NativeHelpers.TokenInformationClass tokenClass = NativeHelpers.TokenInformationClass.TokenSource;
            UInt32 returnLength;
            NativeMethods.GetTokenInformation(hToken, tokenClass, new SafeMemoryBuffer(IntPtr.Zero), 0, out returnLength);
            using (SafeMemoryBuffer infoPtr = new SafeMemoryBuffer((int)returnLength))
            {
                if (!NativeMethods.GetTokenInformation(hToken, tokenClass, infoPtr, returnLength, out returnLength))
                    throw new Win32Exception("GetTokenInformation(TokenSource) failed");
                NativeHelpers.TOKEN_SOURCE source = (NativeHelpers.TOKEN_SOURCE)Marshal.PtrToStructure(
                    infoPtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_SOURCE));
                SourceName = new string(source.SourceName).Replace('\0', ' ').TrimEnd();
            }
        }

        private void SetTokenUser(SafeNativeHandle hToken)
        {
            NativeHelpers.TokenInformationClass tokenClass = NativeHelpers.TokenInformationClass.TokenUser;
            UInt32 returnLength;
            NativeMethods.GetTokenInformation(hToken, tokenClass, new SafeMemoryBuffer(IntPtr.Zero), 0, out returnLength);
            using (SafeMemoryBuffer infoPtr = new SafeMemoryBuffer((int)returnLength))
            {
                if (!NativeMethods.GetTokenInformation(hToken, tokenClass, infoPtr, returnLength, out returnLength))
                    throw new Win32Exception("GetTokenInformation(TokenSource) failed");
                NativeHelpers.TOKEN_USER user = (NativeHelpers.TOKEN_USER)Marshal.PtrToStructure(
                    infoPtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_USER));
                UserName = LookupSidName(user.User.Sid);
                UserSid = new SecurityIdentifier(user.User.Sid);
            }
        }

        private void SetProfileLoaded()
        {
            UInt32 flags;
            ProfileLoaded = NativeMethods.GetProfileType(out flags);
        }

        private static string LookupSidName(IntPtr pSid)
        {
            StringBuilder name = new StringBuilder(0);
            StringBuilder domain = new StringBuilder(0);
            UInt32 nameLength = 0;
            UInt32 domainLength = 0;
            UInt32 peUse;
            NativeMethods.LookupAccountSid(null, pSid, name, ref nameLength, domain, ref domainLength, out peUse);
            name.EnsureCapacity((int)nameLength);
            domain.EnsureCapacity((int)domainLength);

            if (!NativeMethods.LookupAccountSid(null, pSid, name, ref nameLength, domain, ref domainLength, out peUse))
                throw new Win32Exception("LookupAccountSid() failed");

            return String.Format("{0}\\{1}", domain.ToString(), name.ToString());
        }
    }
}
'@
    $logon = New-Object -TypeName Ansible.Logon
    ConvertTo-Json -InputObject $logon
}.ToString()

$current_user_raw = [Ansible.Process.ProcessUtil]::CreateProcess($null, "powershell.exe -NoProfile -", $null, $null, $test_whoami + "`r`n")
$current_user = ConvertFrom-Json -InputObject $current_user_raw.StandardOut

$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"

$standard_user = "become_standard"
$admin_user = "become_admin"
$become_pass = "password123!$([System.IO.Path]::GetRandomFileName())"
$medium_integrity_sid = "S-1-16-8192"
$high_integrity_sid = "S-1-16-12288"
$system_integrity_sid = "S-1-16-16384"

$tests = @{
    "Runas standard user" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
    }

    "Runas admin user" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
    }

    "Runas SYSTEM" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "System"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected "S-1-5-18"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $system_integrity_sid

        $with_domain = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("NT AUTHORITY\System", $null, "whoami.exe")
        $with_domain.StandardOut | Assert-Equals -Expected "nt authority\system`r`n"
    }

    "Runas LocalService" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("LocalService", $null,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Service"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected "S-1-5-19"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $system_integrity_sid

        $with_domain = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("NT AUTHORITY\LocalService", $null, "whoami.exe")
        $with_domain.StandardOut | Assert-Equals -Expected "nt authority\local service`r`n"
    }

    "Runas NetworkService" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("NetworkService", $null,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Service"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected "S-1-5-20"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $system_integrity_sid

        $with_domain = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("NT AUTHORITY\NetworkService", $null, "whoami.exe")
        $with_domain.StandardOut | Assert-Equals -Expected "nt authority\network service`r`n"
    }

    "Runas without working dir set" = {
        $expected = "$env:SystemRoot\system32`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe $pwd.Path', $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas with working dir set" = {
        $expected = "$env:SystemRoot`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe $pwd.Path', $env:SystemRoot, $null, "")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas without environment set" = {
        $expected = "Windows_NT`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe $env:TEST; $env:OS', $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas with environment set" = {
        $env_vars = @{
            TEST = "tesTing"
            TEST2 = "Testing 2"
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, 0, "Interactive", $null,
            'cmd.exe /c set', $null, $env_vars, "")
        ("TEST=tesTing" -cin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        ("TEST2=Testing 2" -cin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        ("OS=Windows_NT" -cnotin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas with string stdin" = {
        $expected = "input value`r`n`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe [System.Console]::In.ReadToEnd()', $null, $null, "input value")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas with string stdin and newline" = {
        $expected = "input value`r`n`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe [System.Console]::In.ReadToEnd()', $null, $null, "input value`r`n")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Runas with byte stdin" = {
        $expected = "input value`r`n"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, 0, "Interactive", $null,
            'powershell.exe [System.Console]::In.ReadToEnd()', $null, $null, [System.Text.Encoding]::UTF8.GetBytes("input value"))
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "Missing executable" = {
        $failed = $false
        try {
            [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null, "fake.exe")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "Ansible.Process.Win32Exception"
            $expected = 'Exception calling "CreateProcessAsUser" with "3" argument(s): "CreateProcessWithTokenW() failed '
            $expected += '(The system cannot find the file specified, Win32ErrorCode 2)"'
            $_.Exception.Message | Assert-Equals -Expected $expected
        }
        $failed | Assert-Equals -Expected $true
    }

    "CreateProcessAsUser with lpApplicationName" = {
        $expected = "abc`r`n"
        $full_path = "$($env:SystemRoot)\System32\WindowsPowerShell\v1.0\powershell.exe"
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null, 0, "Interactive", $full_path,
            "Write-Output 'abc'", $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null, 0, "Interactive", $full_path,
            "powershell.exe Write-Output 'abc'", $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcessAsUser with stderr" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null, 0, "Interactive", $null,
            "powershell.exe [System.Console]::Error.WriteLine('hi')", $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected ""
        $actual.StandardError | Assert-Equals -Expected "hi`r`n"
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcessAsUser with exit code" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("SYSTEM", $null, 0, "Interactive", $null,
            "powershell.exe exit 10", $null, $null, "")
        $actual.StandardOut | Assert-Equals -Expected ""
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 10
    }

    "Local account with computer name" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("$env:COMPUTERNAME\$standard_user", $become_pass,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
    }

    "Local account with computer as period" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser(".\$standard_user", $become_pass,
            "powershell.exe -NoProfile -ExecutionPolicy ByPass -File $tmp_script")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
    }

    "Local account with invalid password" = {
        $failed = $false
        try {
            [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, "incorrect", "powershell.exe Write-Output abc")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "Ansible.AccessToken.Win32Exception"
            # Server 2008 has a slightly different error msg, just assert we get the error 1326
            ($_.Exception.Message.Contains("Win32ErrorCode 1326")) | Assert-Equals -Expected $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Invalid account" = {
        $failed = $false
        try {
            [Ansible.Become.BecomeUtil]::CreateProcessAsUser("incorrect", "incorrect", "powershell.exe Write-Output abc")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.Security.Principal.IdentityNotMappedException"
            $expected = 'Exception calling "CreateProcessAsUser" with "3" argument(s): "Some or all '
            $expected += 'identity references could not be translated."'
            $_.Exception.Message | Assert-Equals -Expected $expected
        }
        $failed | Assert-Equals -Expected $true
    }

    "Interactive logon with standard" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, "WithProfile",
            "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Batch logon with standard" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, "WithProfile",
            "Batch", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Batch"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Network logon with standard" = {
        # Server 2008 will not work with become to Network or Network Credentials
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, "WithProfile",
            "Network", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Network"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Network with cleartext logon with standard" = {
        # Server 2008 will not work with become to Network or Network Cleartext
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, $become_pass, "WithProfile",
            "NetworkCleartext", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "NetworkCleartext"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Logon without password with standard" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, [NullString]::Value, "WithProfile",
            "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        # Too unstable, there might be another process still lingering which causes become to steal instead of using
        # S4U. Just don't check the type and source to verify we can become without a password
        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        # $stdout.LogonType | Assert-Equals -Expected "Batch"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        # $stdout.SourceName | Assert-Equals -Expected "ansible"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Logon without password and network type with standard" = {
        # Server 2008 will not work with become to Network or Network Cleartext
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($standard_user, [NullString]::Value, "WithProfile",
            "Network", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        # Too unstable, there might be another process still lingering which causes become to steal instead of using
        # S4U. Just don't check the type and source to verify we can become without a password
        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        # $stdout.LogonType | Assert-Equals -Expected "Network"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $medium_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        # $stdout.SourceName | Assert-Equals -Expected "ansible"
        $stdout.UserSid.Value | Assert-Equals -Expected $standard_user_sid
    }

    "Interactive logon with admin" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, "WithProfile",
            "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Batch logon with admin" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, "WithProfile",
            "Batch", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Batch"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Network logon with admin" = {
        # Server 2008 will not work with become to Network or Network Credentials
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, "WithProfile",
            "Network", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Network"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Network with cleartext logon with admin" = {
        # Server 2008 will not work with become to Network or Network Credentials
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, "WithProfile",
            "NetworkCleartext", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "NetworkCleartext"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Fail to logon with null or empty password" = {
        $failed = $false
        try {
            # Having $null or an empty string means we are trying to become a user with a blank password and not
            # become without setting the password. This is confusing as $null gets converted to "" and we need to
            # use [NullString]::Value instead if we want that behaviour. This just tests to see that an empty
            # string won't go the S4U route.
            [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $null, "WithProfile",
                    "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "Ansible.AccessToken.Win32Exception"
            # Server 2008 has a slightly different error msg, just assert we get the error 1326
            ($_.Exception.Message.Contains("Win32ErrorCode 1326")) | Assert-Equals -Expected $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Logon without password with admin" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, [NullString]::Value, "WithProfile",
            "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        # Too unstable, there might be another process still lingering which causes become to steal instead of using
        # S4U. Just don't check the type and source to verify we can become without a password
        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        # $stdout.LogonType | Assert-Equals -Expected "Batch"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        # $stdout.SourceName | Assert-Equals -Expected "ansible"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Logon without password and network type with admin" = {
        # become network doesn't work on Server 2008
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.1") {
            continue
        }
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, [NullString]::Value, "WithProfile",
            "Network", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        # Too unstable, there might be another process still lingering which causes become to steal instead of using
        # S4U. Just don't check the type and source to verify we can become without a password
        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        # $stdout.LogonType | Assert-Equals -Expected "Network"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $true
        # $stdout.SourceName | Assert-Equals -Expected "ansible"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Logon without profile with admin" = {
        # Server 2008 and 2008 R2 does not support running without the profile being set
        if ([System.Environment]::OSVersion.Version -lt [Version]"6.2") {
            continue
        }

        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($admin_user, $become_pass, 0,
            "Interactive", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "Interactive"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $high_integrity_sid
        $stdout.ProfileLoaded | Assert-Equals -Expected $false
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $admin_user_sid
    }

    "Logon with network credentials and no profile" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("fakeuser", "fakepassword", "NetcredentialsOnly",
            "NewCredentials", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "NewCredentials"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $current_user.MandatoryLabelSid.Value

        # while we didn't set WithProfile, the new process is based on the current process
        $stdout.ProfileLoaded | Assert-Equals -Expected $current_user.ProfileLoaded
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $current_user.UserSid.Value
    }

    "Logon with network credentials and with profile" = {
        $actual = [Ansible.Become.BecomeUtil]::CreateProcessAsUser("fakeuser", "fakepassword", "NetcredentialsOnly, WithProfile",
            "NewCredentials", $null, "powershell.exe -NoProfile -", $tmp_dir, $null, $test_whoami + "`r`n")
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $stdout = ConvertFrom-Json -InputObject $actual.StandardOut
        $stdout.LogonType | Assert-Equals -Expected "NewCredentials"
        $stdout.MandatoryLabelSid.Value | Assert-Equals -Expected $current_user.MandatoryLabelSid.Value
        $stdout.ProfileLoaded | Assert-Equals -Expected $current_user.ProfileLoaded
        $stdout.SourceName | Assert-Equals -Expected "Advapi"
        $stdout.UserSid.Value | Assert-Equals -Expected $current_user.UserSid.Value
    }
}

try {
    $tmp_dir = Join-Path -Path ([System.IO.Path]::GetTempPath()) -ChildPath ([System.IO.Path]::GetRandomFileName())
    New-Item -Path $tmp_dir -ItemType Directory > $null
    $acl = Get-Acl -Path $tmp_dir
    $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
        New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList ([System.Security.Principal.WellKnownSidType]::WorldSid, $null)
        [System.Security.AccessControl.FileSystemRights]::FullControl,
        [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit",
        [System.Security.AccessControl.PropagationFlags]::None,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    $acl.AddAccessRule($ace)
    Set-Acl -Path $tmp_dir -AclObject $acl

    $tmp_script = Join-Path -Path $tmp_dir -ChildPath "whoami.ps1"
    Set-Content -Path $tmp_script -Value $test_whoami

    foreach ($user in $standard_user, $admin_user) {
        $user_obj = $adsi.Children | Where-Object { $_.SchemaClassName -eq "User" -and $_.Name -eq $user }
        if ($null -eq $user_obj) {
            $user_obj = $adsi.Create("User", $user)
            $user_obj.SetPassword($become_pass)
            $user_obj.SetInfo()
        } else {
            $user_obj.SetPassword($become_pass)
        }
        $user_obj.RefreshCache()

        if ($user -eq $standard_user) {
            $standard_user_sid = (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @($user_obj.ObjectSid.Value, 0)).Value
            $group = [System.Security.Principal.WellKnownSidType]::BuiltinUsersSid
        } else {
            $admin_user_sid = (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @($user_obj.ObjectSid.Value, 0)).Value
            $group = [System.Security.Principal.WellKnownSidType]::BuiltinAdministratorsSid
        }
        $group = (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList $group, $null).Value
        [string[]]$current_groups = $user_obj.Groups() | ForEach-Object {
            New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @($_.GetType().InvokeMember("objectSID", "GetProperty", $null, $_, $null), 0)
        }
        if ($current_groups -notcontains $group) {
            $group_obj = $adsi.Children | Where-Object {
                if ($_.SchemaClassName -eq "Group") {
                    $group_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @($_.objectSID.Value, 0)
                    $group_sid -eq $group
                }
            }
            $group_obj.Add($user_obj.Path)
        }
    }
    foreach ($test_impl in $tests.GetEnumerator()) {
        $test = $test_impl.Key
        &$test_impl.Value
    }
} finally {
    Remove-Item -Path $tmp_dir -Force -Recurse
    foreach ($user in $standard_user, $admin_user) {
        $user_obj = $adsi.Children | Where-Object { $_.SchemaClassName -eq "User" -and $_.Name -eq $user }
        $adsi.Delete("User", $user_obj.Name.Value)
    }
}


$module.Result.data = "success"
$module.ExitJson()

