#!powershell
# This file is part of Ansible
#
# Copyright 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
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

# See also: https://technet.microsoft.com/en-us/sysinternals/pxexec.aspx

$params = Parse-Args $args

$command = Get-AnsibleParam -obj $params -name "command" -type "str" -failifempty $true
$executable = Get-AnsibleParam -obj $params -name "executable" -type "path" -default "psexec.exe"
$hostnames = Get-AnsibleParam -obj $params -name "hostnames" -type "list"
$username = Get-AnsibleParam -obj $params -name "username" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$chdir = Get-AnsibleParam -obj $params -name "chdir" -type "path"
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $true
$nobanner = Get-AnsibleParam -obj $params -name "nobanner" -type "bool" -default $false
$noprofile = Get-AnsibleParam -obj $params -name "noprofile" -type "bool" -default $false
$elevated = Get-AnsibleParam -obj $params -name "elevated" -type "bool" -default $false
$limited = Get-AnsibleParam -obj $params -name "limited" -type "bool" -default $false
$system = Get-AnsibleParam -obj $params -name "system" -type "bool" -default $false
$interactive = Get-AnsibleParam -obj $params -name "interactive" -type "bool" -default $false
$priority = Get-AnsibleParam -obj $params -name "priority" -type "str" -validateset "background","low","belownormal","abovenormal","high","realtime"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int"
$extra_opts = Get-AnsibleParam -obj $params -name "extra_opts" -type "list"

$result = @{
    changed = $true
}

If (-Not (Get-Command $executable -ErrorAction SilentlyContinue)) {
    Fail-Json $result "Executable '$executable' was not found."
}

$util_def = @'
using System;
using System.ComponentModel;
using System.IO;
using System.Threading;

namespace Ansible.Command {

    public static class NativeUtil {

        public static void GetProcessOutput(StreamReader stdoutStream, StreamReader stderrStream, out string stdout, out string stderr) {
            var sowait = new EventWaitHandle(false, EventResetMode.ManualReset);
            var sewait = new EventWaitHandle(false, EventResetMode.ManualReset);

            string so = null, se = null;

            ThreadPool.QueueUserWorkItem((s)=> {
                so = stdoutStream.ReadToEnd();
                sowait.Set();
            });

            ThreadPool.QueueUserWorkItem((s) => {
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

$util_type = Add-Type -TypeDefinition $util_def

$arguments = ""

If ($nobanner -eq $true) {
    $arguments += " -nobanner"
}

# Support running on local system if no hostname is specified
If ($hostnames) {
  $arguments += " \\" + $($hostnames | sort -Unique) -join ','
}

# Username is optional
If ($username -ne $null) {
    $arguments += " -u `"$username`""
}

# Password is optional
If ($password -ne $null) {
    $arguments += " -p `"$password`""
}

If ($chdir -ne $null) {
    $arguments += " -w `"$chdir`""
}

If ($wait -eq $false) {
    $arguments += " -d"
}

If ($noprofile -eq $true) {
    $arguments += " -e"
}

If ($elevated -eq $true) {
    $arguments += " -h"
}

If ($system -eq $true) {
    $arguments += " -s"
}

If ($interactive -eq $true) {
    $arguments += " -i"
}

If ($limited -eq $true) {
    $arguments += " -l"
}

If ($priority -ne $null) {
    $arguments += " -$priority"
}

If ($timeout -ne $null) {
    $arguments += " -n $timeout"
}

# Add additional advanced options
If ($extra_opts) {
    ForEach ($opt in $extra_opts) {
        $arguments += " $opt"
    }
}

$arguments += " -accepteula"

$proc = New-Object System.Diagnostics.Process
$psi = $proc.StartInfo
$psi.FileName = $executable
$psi.Arguments = "$arguments $command"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false

$result.psexec_command = "$executable$arguments $command"

$start_datetime = [DateTime]::UtcNow

Try {
    $proc.Start() | Out-Null # will always return $true for non shell-exec cases
} Catch [System.ComponentModel.Win32Exception] {
    # fail nicely for "normal" error conditions
    # FUTURE: this probably won't work on Nano Server
    $excep = $_
    $result.rc = $excep.Exception.NativeErrorCode
    Fail-Json $result $excep.Exception.Message
}

$stdout = $stderr = [string] $null

[Ansible.Command.NativeUtil]::GetProcessOutput($proc.StandardOutput, $proc.StandardError, [ref] $stdout, [ref] $stderr) | Out-Null

$result.stdout = $stdout
$result.stderr = $stderr

$proc.WaitForExit() | Out-Null

If ($wait -eq $true) {
    $result.rc = $proc.ExitCode
} else {
    $result.rc = 0
    $result.pid = $proc.ExitCode
}

$end_datetime = [DateTime]::UtcNow

$result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

Exit-Json $result

