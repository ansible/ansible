#!powershell
# This file is part of Ansible
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

# WANT_JSON
# POWERSHELL_COMMON

# TODO: add check mode support

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$helper_def = @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;

namespace Ansible.Command
{
    public static class NativeUtil
    {
        [DllImport("shell32.dll", SetLastError = true)]
        static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string lpCmdLine, out int pNumArgs);

        public static string[] ParseCommandLine(string cmdline)
        {
            int numArgs;
            IntPtr ret = CommandLineToArgvW(cmdline, out numArgs);

            if (ret == IntPtr.Zero)
                throw new Exception(String.Format("Error parsing command line: {0}", new Win32Exception(Marshal.GetLastWin32Error()).Message));

            IntPtr[] strptrs = new IntPtr[numArgs];
            Marshal.Copy(ret, strptrs, 0, numArgs);
            string[] cmdlineParts = strptrs.Select(s=>Marshal.PtrToStringUni(s)).ToArray();

            Marshal.FreeHGlobal(ret);

            return cmdlineParts;
        }

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
    }
}
'@

$params = Parse-Args $args -supports_check_mode $false

$raw_command_line = Get-AnsibleParam -obj $params -name "_raw_params" -type "str" -failifempty $true
$chdir = Get-AnsibleParam -obj $params -name "chdir" -type "path"
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"

$raw_command_line = $raw_command_line.Trim()

$result = @{
    changed = $true
    cmd = $raw_command_line
}

If($creates -and $(Test-Path -Path $creates)) {
    Exit-Json @{msg="skipped, since $creates exists";cmd=$raw_command_line;changed=$false;skipped=$true;rc=0}
}

If($removes -and -not $(Test-Path -Path $removes)) {
    Exit-Json @{msg="skipped, since $removes does not exist";cmd=$raw_command_line;changed=$false;skipped=$true;rc=0}
}

Add-Type -TypeDefinition $helper_def

$exec_args = $null

# FUTURE: extract this code to separate module_utils as Windows module API version of run_command

# Parse the command-line with the Win32 parser to get the application name to run. The Win32 parser
# will deal with quoting/escaping for us...
# FUTURE: no longer necessary once we switch to raw Win32 CreateProcess
$parsed_command_line = [Ansible.Command.NativeUtil]::ParseCommandLine($raw_command_line);
$exec_application = $parsed_command_line[0]
If($parsed_command_line.Length -gt 1) {
    # lop the application off, then rejoin the args as a single string
    $exec_args = $parsed_command_line[1..$($parsed_command_line.Length-1)] -join " "
}

$proc = New-Object System.Diagnostics.Process
$psi = $proc.StartInfo
$psi.FileName = $exec_application
$psi.Arguments = $exec_args
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false

If ($chdir) {
    $psi.WorkingDirectory = $chdir
}

$start_datetime = [DateTime]::UtcNow

Try {
    $proc.Start() | Out-Null # will always return $true for non shell-exec cases
}
Catch [System.ComponentModel.Win32Exception] {
    # fail nicely for "normal" error conditions
    # FUTURE: this probably won't work on Nano Server
    $excep = $_
    Exit-Json @{msg = $excep.Exception.Message; cmd = $raw_command_line; changed = $false; rc = $excep.Exception.NativeErrorCode}
}

$stdout = $stderr = [string] $null

[Ansible.Command.NativeUtil]::GetProcessOutput($proc.StandardOutput, $proc.StandardError, [ref] $stdout, [ref] $stderr) | Out-Null

$result.stdout = $stdout
$result.stderr = $stderr

# TODO: decode CLIXML stderr output (and other streams?)

$proc.WaitForExit() | Out-Null

$result.rc = $proc.ExitCode

$end_datetime = [DateTime]::UtcNow

$result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

If ($result.rc -ne 0) {
    Fail-Json -obj $result -message "non-zero return code"
}

Exit-Json $result
