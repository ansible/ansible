# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os
import re
import shlex

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text


_common_args = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted']

# Primarily for testing, allow explicitly specifying PowerShell version via
# an environment variable.
_powershell_version = os.environ.get('POWERSHELL_VERSION', None)
if _powershell_version:
    _common_args = ['PowerShell', '-Version', _powershell_version] + _common_args[1:]

exec_wrapper = br'''
#Requires -Version 3.0
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

    $json_raw = ""
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

''' # end exec_wrapper

leaf_exec = br'''
Function Run($payload) {
    $entrypoint = $payload.module_entry

    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

    $ps = [powershell]::Create()

    $ps.AddStatement().AddCommand("Set-Variable").AddParameters(@{Scope="global";Name="complex_args";Value=$payload.module_args}) | Out-Null
    $ps.AddCommand("Out-Null") | Out-Null

    # redefine Write-Host to dump to output instead of failing- lots of scripts use it
    $ps.AddStatement().AddScript("Function Write-Host(`$msg){ Write-Output `$msg }") | Out-Null

    # dynamically create/load modules
    ForEach ($mod in $payload.powershell_modules.GetEnumerator()) {
        $decoded_module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mod.Value))
        $ps.AddStatement().AddCommand("New-Module").AddParameters(@{ScriptBlock=([scriptblock]::Create($decoded_module));Name=$mod.Key}) | Out-Null
        $ps.AddCommand("Import-Module").AddParameters(@{WarningAction="SilentlyContinue"}) | Out-Null
        $ps.AddCommand("Out-Null") | Out-Null
    }

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
        $host.SetShouldExit($exit_code)
    }
}
''' # end leaf_exec


become_wrapper = br'''
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$helper_def = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Security;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Runtime.InteropServices;

namespace Ansible.Shell
{
    public class ProcessUtil
    {
        public static void GetProcessOutput(StreamReader stdoutStream, StreamReader stderrStream, out string stdout, out string stderr)
        {
            var sowait = new EventWaitHandle(false, EventResetMode.ManualReset);
            var sewait = new EventWaitHandle(false, EventResetMode.ManualReset);

            string so = null, se = null;

            ThreadPool.QueueUserWorkItem((s)=>
            {
                so = stdoutStream.ReadToEnd();
                sowait.Set();
            });

            ThreadPool.QueueUserWorkItem((s) =>
            {
                se = stderrStream.ReadToEnd();
                sewait.Set();
            });

            foreach(var wh in new WaitHandle[] { sowait, sewait })
                wh.WaitOne();

            stdout = so;
            stderr = se;
        }

        // http://stackoverflow.com/a/30687230/139652
        public static void GrantAccessToWindowStationAndDesktop(string username)
        {
            const int WindowStationAllAccess = 0x000f037f;
            GrantAccess(username, GetProcessWindowStation(), WindowStationAllAccess);
            const int DesktopRightsAllAccess = 0x000f01ff;
            GrantAccess(username, GetThreadDesktop(GetCurrentThreadId()), DesktopRightsAllAccess);
        }

        private static void GrantAccess(string username, IntPtr handle, int accessMask)
        {
            SafeHandle safeHandle = new NoopSafeHandle(handle);
            GenericSecurity security =
                new GenericSecurity(false, ResourceType.WindowObject, safeHandle, AccessControlSections.Access);

            security.AddAccessRule(
                new GenericAccessRule(new NTAccount(username), accessMask, AccessControlType.Allow));
            security.Persist(safeHandle, AccessControlSections.Access);
        }

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr GetProcessWindowStation();

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr GetThreadDesktop(int dwThreadId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern int GetCurrentThreadId();

        private class GenericAccessRule : AccessRule
        {
            public GenericAccessRule(IdentityReference identity, int accessMask, AccessControlType type) :
                base(identity, accessMask, false, InheritanceFlags.None, PropagationFlags.None, type) { }
        }

        private class GenericSecurity : NativeObjectSecurity
        {
            public GenericSecurity(bool isContainer, ResourceType resType, SafeHandle objectHandle, AccessControlSections sectionsRequested)
                : base(isContainer, resType, objectHandle, sectionsRequested) { }

            public new void Persist(SafeHandle handle, AccessControlSections includeSections) { base.Persist(handle, includeSections); }

            public new void AddAccessRule(AccessRule rule) { base.AddAccessRule(rule); }

            public override Type AccessRightType { get { throw new NotImplementedException(); } }

            public override AccessRule AccessRuleFactory(System.Security.Principal.IdentityReference identityReference, int accessMask, bool isInherited,
                InheritanceFlags inheritanceFlags, PropagationFlags propagationFlags, AccessControlType type) { throw new NotImplementedException(); }

            public override Type AccessRuleType { get { return typeof(AccessRule); } }

            public override AuditRule AuditRuleFactory(System.Security.Principal.IdentityReference identityReference, int accessMask, bool isInherited,
                InheritanceFlags inheritanceFlags, PropagationFlags propagationFlags, AuditFlags flags) { throw new NotImplementedException(); }

            public override Type AuditRuleType { get { return typeof(AuditRule); } }
        }

        private class NoopSafeHandle : SafeHandle
        {
            public NoopSafeHandle(IntPtr handle) : base(handle, false) { }
            public override bool IsInvalid { get { return false; } }
            protected override bool ReleaseHandle() { return true; }
        }

    }
}
"@

$exec_wrapper = {
#Requires -Version 3.0
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
    # NB: action popping handled inside subprocess wrapper

    $username = $payload.become_user
    $password = $payload.become_password

    Add-Type -TypeDefinition $helper_def
    Add-Type -TypeDefinition $helper_def -Debug:$false

    $exec_args = $null

    $exec_application = "powershell"

    # NB: CreateProcessWithLogonW commandline maxes out at 1024 chars, must bootstrap via filesystem
    $temp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".ps1")
    $exec_wrapper.ToString() | Set-Content -Path $temp

    # TODO: grant target user permissions on tempfile/tempdir

    Try {

        # Base64 encode the command so we don't have to worry about the various levels of escaping
        # $encoded_command = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($exec_wrapper.ToString()))

        # force the input encoding to preamble-free UTF8 before we create the new process
        [System.Console]::InputEncoding = $(New-Object System.Text.UTF8Encoding @($false))

        $exec_args = @("-noninteractive", $temp)

        $proc = New-Object System.Diagnostics.Process
        $psi = $proc.StartInfo
        $psi.FileName = $exec_application
        $psi.Arguments = $exec_args
        $psi.RedirectStandardInput = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false

        If($username.Contains("\")) {
            $sp = $username.Split(@([char]"\"), 2)
            $domain = $sp[0]
            $username = $sp[1]
        }
        ElseIf ($username.Contains("@")) {
            $domain = $null
        }
        Else {
            $domain = "."
        }

        $psi.Domain = $domain
        $psi.Username = $username
        $psi.Password = $($password | ConvertTo-SecureString -AsPlainText -Force)

        [Ansible.Shell.ProcessUtil]::GrantAccessToWindowStationAndDesktop($username)

        $proc.Start() | Out-Null # will always return $true for non shell-exec cases

        $payload_string = $payload | ConvertTo-Json -Depth 99 -Compress

        # push the execution payload over stdin
        $proc.StandardInput.WriteLine($payload_string)
        $proc.StandardInput.Close()

        $stdout = $stderr = [string] $null

        [Ansible.Shell.ProcessUtil]::GetProcessOutput($proc.StandardOutput, $proc.StandardError, [ref] $stdout, [ref] $stderr) | Out-Null

        # TODO: decode CLIXML stderr output (and other streams?)

        $proc.WaitForExit() | Out-Null

        $rc = $proc.ExitCode

        If ($rc -eq 0) {
            $stdout
            $stderr
        }
        Else {
            Throw "failed, rc was $rc, stderr was $stderr, stdout was $stdout"
        }
    }
    Finally {
        Remove-Item $temp -ErrorAction SilentlyContinue
    }

}

''' # end become_wrapper


async_wrapper = br'''
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

# build exec_wrapper encoded command
# start powershell with breakaway running exec_wrapper encodedcommand
# stream payload to powershell with normal exec, but normal exec writes results to resultfile instead of stdout/stderr
# return asyncresult to controller

$exec_wrapper = {
#Requires -Version 3.0
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
                    STARTUPINFO lpStartupInfo,
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

    # calculate the result path so we can include it in the worker payload
    $jid = $payload.async_jid
    $local_jid = $jid + "." + $pid

    $results_path = [System.IO.Path]::Combine($env:LOCALAPPDATA, ".ansible_async", $local_jid)

    $payload.async_results_path = $results_path

    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($results_path)) | Out-Null

    Add-Type -TypeDefinition $native_process_util
    Add-Type -TypeDefinition $native_process_util -Debug:$false

    # FUTURE: create under new job to ensure all children die on exit?

    # FUTURE: move these flags into C# enum
    # start process suspended + breakaway so we can record the watchdog pid without worrying about a completion race
    Set-Variable CREATE_BREAKAWAY_FROM_JOB -Value ([uint32]0x01000000) -Option Constant
    Set-Variable CREATE_SUSPENDED -Value ([uint32]0x00000004) -Option Constant
    Set-Variable CREATE_UNICODE_ENVIRONMENT -Value ([uint32]0x000000400) -Option Constant
    Set-Variable CREATE_NEW_CONSOLE -Value ([uint32]0x00000010) -Option Constant

    $pstartup_flags = $CREATE_BREAKAWAY_FROM_JOB -bor $CREATE_UNICODE_ENVIRONMENT -bor $CREATE_NEW_CONSOLE -bor $CREATE_SUSPENDED

    # execute the dynamic watchdog as a breakway process, which will in turn exec the module
    $si = New-Object Ansible.Async.STARTUPINFO

    # setup stdin redirection, we'll leave stdout/stderr as normal
    $si.dwFlags = [Ansible.Async.StartupInfoFlags]::USESTDHANDLES
    $si.hStdOutput = [Ansible.Async.NativeProcessUtil]::GetStdHandle([Ansible.Async.StandardHandleValues]::STD_OUTPUT_HANDLE)
    $si.hStdError = [Ansible.Async.NativeProcessUtil]::GetStdHandle([Ansible.Async.StandardHandleValues]::STD_ERROR_HANDLE)

    $stdin_read = $stdin_write = 0

    $pipesec = New-Object Ansible.Async.SECURITY_ATTRIBUTES
    $pipesec.bInheritHandle = $true

    If(-not [Ansible.Async.NativeProcessUtil]::CreatePipe([ref]$stdin_read, [ref]$stdin_write, $pipesec, 0)) {
        throw "Stdin pipe setup failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    If(-not [Ansible.Async.NativeProcessUtil]::SetHandleInformation($stdin_write, [Ansible.Async.HandleFlags]::INHERIT, 0)) {
        throw "Stdin handle setup failed, Win32Error: $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    $si.hStdInput = $stdin_read

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

''' # end async_wrapper

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

''' # end async_watchdog

class ShellModule(object):

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

    # TODO: implement module transfer
    # TODO: implement #Requires -Modules parser/locator
    # TODO: add raw failure + errcode preservation (all success right now)
    # TODO: add KEEP_REMOTE_FILES support + debug wrapper dump
    # TODO: add become support
    # TODO: add binary module support
    # TODO: figure out non-pipelined path (or force pipelining)


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
        env = self.env.copy()
        env.update(kwargs)
        return ';'.join(["$env:%s='%s'" % (self.assert_safe_env_key(k), self.safe_env_value(k,v)) for k,v in env.items()])

    def join_path(self, *args):
        parts = []
        for arg in args:
            arg = self._unquote(arg).replace('/', '\\')
            parts.extend([a for a in arg.split('\\') if a])
        path = '\\'.join(parts)
        if path.startswith('~'):
            return path
        return '\'%s\'' % path

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

    def mkdtemp(self, basefile, system=False, mode=None, tmpdir=None):
        basefile = self._escape(self._unquote(basefile))
        # FIXME: Support system temp path and passed in tmpdir!
        return self._encode_script('''(New-Item -Type Directory -Path $env:temp -Name "%s").FullName | Write-Host -Separator '';''' % basefile)

    def expand_user(self, user_home_path):
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

    def build_module_command(self, env_string, shebang, cmd, arg_path=None, rm_tmp=None):
        # pipelining bypass
        if cmd == '':
            return ''

        # non-pipelining

        cmd_parts = shlex.split(to_bytes(cmd), posix=False)
        cmd_parts = map(to_text, cmd_parts)
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
        if rm_tmp:
            rm_tmp = self._escape(self._unquote(rm_tmp))
            rm_cmd = 'Remove-Item "%s" -Force -Recurse -ErrorAction SilentlyContinue' % rm_tmp
            script = '%s\nFinally { %s }' % (script, rm_cmd)
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
        replace = lambda m: substs[m.lastindex - 1]
        return re.sub(pattern, replace, value)

    def _encode_script(self, script, as_list=False, strict_mode=True, preserve_rc=True):
        '''Convert a PowerShell script to a single base64-encoded command.'''
        script = to_text(script)
        if strict_mode:
            script = u'Set-StrictMode -Version Latest\r\n%s' % script
        # try to propagate exit code if present- won't work with begin/process/end-style scripts (ala put_file)
        # NB: the exit code returned may be incorrect in the case of a successful command followed by an invalid command
        if preserve_rc:
            script = u'%s\r\nIf (-not $?) { If (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { exit $LASTEXITCODE } Else { exit 1 } }\r\n' % script
        script = '\n'.join([x.strip() for x in script.splitlines() if x.strip()])
        encoded_script = base64.b64encode(script.encode('utf-16-le'))
        cmd_parts = _common_args + ['-EncodedCommand', encoded_script]
        if as_list:
            return cmd_parts
        return ' '.join(cmd_parts)
