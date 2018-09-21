# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: powershell
    plugin_type: shell
    version_added: ""
    short_description: Windows Powershell
    description:
      - The only option when using 'winrm' as a connection plugin
    options:
      remote_tmp:
        description:
        - Temporary directory to use on targets when copying files to the host.
        default: '%TEMP%'
        ini:
        - section: powershell
          key: remote_tmp
        vars:
        - name: ansible_remote_tmp
      set_module_language:
        description:
        - Controls if we set the locale for moduels when executing on the
          target.
        - Windows only supports C(no) as an option.
        type: bool
        default: 'no'
        choices:
        - 'no'
      environment:
        description:
        - Dictionary of environment variables and their values to use when
          executing commands.
        type: dict
        default: {}
'''
# FIXME: admin_users and set_module_language don't belong here but must be set
# so they don't failk when someone get_option('admin_users') on this plugin

import base64
import os
import re
import shlex

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_text
from ansible.plugins.shell import ShellBase


_common_args = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted']

# Primarily for testing, allow explicitly specifying PowerShell version via
# an environment variable.
_powershell_version = os.environ.get('POWERSHELL_VERSION', None)
if _powershell_version:
    _common_args = ['PowerShell', '-Version', _powershell_version] + _common_args[1:]

exec_wrapper = br'''
begin {
    $DebugPreference = "Continue"
    $ErrorActionPreference = "Stop"
    Set-StrictMode -Version 2

    function ConvertTo-HashtableFromPsCustomObject ($myPsObject){
        $output = @{};
        $myPsObject | Get-Member -MemberType *Property | % {
            $val = $myPsObject.($_.name);
            If ($val -is [psobject]) {
                $val = ConvertTo-HashtableFromPsCustomObject $val
            }
            $output.($_.name) = $val
        }
        return $output;
    }
    # stream JSON including become_pw, ps_module_payload, bin_module_payload, become_payload, write_payload_path, preserve directives
    # exec runspace, capture output, cleanup, return module output

    # NB: do not adjust the following line- it is replaced when doing non-streamed module output
    $json_raw = ''
}
process {
    $input_as_string = [string]$input

    $json_raw += $input_as_string
}
end {
    If (-not $json_raw) {
        Write-Error "no input given" -Category InvalidArgument
    }
    $payload = ConvertTo-HashtableFromPsCustomObject (ConvertFrom-Json $json_raw)

    # TODO: handle binary modules
    # TODO: handle persistence

    $min_os_version = [version]$payload.min_os_version
    if ($min_os_version -ne $null) {
        $actual_os_version = [System.Environment]::OSVersion.Version
        if ($actual_os_version -lt $min_os_version) {
            $msg = "This module cannot run on this OS as it requires a minimum version of $min_os_version, actual was $actual_os_version"
            Write-Output (ConvertTo-Json @{failed=$true;msg=$msg})
            exit 1
        }
    }

    $min_ps_version = [version]$payload.min_ps_version
    if ($min_ps_version -ne $null) {
        $actual_ps_version = $PSVersionTable.PSVersion
        if ($actual_ps_version -lt $min_ps_version) {
            $msg = "This module cannot run as it requires a minimum PowerShell version of $min_ps_version, actual was $actual_ps_version"
            Write-Output (ConvertTo-Json @{failed=$true;msg=$msg})
            exit 1
        }
    }

    $actions = $payload.actions

    # pop 0th action as entrypoint
    $entrypoint = $payload.($actions[0])
    $payload.actions = $payload.actions[1..99]

    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

    # load the current action entrypoint as a module custom object with a Run method
    $entrypoint = New-Module -ScriptBlock ([scriptblock]::Create($entrypoint)) -AsCustomObject

    Set-Variable -Scope global -Name complex_args -Value $payload["module_args"] | Out-Null

    # dynamically create/load modules
    ForEach ($mod in $payload.powershell_modules.GetEnumerator()) {
        $decoded_module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mod.Value))
        New-Module -ScriptBlock ([scriptblock]::Create($decoded_module)) -Name $mod.Key | Import-Module -WarningAction SilentlyContinue | Out-Null
    }

    $output = $entrypoint.Run($payload)

    Write-Output $output
}

'''  # end exec_wrapper

leaf_exec = br'''
Function Run($payload) {
    $entrypoint = $payload.module_entry

    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

    $ps = [powershell]::Create()

    $ps.AddStatement().AddCommand("Set-Variable").AddParameters(@{Scope="global";Name="complex_args";Value=$payload.module_args}) | Out-Null
    $ps.AddCommand("Out-Null") | Out-Null

    # redefine Write-Host to dump to output instead of failing- lots of scripts use it
    $ps.AddStatement().AddScript("Function Write-Host(`$msg){ Write-Output `$msg }") | Out-Null

    ForEach ($env_kv in $payload.environment.GetEnumerator()) {
        # need to escape ' in both the key and value
        $env_key = $env_kv.Key.ToString().Replace("'", "''")
        $env_value = $env_kv.Value.ToString().Replace("'", "''")
        $escaped_env_set = "[System.Environment]::SetEnvironmentVariable('{0}', '{1}')" -f $env_key, $env_value
        $ps.AddStatement().AddScript($escaped_env_set) | Out-Null
    }

    # dynamically create/load modules
    ForEach ($mod in $payload.powershell_modules.GetEnumerator()) {
        $decoded_module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mod.Value))
        $ps.AddStatement().AddCommand("New-Module").AddParameters(@{ScriptBlock=([scriptblock]::Create($decoded_module));Name=$mod.Key}) | Out-Null
        $ps.AddCommand("Import-Module").AddParameters(@{WarningAction="SilentlyContinue"}) | Out-Null
        $ps.AddCommand("Out-Null") | Out-Null
    }

    # force input encoding to preamble-free UTF8 so PS sub-processes (eg, Start-Job) don't blow up
    $ps.AddStatement().AddScript("[Console]::InputEncoding = New-Object Text.UTF8Encoding `$false") | Out-Null

    $ps.AddStatement().AddScript($entrypoint) | Out-Null

    $output = $ps.Invoke()

    $output

    # PS3 doesn't properly set HadErrors in many cases, inspect the error stream as a fallback
    If ($ps.HadErrors -or ($PSVersionTable.PSVersion.Major -lt 4 -and $ps.Streams.Error.Count -gt 0)) {
        [System.Console]::Error.WriteLine($($ps.Streams.Error | Out-String))
        $exit_code = $ps.Runspace.SessionStateProxy.GetVariable("LASTEXITCODE")
        If(-not $exit_code) {
            $exit_code = 1
        }
        # need to use this instead of Exit keyword to prevent runspace from crashing with dynamic modules
        $host.SetShouldExit($exit_code)
    }
}
'''  # end leaf_exec

become_wrapper = br'''
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$helper_def = @"
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

namespace Ansible
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

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public UInt64 PerProcessUserTimeLimit;
        public UInt64 PerJobUserTimeLimit;
        public LimitFlags LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public UInt32 ActiveProcessLimit;
        public UIntPtr Affinity;
        public UInt32 PriorityClass;
        public UInt32 SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    public class JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation = new JOBOBJECT_BASIC_LIMIT_INFORMATION();
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=48)]
        public byte[] IO_COUNTERS_BLOB;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=4)]
        public UIntPtr[] LIMIT_BLOB;
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

    enum JobObjectInfoType
    {
        ExtendedLimitInformation = 9,
    }

    [Flags]
    enum ThreadAccessRights : uint
    {
        SUSPEND_RESUME = 0x0002
    }

    [Flags]
    public enum LimitFlags : uint
    {
        JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
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

    public class Job : IDisposable
    {
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern IntPtr CreateJobObject(
            IntPtr lpJobAttributes,
            string lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetInformationJobObject(
            IntPtr hJob,
            JobObjectInfoType JobObjectInfoClass,
            JOBOBJECT_EXTENDED_LIMIT_INFORMATION lpJobObjectInfo,
            int cbJobObjectInfoLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AssignProcessToJobObject(
            IntPtr hJob,
            IntPtr hProcess);

        [DllImport("kernel32.dll")]
        private static extern bool CloseHandle(
            IntPtr hObject);

        private IntPtr handle;

        public Job()
        {
            handle = CreateJobObject(IntPtr.Zero, null);
            if (handle == IntPtr.Zero)
                throw new Win32Exception("CreateJobObject() failed");

            JOBOBJECT_EXTENDED_LIMIT_INFORMATION extendedJobInfo = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
            // on OSs that support nested jobs, one of the jobs must allow breakaway for async to work properly under WinRM
            extendedJobInfo.BasicLimitInformation.LimitFlags = LimitFlags.JOB_OBJECT_LIMIT_BREAKAWAY_OK | LimitFlags.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

            if (!SetInformationJobObject(handle, JobObjectInfoType.ExtendedLimitInformation, extendedJobInfo, Marshal.SizeOf(extendedJobInfo)))
                throw new Win32Exception("SetInformationJobObject() failed");
        }

        public void AssignProcess(IntPtr processHandle)
        {
            if (!AssignProcessToJobObject(handle, processHandle))
                throw new Win32Exception("AssignProcessToJobObject() failed");
        }

        public void Dispose()
        {
            if (handle != IntPtr.Zero)
            {
                CloseHandle(handle);
                handle = IntPtr.Zero;
            }

            GC.SuppressFinalize(this);
        }
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

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern SafeFileHandle OpenThread(
            ThreadAccessRights dwDesiredAccess,
            bool bInheritHandle,
            int dwThreadId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern int ResumeThread(
            SafeHandle hThread);

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

            // To support async + become, we have to do some job magic later, which requires both breakaway and starting suspended
            CreationFlags startup_flags = CreationFlags.CREATE_UNICODE_ENVIRONMENT | CreationFlags.CREATE_BREAKAWAY_FROM_JOB | CreationFlags.CREATE_SUSPENDED;

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

            // If 2012/8+ OS, create new job with JOB_OBJECT_LIMIT_BREAKAWAY_OK
            // so that async can work
            Job job = null;
            if (Environment.OSVersion.Version >= new Version("6.2"))
            {
                job = new Job();
                job.AssignProcess(pi.hProcess);
            }
            ResumeProcessById(pi.dwProcessId);

            CommandResult result = new CommandResult();
            try
            {
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
            }
            finally
            {
                if (job != null)
                    job.Dispose();
            }

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

        private static void ResumeThreadById(int threadId)
        {
            var threadHandle = OpenThread(ThreadAccessRights.SUSPEND_RESUME, false, threadId);
            if (threadHandle.IsInvalid)
                throw new Win32Exception(String.Format("Thread ID {0} is invalid", threadId));

            try
            {
                if (ResumeThread(threadHandle) == -1)
                    throw new Win32Exception(String.Format("Thread ID {0} cannot be resumed", threadId));
            }
            finally
            {
                threadHandle.Dispose();
            }
        }

        private static void ResumeProcessById(int pid)
        {
            var proc = Process.GetProcessById(pid);

            // wait for at least one suspended thread in the process (this handles possible slow startup race where
            // primary thread of created-suspended process has not yet become runnable)
            var retryCount = 0;
            while (!proc.Threads.OfType<ProcessThread>().Any(t => t.ThreadState == System.Diagnostics.ThreadState.Wait &&
                 t.WaitReason == ThreadWaitReason.Suspended))
            {
                proc.Refresh();
                Thread.Sleep(50);
                if (retryCount > 100)
                    throw new InvalidOperationException(String.Format("No threads were suspended in target PID {0} after 5s", pid));
            }

            foreach (var thread in proc.Threads.OfType<ProcessThread>().Where(t => t.ThreadState == System.Diagnostics.ThreadState.Wait &&
                 t.WaitReason == ThreadWaitReason.Suspended))
                ResumeThreadById(thread.Id);
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
"@

$exec_wrapper = {
    Set-StrictMode -Version 2
    $DebugPreference = "Continue"
    $ErrorActionPreference = "Stop"

    Function ConvertTo-HashtableFromPsCustomObject($myPsObject) {
        $output = @{}
        $myPsObject | Get-Member -MemberType *Property | % {
            $val = $myPsObject.($_.name)
            if ($val -is [psobject]) {
                $val = ConvertTo-HashtableFromPsCustomObject -myPsObject $val
            }
            $output.($_.name) = $val
        }
        return $output
    }

    Function Invoke-Win32Api {
        # Inspired by - Call a Win32 API in PowerShell without compiling C# code on
        # the disk
        # http://www.leeholmes.com/blog/2007/10/02/managing-ini-files-with-powershell/
        # https://blogs.technet.microsoft.com/heyscriptingguy/2013/06/27/use-powershell-to-interact-with-the-windows-api-part-3/
        [CmdletBinding()]
        param(
            [Parameter(Mandatory=$true)] [String]$DllName,
            [Parameter(Mandatory=$true)] [String]$MethodName,
            [Parameter(Mandatory=$true)] [Type]$ReturnType,
            [Parameter()] [Type[]]$ParameterTypes = [Type[]]@(),
            [Parameter()] [Object[]]$Parameters = [Object[]]@()
        )

        $assembly = New-Object -TypeName System.Reflection.AssemblyName -ArgumentList "Win32ApiAssembly"
        $dynamic_assembly = [AppDomain]::CurrentDomain.DefineDynamicAssembly($assembly, [Reflection.Emit.AssemblyBuilderAccess]::Run)
        $dynamic_module = $dynamic_assembly.DefineDynamicModule("Win32Module", $false)
        $dynamic_type = $dynamic_module.DefineType("Win32Type", "Public, Class")

        $dynamic_method = $dynamic_type.DefineMethod(
            $MethodName,
            [Reflection.MethodAttributes]"Public, Static",
            $ReturnType,
            $ParameterTypes
        )

        $constructor = [Runtime.InteropServices.DllImportAttribute].GetConstructor([String])
        $custom_attributes = New-Object -TypeName Reflection.Emit.CustomAttributeBuilder -ArgumentList @(
            $constructor,
            $DllName
        )

        $dynamic_method.SetCustomAttribute($custom_attributes)
        $win32_type = $dynamic_type.CreateType()
        $win32_type::$MethodName.Invoke($Parameters)
    }

    # become process is run under a different console to the WinRM one so we
    # need to set the UTF-8 codepage again, this also needs to be set before
    # reading the stdin pipe that contains the module args specifying the
    # remote_tmp to use. Instead this will use reflection when calling the Win32
    # API no tmp files touch the disk
    $invoke_args = @{
        DllName = "kernel32.dll"
        ReturnType = [bool]
        ParameterTypes = @([UInt32])
        Parameters = @(65001)
    }
    Invoke-Win32Api -MethodName SetConsoleCP @invoke_args > $null
    Invoke-Win32Api -MethodName SetConsoleOutputCP @invoke_args > $null

    # stream JSON including become_pw, ps_module_payload, bin_module_payload, become_payload, write_payload_path, preserve directives
    # exec runspace, capture output, cleanup, return module output

    $json_raw = [System.Console]::In.ReadToEnd()

    If (-not $json_raw) {
        Write-Error "no input given" -Category InvalidArgument
    }

    $payload = ConvertTo-HashtableFromPsCustomObject -myPsObject (ConvertFrom-Json $json_raw)

    # TODO: handle binary modules
    # TODO: handle persistence

    $actions = $payload.actions

    # pop 0th action as entrypoint
    $entrypoint = $payload.($actions[0])
    $payload.actions = $payload.actions[1..99]

    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

    # load the current action entrypoint as a module custom object with a Run method
    $entrypoint = New-Module -ScriptBlock ([scriptblock]::Create($entrypoint)) -AsCustomObject

    Set-Variable -Scope global -Name complex_args -Value $payload["module_args"] | Out-Null

    # dynamically create/load modules
    ForEach ($mod in $payload.powershell_modules.GetEnumerator()) {
        $decoded_module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mod.Value))
        New-Module -ScriptBlock ([scriptblock]::Create($decoded_module)) -Name $mod.Key | Import-Module -WarningAction SilentlyContinue | Out-Null
    }

    $output = $entrypoint.Run($payload)
    # base64 encode the output so the non-ascii characters are preserved
    Write-Output ([System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Write-Output $output))))
} # end exec_wrapper

Function Dump-Error ($excep, $msg=$null) {
    $eo = @{failed=$true}

    $exception_message = $excep.Exception.Message
    if ($null -ne $msg) {
        $exception_message = "$($msg): $exception_message"
    }
    $eo.msg = $exception_message
    $eo.exception = $excep | Out-String
    $host.SetShouldExit(1)

    $eo | ConvertTo-Json -Depth 10 -Compress
}

Function Parse-EnumValue($enum, $flag_type, $value, $prefix) {
    $raw_enum_value = "$prefix$($value.ToUpper())"
    try {
        $enum_value = [Enum]::Parse($enum, $raw_enum_value)
    } catch [System.ArgumentException] {
        $valid_options = [Enum]::GetNames($enum) | ForEach-Object { $_.Substring($prefix.Length).ToLower() }
        throw "become_flags $flag_type value '$value' is not valid, valid values are: $($valid_options -join ", ")"
    }
    return $enum_value
}

Function Parse-BecomeFlags($flags) {
    $logon_type = [Ansible.LogonType]::LOGON32_LOGON_INTERACTIVE
    $logon_flags = [Ansible.LogonFlags]::LOGON_WITH_PROFILE

    if ($flags -eq $null -or $flags -eq "") {
        $flag_split = @()
    } elseif ($flags -is [string]) {
        $flag_split = $flags.Split(" ")
    } else {
        throw "become_flags must be a string, was $($flags.GetType())"
    }

    foreach ($flag in $flag_split) {
        $split = $flag.Split("=")
        if ($split.Count -ne 2) {
            throw "become_flags entry '$flag' is in an invalid format, must be a key=value pair"
        }
        $flag_key = $split[0]
        $flag_value = $split[1]
        if ($flag_key -eq "logon_type") {
            $enum_details = @{
                enum = [Ansible.LogonType]
                flag_type = $flag_key
                value = $flag_value
                prefix = "LOGON32_LOGON_"
            }
            $logon_type = Parse-EnumValue @enum_details
        } elseif ($flag_key -eq "logon_flags") {
            $logon_flag_values = $flag_value.Split(",")
            $logon_flags = 0 -as [Ansible.LogonFlags]
            foreach ($logon_flag_value in $logon_flag_values) {
                if ($logon_flag_value -eq "") {
                    continue
                }
                $enum_details = @{
                    enum = [Ansible.LogonFlags]
                    flag_type = $flag_key
                    value = $logon_flag_value
                    prefix = "LOGON_"
                }
                $logon_flag = Parse-EnumValue @enum_details
                $logon_flags = $logon_flags -bor $logon_flag
            }
        } else {
            throw "become_flags key '$flag_key' is not a valid runas flag, must be 'logon_type' or 'logon_flags'"
        }
    }

    return $logon_type, [Ansible.LogonFlags]$logon_flags
}

Function Run($payload) {
    # NB: action popping handled inside subprocess wrapper

    $original_tmp = $env:TMP
    $original_temp = $env:TEMP
    $remote_tmp = $payload["module_args"]["_ansible_remote_tmp"]
    $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
    if ($null -eq $remote_tmp) {
        $remote_tmp = $original_tmp
    }

    # become process is run under a different console to the WinRM one so we
    # need to set the UTF-8 codepage again
    $env:TMP = $remote_tmp
    $env:TEMP = $remote_tmp
    Add-Type -TypeDefinition $helper_def -Debug:$false
    $env:TMP = $original_tmp
    $env:TEMP = $original_tmp

    $username = $payload.become_user
    $password = $payload.become_password
    try {
        $logon_type, $logon_flags = Parse-BecomeFlags -flags $payload.become_flags
    } catch {
        Dump-Error -excep $_ -msg "Failed to parse become_flags '$($payload.become_flags)'"
        return $null
    }

    # NB: CreateProcessWithTokenW commandline maxes out at 1024 chars, must bootstrap via filesystem
    $temp = [System.IO.Path]::Combine($remote_tmp, [System.IO.Path]::GetRandomFileName() + ".ps1")
    $exec_wrapper.ToString() | Set-Content -Path $temp
    $rc = 0

    Try {
        # do not modify the ACL if the logon_type is LOGON32_LOGON_NEW_CREDENTIALS
        # as this results in the local execution running under the same user's token,
        # otherwise we need to allow (potentially unprivileges) the become user access
        # to the tempfile (NB: this likely won't work if traverse checking is enaabled).
        if ($logon_type -ne [Ansible.LogonType]::LOGON32_LOGON_NEW_CREDENTIALS) {
            $acl = Get-Acl -Path $temp

            Try {
                $acl.AddAccessRule($(New-Object System.Security.AccessControl.FileSystemAccessRule($username, "FullControl", "Allow")))
            } Catch [System.Security.Principal.IdentityNotMappedException] {
                throw "become_user '$username' is not recognized on this host"
            } Catch {
                throw "failed to set ACL on temp become execution script: $($_.Exception.Message)"
            }
            Set-Acl -Path $temp -AclObject $acl | Out-Null
        }

        $payload_string = $payload | ConvertTo-Json -Depth 99 -Compress

        $lp_command_line = New-Object System.Text.StringBuilder @("powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File $temp")
        $lp_current_directory = "$env:SystemRoot"

        $result = [Ansible.BecomeUtil]::RunAsUser($username, $password, $lp_command_line, $lp_current_directory, $payload_string, $logon_flags, $logon_type)
        $stdout = $result.StandardOut
        $stdout = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($stdout.Trim()))
        $stderr = $result.StandardError
        $rc = $result.ExitCode

        [Console]::Out.WriteLine($stdout)
        [Console]::Error.WriteLine($stderr.Trim())
    } Catch {
        $excep = $_
        Dump-Error -excep $excep -msg "Failed to become user $username"
    } Finally {
        Remove-Item $temp -ErrorAction SilentlyContinue
    }
    $host.SetShouldExit($rc)
}
'''

async_wrapper = br'''
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

# build exec_wrapper encoded command
# start powershell with breakaway running exec_wrapper encodedcommand
# stream payload to powershell with normal exec, but normal exec writes results to resultfile instead of stdout/stderr
# return asyncresult to controller

$exec_wrapper = {
$DebugPreference = "Continue"
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

function ConvertTo-HashtableFromPsCustomObject ($myPsObject){
    $output = @{};
    $myPsObject | Get-Member -MemberType *Property | % {
        $val = $myPsObject.($_.name);
        If ($val -is [psobject]) {
            $val = ConvertTo-HashtableFromPsCustomObject $val
        }
        $output.($_.name) = $val
    }
    return $output;
}
# stream JSON including become_pw, ps_module_payload, bin_module_payload, become_payload, write_payload_path, preserve directives
# exec runspace, capture output, cleanup, return module output

$json_raw = [System.Console]::In.ReadToEnd()

If (-not $json_raw) {
    Write-Error "no input given" -Category InvalidArgument
}

$payload = ConvertTo-HashtableFromPsCustomObject (ConvertFrom-Json $json_raw)

# TODO: handle binary modules
# TODO: handle persistence

$actions = $payload.actions

# pop 0th action as entrypoint
$entrypoint = $payload.($actions[0])
$payload.actions = $payload.actions[1..99]

$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

# load the current action entrypoint as a module custom object with a Run method
$entrypoint = New-Module -ScriptBlock ([scriptblock]::Create($entrypoint)) -AsCustomObject

Set-Variable -Scope global -Name complex_args -Value $payload["module_args"] | Out-Null

# dynamically create/load modules
ForEach ($mod in $payload.powershell_modules.GetEnumerator()) {
    $decoded_module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mod.Value))
    New-Module -ScriptBlock ([scriptblock]::Create($decoded_module)) -Name $mod.Key | Import-Module -WarningAction SilentlyContinue | Out-Null
}

$output = $entrypoint.Run($payload)

Write-Output $output

} # end exec_wrapper


Function Run($payload) {
# BEGIN Ansible.Async native type definition
    $native_process_util = @"
        using Microsoft.Win32.SafeHandles;
        using System;
        using System.ComponentModel;
        using System.Diagnostics;
        using System.IO;
        using System.Linq;
        using System.Runtime.InteropServices;
        using System.Text;
        using System.Threading;

        namespace Ansible.Async {

            public static class NativeProcessUtil
            {
                [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode, BestFitMapping=false)]
                public static extern bool CreateProcess(
                    [MarshalAs(UnmanagedType.LPTStr)]
                    string lpApplicationName,
                    StringBuilder lpCommandLine,
                    IntPtr lpProcessAttributes,
                    IntPtr lpThreadAttributes,
                    bool bInheritHandles,
                    uint dwCreationFlags,
                    IntPtr lpEnvironment,
                    [MarshalAs(UnmanagedType.LPTStr)]
                    string lpCurrentDirectory,
                    STARTUPINFOEX lpStartupInfo,
                    out PROCESS_INFORMATION lpProcessInformation);

                [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
                public static extern uint SearchPath (
                    string lpPath,
                    string lpFileName,
                    string lpExtension,
                    int nBufferLength,
                    [MarshalAs (UnmanagedType.LPTStr)]
                    StringBuilder lpBuffer,
                    out IntPtr lpFilePart);

                [DllImport("kernel32.dll")]
                public static extern bool CreatePipe(out IntPtr hReadPipe, out IntPtr hWritePipe, SECURITY_ATTRIBUTES lpPipeAttributes, uint nSize);

                [DllImport("kernel32.dll", SetLastError=true)]
                public static extern IntPtr GetStdHandle(StandardHandleValues nStdHandle);

                [DllImport("kernel32.dll", SetLastError=true)]
                public static extern bool SetHandleInformation(IntPtr hObject, HandleFlags dwMask, int dwFlags);

                [DllImport("kernel32.dll", SetLastError=true)]
                public static extern bool InitializeProcThreadAttributeList(IntPtr lpAttributeList, int dwAttributeCount, int dwFlags, ref int lpSize);

                [DllImport("kernel32.dll", SetLastError=true)]
                public static extern bool UpdateProcThreadAttribute(
                     IntPtr lpAttributeList,
                     uint dwFlags,
                     IntPtr Attribute,
                     IntPtr lpValue,
                     IntPtr cbSize,
                     IntPtr lpPreviousValue,
                     IntPtr lpReturnSize);

                public static string SearchPath(string findThis)
                {
                    StringBuilder sbOut = new StringBuilder(1024);
                    IntPtr filePartOut;

                    if(SearchPath(null, findThis, null, sbOut.Capacity, sbOut, out filePartOut) == 0)
                        throw new FileNotFoundException("Couldn't locate " + findThis + " on path");

                    return sbOut.ToString();
                }

                [DllImport("kernel32.dll", SetLastError=true)]
                static extern SafeFileHandle OpenThread(
                    ThreadAccessRights dwDesiredAccess,
                    bool bInheritHandle,
                    int dwThreadId);

                [DllImport("kernel32.dll", SetLastError=true)]
                static extern int ResumeThread(SafeHandle hThread);

                public static void ResumeThreadById(int threadId)
                {
                    var threadHandle = OpenThread(ThreadAccessRights.SUSPEND_RESUME, false, threadId);
                    if(threadHandle.IsInvalid)
                        throw new Exception(String.Format("Thread ID {0} is invalid ({1})", threadId,
                            new Win32Exception(Marshal.GetLastWin32Error()).Message));

                    try
                    {
                        if(ResumeThread(threadHandle) == -1)
                            throw new Exception(String.Format("Thread ID {0} cannot be resumed ({1})", threadId,
                                new Win32Exception(Marshal.GetLastWin32Error()).Message));
                    }
                    finally
                    {
                        threadHandle.Dispose();
                    }
                }

                public static void ResumeProcessById(int pid)
                {
                    var proc = Process.GetProcessById(pid);

                    // wait for at least one suspended thread in the process (this handles possible slow startup race where
                    // primary thread of created-suspended process has not yet become runnable)
                    var retryCount = 0;
                    while(!proc.Threads.OfType<ProcessThread>().Any(t=>t.ThreadState == System.Diagnostics.ThreadState.Wait &&
                        t.WaitReason == ThreadWaitReason.Suspended))
                    {
                        proc.Refresh();
                        Thread.Sleep(50);
                        if (retryCount > 100)
                            throw new InvalidOperationException(String.Format("No threads were suspended in target PID {0} after 5s", pid));
                    }

                    foreach(var thread in proc.Threads.OfType<ProcessThread>().Where(t => t.ThreadState == System.Diagnostics.ThreadState.Wait &&
                        t.WaitReason == ThreadWaitReason.Suspended))
                        ResumeThreadById(thread.Id);
                }
            }

            [StructLayout(LayoutKind.Sequential)]
            public class SECURITY_ATTRIBUTES
            {
                public int nLength;
                public IntPtr lpSecurityDescriptor;
                public bool bInheritHandle = false;

                public SECURITY_ATTRIBUTES() {
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
                public Int32 dwX;
                public Int32 dwY;
                public Int32 dwXSize;
                public Int32 dwYSize;
                public Int32 dwXCountChars;
                public Int32 dwYCountChars;
                public Int32 dwFillAttribute;
                public Int32 dwFlags;
                public Int16 wShowWindow;
                public Int16 cbReserved2;
                public IntPtr lpReserved2;
                public IntPtr hStdInput;
                public IntPtr hStdOutput;
                public IntPtr hStdError;

                public STARTUPINFO() {
                    cb = Marshal.SizeOf(this);
                }
            }

            [StructLayout(LayoutKind.Sequential)]
            public class STARTUPINFOEX {
                public STARTUPINFO startupInfo;
                public IntPtr lpAttributeList;

                public STARTUPINFOEX() {
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

            [Flags]
            enum ThreadAccessRights : uint
            {
                SUSPEND_RESUME = 0x0002
            }

            [Flags]
            public enum StartupInfoFlags : uint
            {
                USESTDHANDLES = 0x00000100
            }

            public enum StandardHandleValues : int
            {
                STD_INPUT_HANDLE = -10,
                STD_OUTPUT_HANDLE = -11,
                STD_ERROR_HANDLE = -12
            }

            [Flags]
            public enum HandleFlags : uint
            {
                None = 0,
                INHERIT = 1
            }
        }
"@ # END Ansible.Async native type definition

    $original_tmp = $env:TMP
    $original_temp = $env:TEMP
    $remote_tmp = $payload["module_args"]["_ansible_remote_tmp"]
    $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
    if ($null -eq $remote_tmp) {
        $remote_tmp = $original_tmp
    }

    # calculate the result path so we can include it in the worker payload
    $jid = $payload.async_jid
    $local_jid = $jid + "." + $pid

    $results_path = [System.IO.Path]::Combine($remote_tmp, ".ansible_async", $local_jid)

    $payload.async_results_path = $results_path

    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($results_path)) | Out-Null

    $env:TMP = $remote_tmp
    $env:TEMP = $remote_tmp
    Add-Type -TypeDefinition $native_process_util -Debug:$false
    $env:TMP = $original_tmp
    $env:TEMP = $original_temp

    # FUTURE: create under new job to ensure all children die on exit?

    # FUTURE: move these flags into C# enum?
    # start process suspended + breakaway so we can record the watchdog pid without worrying about a completion race
    Set-Variable CREATE_BREAKAWAY_FROM_JOB -Value ([uint32]0x01000000) -Option Constant
    Set-Variable CREATE_SUSPENDED -Value ([uint32]0x00000004) -Option Constant
    Set-Variable CREATE_UNICODE_ENVIRONMENT -Value ([uint32]0x000000400) -Option Constant
    Set-Variable CREATE_NEW_CONSOLE -Value ([uint32]0x00000010) -Option Constant
    Set-Variable EXTENDED_STARTUPINFO_PRESENT -Value ([uint32]0x00080000) -Option Constant

    $pstartup_flags = $CREATE_BREAKAWAY_FROM_JOB -bor $CREATE_UNICODE_ENVIRONMENT -bor $CREATE_NEW_CONSOLE `
        -bor $CREATE_SUSPENDED -bor $EXTENDED_STARTUPINFO_PRESENT

    # execute the dynamic watchdog as a breakway process to free us from the WinRM job, which will in turn exec the module
    $si = New-Object Ansible.Async.STARTUPINFOEX

    # setup stdin redirection, we'll leave stdout/stderr as normal
    $si.startupInfo.dwFlags = [Ansible.Async.StartupInfoFlags]::USESTDHANDLES
    $si.startupInfo.hStdOutput = [Ansible.Async.NativeProcessUtil]::GetStdHandle([Ansible.Async.StandardHandleValues]::STD_OUTPUT_HANDLE)
    $si.startupInfo.hStdError = [Ansible.Async.NativeProcessUtil]::GetStdHandle([Ansible.Async.StandardHandleValues]::STD_ERROR_HANDLE)

    $stdin_read = $stdin_write = 0

    $pipesec = New-Object Ansible.Async.SECURITY_ATTRIBUTES
    $pipesec.bInheritHandle = $true

    If(-not [Ansible.Async.NativeProcessUtil]::CreatePipe([ref]$stdin_read, [ref]$stdin_write, $pipesec, 0)) {
        throw "Stdin pipe setup failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    If(-not [Ansible.Async.NativeProcessUtil]::SetHandleInformation($stdin_write, [Ansible.Async.HandleFlags]::INHERIT, 0)) {
        throw "Stdin handle setup failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    $si.startupInfo.hStdInput = $stdin_read

    # create an attribute list with our explicit handle inheritance list to pass to CreateProcess
    [int]$buf_sz = 0

    # determine the buffer size necessary for our attribute list
    If(-not [Ansible.Async.NativeProcessUtil]::InitializeProcThreadAttributeList([IntPtr]::Zero, 1, 0, [ref]$buf_sz)) {
        $last_err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        If($last_err -ne 122) { # ERROR_INSUFFICIENT_BUFFER
            throw "Attribute list size query failed, Win32Error: $last_err"
        }
    }

    $si.lpAttributeList = [System.Runtime.InteropServices.Marshal]::AllocHGlobal($buf_sz)

    # initialize the attribute list
    If(-not [Ansible.Async.NativeProcessUtil]::InitializeProcThreadAttributeList($si.lpAttributeList, 1, 0, [ref]$buf_sz)) {
        throw "Attribute list init failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }

    $handles_to_inherit = [IntPtr[]]@($stdin_read)
    $pinned_handles = [System.Runtime.InteropServices.GCHandle]::Alloc($handles_to_inherit, [System.Runtime.InteropServices.GCHandleType]::Pinned)

    # update the attribute list with the handles we want to inherit
    If(-not [Ansible.Async.NativeProcessUtil]::UpdateProcThreadAttribute($si.lpAttributeList, 0, 0x20002 <# PROC_THREAD_ATTRIBUTE_HANDLE_LIST #>, `
        $pinned_handles.AddrOfPinnedObject(), [System.Runtime.InteropServices.Marshal]::SizeOf([type][IntPtr]) * $handles_to_inherit.Length, `
        [System.IntPtr]::Zero, [System.IntPtr]::Zero)) {
        throw "Attribute list update failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }

    # need to use a preamble-free version of UTF8Encoding
    $utf8_encoding = New-Object System.Text.UTF8Encoding @($false)
    $stdin_fs = New-Object System.IO.FileStream @($stdin_write, [System.IO.FileAccess]::Write, $true, 32768)
    $stdin = New-Object System.IO.StreamWriter @($stdin_fs, $utf8_encoding, 32768)

    $pi = New-Object Ansible.Async.PROCESS_INFORMATION

    $encoded_command = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($exec_wrapper.ToString()))

    # FUTURE: direct cmdline CreateProcess path lookup fails- this works but is sub-optimal
    $exec_cmd = [Ansible.Async.NativeProcessUtil]::SearchPath("powershell.exe")
    $exec_args = New-Object System.Text.StringBuilder @("`"$exec_cmd`" -NonInteractive -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded_command")

    # TODO: use proper Win32Exception + error
    If(-not [Ansible.Async.NativeProcessUtil]::CreateProcess($exec_cmd, $exec_args,
        [IntPtr]::Zero, [IntPtr]::Zero, $true, $pstartup_flags, [IntPtr]::Zero, $env:windir, $si, [ref]$pi)) {
        #throw New-Object System.ComponentModel.Win32Exception
        throw "Worker creation failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }

    # FUTURE: watch process for quick exit, capture stdout/stderr and return failure

    $watchdog_pid = $pi.dwProcessId

    [Ansible.Async.NativeProcessUtil]::ResumeProcessById($watchdog_pid)

    # once process is resumed, we can send payload over stdin
    $payload_string = $payload | ConvertTo-Json -Depth 99 -Compress
    $stdin.WriteLine($payload_string)
    $stdin.Close()

    # populate initial results before we resume the process to avoid result race
    $result = @{
        started=1;
        finished=0;
        results_file=$results_path;
        ansible_job_id=$local_jid;
        _ansible_suppress_tmpdir_delete=$true;
        ansible_async_watchdog_pid=$watchdog_pid
    }

    $result_json = ConvertTo-Json $result
    Set-Content $results_path -Value $result_json

    return $result_json
}

'''  # end async_wrapper

async_watchdog = br'''
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Web.Extensions

Function Log {
    Param(
        [string]$msg
    )

    If(Get-Variable -Name log_path -ErrorAction SilentlyContinue) {
        Add-Content $log_path $msg
    }
}

Function Deserialize-Json {
    Param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$json
    )

    # FUTURE: move this into module_utils/powershell.ps1 and use for everything (sidestep PSCustomObject issues)
    # FUTURE: won't work w/ Nano Server/.NET Core- fallback to DataContractJsonSerializer (which can't handle dicts on .NET 4.0)

    Log "Deserializing:`n$json"

    $jss = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    return $jss.DeserializeObject($json)
}

Function Write-Result {
    Param(
        [hashtable]$result,
        [string]$resultfile_path
    )

    $result | ConvertTo-Json | Set-Content -Path $resultfile_path
}

Function Run($payload) {
    $actions = $payload.actions

    # pop 0th action as entrypoint
    $entrypoint = $payload.($actions[0])
    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

    $payload.actions = $payload.actions[1..99]

    $resultfile_path = $payload.async_results_path
    $max_exec_time_sec = $payload.async_timeout_sec

    Log "deserializing existing resultfile args"
    # read in existing resultsfile to merge w/ module output (it should be written by the time we're unsuspended and running)
    $result = Get-Content $resultfile_path -Raw | Deserialize-Json

    Log "deserialized result is $($result | Out-String)"

    Log "creating runspace"

    $rs = [runspacefactory]::CreateRunspace()
    $rs.Open()

    Log "creating Powershell object"

    $job = [powershell]::Create()
    $job.Runspace = $rs

    $job.AddScript($entrypoint) | Out-Null
    $job.AddStatement().AddCommand("Run").AddArgument($payload) | Out-Null

    Log "job BeginInvoke()"

    $job_asyncresult = $job.BeginInvoke()

    Log "waiting $max_exec_time_sec seconds for job to complete"

    $signaled = $job_asyncresult.AsyncWaitHandle.WaitOne($max_exec_time_sec * 1000)

    $result["finished"] = 1

    If($job_asyncresult.IsCompleted) {
        Log "job completed, calling EndInvoke()"

        $job_output = $job.EndInvoke($job_asyncresult)
        $job_error = $job.Streams.Error

        Log "raw module stdout: \r\n$job_output"
        If($job_error) {
            Log "raw module stderr: \r\n$job_error"
        }

        # write success/output/error to result object

        # TODO: cleanse leading/trailing junk
        Try {
            $module_result = Deserialize-Json $job_output
            # TODO: check for conflicting keys
            $result = $result + $module_result
        }
        Catch {
            $excep = $_

            $result.failed = $true
            $result.msg = "failed to parse module output: $excep"
        }

        # TODO: determine success/fail, or always include stderr if nonempty?
        Write-Result $result $resultfile_path

        Log "wrote output to $resultfile_path"
    }
    Else {
        $job.BeginStop($null, $null) | Out-Null # best effort stop
        # write timeout to result object
        $result.failed = $true
        $result.msg = "timed out waiting for module completion"
        Write-Result $result $resultfile_path

        Log "wrote timeout to $resultfile_path"
    }

    # in the case of a hung pipeline, this will cause the process to stay alive until it's un-hung...
    #$rs.Close() | Out-Null
}

'''  # end async_watchdog

from ansible.plugins import AnsiblePlugin


class ShellModule(ShellBase):

    # Common shell filenames that this plugin handles
    # Powershell is handled differently.  It's selected when winrm is the
    # connection
    COMPATIBLE_SHELLS = frozenset()
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'powershell'

    env = dict()

    # We're being overly cautious about which keys to accept (more so than
    # the Windows environment is capable of doing), since the powershell
    # env provider's limitations don't appear to be documented.
    safe_envkey = re.compile(r'^[\d\w_]{1,255}$')

    # TODO: add binary module support

    def assert_safe_env_key(self, key):
        if not self.safe_envkey.match(key):
            raise AnsibleError("Invalid PowerShell environment key: %s" % key)
        return key

    def safe_env_value(self, key, value):
        if len(value) > 32767:
            raise AnsibleError("PowerShell environment value for key '%s' exceeds 32767 characters in length" % key)
        # powershell single quoted literals need single-quote doubling as their only escaping
        value = value.replace("'", "''")
        return to_text(value, errors='surrogate_or_strict')

    def env_prefix(self, **kwargs):
        # powershell/winrm env handling is handled in the exec wrapper
        return ""

    def join_path(self, *args):
        parts = []
        for arg in args:
            arg = self._unquote(arg).replace('/', '\\')
            parts.extend([a for a in arg.split('\\') if a])
        path = '\\'.join(parts)
        if path.startswith('~'):
            return path
        return path

    def get_remote_filename(self, pathname):
        # powershell requires that script files end with .ps1
        base_name = os.path.basename(pathname.strip())
        name, ext = os.path.splitext(base_name.strip())
        if ext.lower() not in ['.ps1', '.exe']:
            return name + '.ps1'

        return base_name.strip()

    def path_has_trailing_slash(self, path):
        # Allow Windows paths to be specified using either slash.
        path = self._unquote(path)
        return path.endswith('/') or path.endswith('\\')

    def chmod(self, paths, mode):
        raise NotImplementedError('chmod is not implemented for Powershell')

    def chown(self, paths, user):
        raise NotImplementedError('chown is not implemented for Powershell')

    def set_user_facl(self, paths, user, mode):
        raise NotImplementedError('set_user_facl is not implemented for Powershell')

    def remove(self, path, recurse=False):
        path = self._escape(self._unquote(path))
        if recurse:
            return self._encode_script('''Remove-Item "%s" -Force -Recurse;''' % path)
        else:
            return self._encode_script('''Remove-Item "%s" -Force;''' % path)

    def mkdtemp(self, basefile=None, system=False, mode=None, tmpdir=None):
        # Windows does not have an equivalent for the system temp files, so
        # the param is ignored
        basefile = self._escape(self._unquote(basefile))
        basetmpdir = tmpdir if tmpdir else self.get_option('remote_tmp')

        script = '''
        $tmp_path = [System.Environment]::ExpandEnvironmentVariables('%s')
        $tmp = New-Item -Type Directory -Path $tmp_path -Name '%s'
        $tmp.FullName | Write-Host -Separator ''
        ''' % (basetmpdir, basefile)
        return self._encode_script(script.strip())

    def expand_user(self, user_home_path, username=''):
        # PowerShell only supports "~" (not "~username").  Resolve-Path ~ does
        # not seem to work remotely, though by default we are always starting
        # in the user's home directory.
        user_home_path = self._unquote(user_home_path)
        if user_home_path == '~':
            script = 'Write-Host (Get-Location).Path'
        elif user_home_path.startswith('~\\'):
            script = 'Write-Host ((Get-Location).Path + "%s")' % self._escape(user_home_path[1:])
        else:
            script = 'Write-Host "%s"' % self._escape(user_home_path)
        return self._encode_script(script)

    def exists(self, path):
        path = self._escape(self._unquote(path))
        script = '''
            If (Test-Path "%s")
            {
                $res = 0;
            }
            Else
            {
                $res = 1;
            }
            Write-Host "$res";
            Exit $res;
         ''' % path
        return self._encode_script(script)

    def checksum(self, path, *args, **kwargs):
        path = self._escape(self._unquote(path))
        script = '''
            If (Test-Path -PathType Leaf "%(path)s")
            {
                $sp = new-object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider;
                $fp = [System.IO.File]::Open("%(path)s", [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read);
                [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
                $fp.Dispose();
            }
            ElseIf (Test-Path -PathType Container "%(path)s")
            {
                Write-Host "3";
            }
            Else
            {
                Write-Host "1";
            }
        ''' % dict(path=path)
        return self._encode_script(script)

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        # pipelining bypass
        if cmd == '':
            return '-'

        # non-pipelining

        cmd_parts = shlex.split(to_native(cmd), posix=False)
        cmd_parts = list(map(to_text, cmd_parts))
        if shebang and shebang.lower() == '#!powershell':
            if not self._unquote(cmd_parts[0]).lower().endswith('.ps1'):
                cmd_parts[0] = '"%s.ps1"' % self._unquote(cmd_parts[0])
            cmd_parts.insert(0, '&')
        elif shebang and shebang.startswith('#!'):
            cmd_parts.insert(0, shebang[2:])
        elif not shebang:
            # The module is assumed to be a binary
            cmd_parts[0] = self._unquote(cmd_parts[0])
            cmd_parts.append(arg_path)
        script = '''
            Try
            {
                %s
                %s
            }
            Catch
            {
                $_obj = @{ failed = $true }
                If ($_.Exception.GetType)
                {
                    $_obj.Add('msg', $_.Exception.Message)
                }
                Else
                {
                    $_obj.Add('msg', $_.ToString())
                }
                If ($_.InvocationInfo.PositionMessage)
                {
                    $_obj.Add('exception', $_.InvocationInfo.PositionMessage)
                }
                ElseIf ($_.ScriptStackTrace)
                {
                    $_obj.Add('exception', $_.ScriptStackTrace)
                }
                Try
                {
                    $_obj.Add('error_record', ($_ | ConvertTo-Json | ConvertFrom-Json))
                }
                Catch
                {
                }
                Echo $_obj | ConvertTo-Json -Compress -Depth 99
                Exit 1
            }
        ''' % (env_string, ' '.join(cmd_parts))
        return self._encode_script(script, preserve_rc=False)

    def wrap_for_exec(self, cmd):
        return '& %s' % cmd

    def _unquote(self, value):
        '''Remove any matching quotes that wrap the given value.'''
        value = to_text(value or '')
        m = re.match(r'^\s*?\'(.*?)\'\s*?$', value)
        if m:
            return m.group(1)
        m = re.match(r'^\s*?"(.*?)"\s*?$', value)
        if m:
            return m.group(1)
        return value

    def _escape(self, value, include_vars=False):
        '''Return value escaped for use in PowerShell command.'''
        # http://www.techotopia.com/index.php/Windows_PowerShell_1.0_String_Quoting_and_Escape_Sequences
        # http://stackoverflow.com/questions/764360/a-list-of-string-replacements-in-python
        subs = [('\n', '`n'), ('\r', '`r'), ('\t', '`t'), ('\a', '`a'),
                ('\b', '`b'), ('\f', '`f'), ('\v', '`v'), ('"', '`"'),
                ('\'', '`\''), ('`', '``'), ('\x00', '`0')]
        if include_vars:
            subs.append(('$', '`$'))
        pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
        substs = [s for p, s in subs]

        def replace(m):
            return substs[m.lastindex - 1]

        return re.sub(pattern, replace, value)

    def _encode_script(self, script, as_list=False, strict_mode=True, preserve_rc=True):
        '''Convert a PowerShell script to a single base64-encoded command.'''
        script = to_text(script)

        if script == u'-':
            cmd_parts = _common_args + ['-']

        else:
            if strict_mode:
                script = u'Set-StrictMode -Version Latest\r\n%s' % script
            # try to propagate exit code if present- won't work with begin/process/end-style scripts (ala put_file)
            # NB: the exit code returned may be incorrect in the case of a successful command followed by an invalid command
            if preserve_rc:
                script = u'%s\r\nIf (-not $?) { If (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { exit $LASTEXITCODE } Else { exit 1 } }\r\n'\
                    % script
            script = '\n'.join([x.strip() for x in script.splitlines() if x.strip()])
            encoded_script = to_text(base64.b64encode(script.encode('utf-16-le')), 'utf-8')
            cmd_parts = _common_args + ['-EncodedCommand', encoded_script]

        if as_list:
            return cmd_parts
        return ' '.join(cmd_parts)
