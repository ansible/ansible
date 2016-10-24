#!powershell
# This file is part of Ansible
#
# Copyright (c)2016, Matt Davis
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

Param(
    [string]$jid,
    [int]$max_exec_time_sec,
    [string]$module_path,
    [string]$argfile_path,
    [switch]$preserve_tmp
)

# WANT_JSON
# POWERSHELL_COMMON

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

Function Start-Watchdog {
    Param(
        [string]$module_tempdir,
        [string]$module_path,
        [int]$max_exec_time_sec,
        [string]$resultfile_path,
        [string]$argfile_path,
        [switch]$preserve_tmp,
        [switch]$start_suspended
    )

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
                [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
                public static extern bool CreateProcess(
                    string lpApplicationName,
                    string lpCommandLine,
                    IntPtr lpProcessAttributes,
                    IntPtr lpThreadAttributes,
                    bool bInheritHandles,
                    uint dwCreationFlags,
                    IntPtr lpEnvironment,
                    string lpCurrentDirectory,
                    [In] ref STARTUPINFO lpStartupInfo,
                    out PROCESS_INFORMATION lpProcessInformation);

                [DllImport("kernel32.dll", SetLastError = true, CharSet=CharSet.Unicode)]
                public static extern uint SearchPath (
                    string lpPath,
                    string lpFileName,
                    string lpExtension,
                    int nBufferLength,
                    [MarshalAs (UnmanagedType.LPTStr)]
                    StringBuilder lpBuffer,
                    out IntPtr lpFilePart);

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
                        throw new Exception(String.Format("Thread ID {0} is invalid ({1})", threadId, new Win32Exception(Marshal.GetLastWin32Error()).Message));

                    try
                    {
                        if(ResumeThread(threadHandle) == -1)
                            throw new Exception(String.Format("Thread ID {0} cannot be resumed ({1})", threadId, new Win32Exception(Marshal.GetLastWin32Error()).Message));
                    }
                    finally
                    {
                        threadHandle.Dispose();
                    }
                }

                public static void ResumeProcessById(int pid)
                {
                    var proc = Process.GetProcessById(pid);

                    // wait for at least one suspended thread in the process (this handles possible slow startup race where primary thread of created-suspended process has not yet become runnable)
                    var retryCount = 0;
                    while(!proc.Threads.OfType<ProcessThread>().Any(t=>t.ThreadState == System.Diagnostics.ThreadState.Wait && t.WaitReason == ThreadWaitReason.Suspended))
                    {
                        proc.Refresh();
                        Thread.Sleep(50);
                        if (retryCount > 100)
                            throw new InvalidOperationException(String.Format("No threads were suspended in target PID {0} after 5s", pid));
                    }

                    foreach(var thread in proc.Threads.OfType<ProcessThread>().Where(t => t.ThreadState == System.Diagnostics.ThreadState.Wait && t.WaitReason == ThreadWaitReason.Suspended))
                        ResumeThreadById(thread.Id);
                }
            }

            [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
            public struct STARTUPINFO
            {
                public Int32 cb;
                public string lpReserved;
                public string lpDesktop;
                public string lpTitle;
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
        }
"@ # END Ansible.Async native type definition

    Add-Type -TypeDefinition $native_process_util

    $watchdog_script = {
        Set-StrictMode -Version 2
        $ErrorActionPreference = "Stop"

        Function Log {
            Param(
                [string]$msg
            )

            If(Get-Variable -Name log_path -ErrorAction SilentlyContinue) {
                Add-Content $log_path $msg
            }
        }

        Add-Type -AssemblyName System.Web.Extensions

        # -EncodedCommand won't allow us to pass args, so they have to be templated into the script
        $jsonargs = @"
        <<JSONARGS>>
"@
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
            [hashtable]$result,
            [string]$resultfile_path

            $result | ConvertTo-Json | Set-Content -Path $resultfile_path
        }

        Function Exec-Module {
            Param(
                [string]$module_tempdir,
                [string]$module_path,
                [int]$max_exec_time_sec,
                [string]$resultfile_path,
                [string]$argfile_path,
                [switch]$preserve_tmp
            )

            Log "in watchdog exec"

            Try
            {
                Log "deserializing existing resultfile args"
                # read in existing resultsfile to merge w/ module output (it should be written by the time we're unsuspended and running)
                $result = Get-Content $resultfile_path -Raw | Deserialize-Json

                Log "deserialized result is $($result | Out-String)"

                Log "creating runspace"

                $rs = [runspacefactory]::CreateRunspace()
                $rs.Open()
                $rs.SessionStateProxy.Path.SetLocation($module_tempdir) | Out-Null

                Log "creating Powershell object"

                $job = [powershell]::Create()
                $job.Runspace = $rs

                Log "adding scripts"

                if($module_path.EndsWith(".ps1")) {
                    $job.AddScript($module_path) | Out-Null
                }
                else {
                    $job.AddCommand($module_path) | Out-Null
                    $job.AddArgument($argfile_path) | Out-Null
                }

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
                    $job.Stop()
                    # write timeout to result object
                    $result.failed = $true
                    $result.msg = "timed out waiting for module completion"
                    Write-Result $result $resultfile_path

                    Log "wrote timeout to $resultfile_path"
                }

                $rs.Close() | Out-Null
            }
            Catch {
                $excep = $_

                $result = @{failed=$true; msg="module execution failed: $($excep.ToString())`n$($excep.InvocationInfo.PositionMessage)"}

                Write-Result $result $resultfile_path
            }
            Finally
            {
                If(-not $preserve_tmp -and $module_tempdir -imatch "-tmp-") {
                    Try {
                        Log "deleting tempdir, cwd is $(Get-Location)"
                        Set-Location $env:USERPROFILE
                        $res = Remove-Item $module_tempdir -recurse 2>&1
                        Log "delete output was $res"
                    }
                    Catch {
                        $excep = $_
                        Log "error deleting tempdir: $excep"
                    }
                }
                Else {
                    Log "skipping tempdir deletion"
                }
            }
        }

        Try {
            Log "deserializing args"

            # deserialize the JSON args that should've been templated in before execution
            $ext_args = Deserialize-Json $jsonargs

            Log "exec module"

            Exec-Module @ext_args

            Log "exec done"
        }
        Catch {
            $excep = $_

            Log $excep
        }
    }

    $bp = [hashtable] $MyInvocation.BoundParameters
    # convert switch types to bool so they'll serialize as simple bools
    $bp["preserve_tmp"] = [bool]$bp["preserve_tmp"]
    $bp["start_suspended"] = [bool]$bp["start_suspended"]

    # serialize this function's args to JSON so we can template them verbatim into the script(block)
    $jsonargs =  $bp | ConvertTo-Json

    $raw_script = $watchdog_script.ToString()
    $raw_script = $raw_script.Replace("<<JSONARGS>>", $jsonargs)

    $encoded_command = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($raw_script))

    # FUTURE: create under new job to ensure all children die on exit?

    # FUTURE: move these flags into C# enum
    # start process suspended + breakaway so we can record the watchdog pid without worrying about a completion race
    Set-Variable CREATE_BREAKAWAY_FROM_JOB -Value ([uint32]0x01000000) -Option Constant
    Set-Variable CREATE_SUSPENDED -Value ([uint32]0x00000004) -Option Constant
    Set-Variable CREATE_UNICODE_ENVIRONMENT -Value ([uint32]0x000000400) -Option Constant
    Set-Variable CREATE_NEW_CONSOLE -Value ([uint32]0x00000010) -Option Constant

    $pstartup_flags = $CREATE_BREAKAWAY_FROM_JOB -bor $CREATE_UNICODE_ENVIRONMENT -bor $CREATE_NEW_CONSOLE
    If($start_suspended) {
        $pstartup_flags = $pstartup_flags -bor $CREATE_SUSPENDED
    }

    # execute the dynamic watchdog as a breakway process, which will in turn exec the module
    $si = New-Object Ansible.Async.STARTUPINFO
    $si.cb = [System.Runtime.InteropServices.Marshal]::SizeOf([type][Ansible.Async.STARTUPINFO])

    $pi = New-Object Ansible.Async.PROCESS_INFORMATION

    # FUTURE: direct cmdline CreateProcess path lookup fails- this works but is sub-optimal
    $exec_cmd = [Ansible.Async.NativeProcessUtil]::SearchPath("powershell.exe")
    $exec_args = "`"$exec_cmd`" -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded_command"

    If(-not [Ansible.Async.NativeProcessUtil]::CreateProcess($exec_cmd, $exec_args, [IntPtr]::Zero, [IntPtr]::Zero, $true, $pstartup_flags, [IntPtr]::Zero, $env:windir, [ref]$si, [ref]$pi)) {
        #throw New-Object System.ComponentModel.Win32Exception
        throw "create bang $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }

    $watchdog_pid = $pi.dwProcessId

    return $watchdog_pid
}

$local_jid = $jid + "." + $pid

$results_path = [System.IO.Path]::Combine($env:LOCALAPPDATA, ".ansible_async", $local_jid)

[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($results_path)) | Out-Null

$watchdog_args = @{
        module_tempdir=$([System.IO.Path]::GetDirectoryName($module_path));
        module_path=$module_path;
        max_exec_time_sec=$max_exec_time_sec;
        resultfile_path=$results_path;
        argfile_path=$argfile_path;
        start_suspended=$true;
}

If($preserve_tmp) {
    $watchdog_args["preserve_tmp"] = $true
}

# start watchdog/module-exec
$watchdog_pid = Start-Watchdog @watchdog_args

# populate initial results before we resume the process to avoid result race
$result = @{
    started=1;
    finished=0;
    results_file=$results_path;
    ansible_job_id=$local_jid;
    _suppress_tmpdir_delete=$true;
    ansible_async_watchdog_pid=$watchdog_pid
}

$result_json = ConvertTo-Json $result
Set-Content $results_path -Value $result_json

[Ansible.Async.NativeProcessUtil]::ResumeProcessById($watchdog_pid)

return $result_json
