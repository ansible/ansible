#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.ArgvParser

$ErrorActionPreference = 'Continue'

$params = Parse-Args $args
$exe = Get-AnsibleParam -obj $params -name "exe" -type "path" -failifempty $true

Add-Type -TypeDefinition @'
using System.IO;
using System.Threading;

namespace Ansible.Command
{
    public static class NativeUtil
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
    }
}
'@

Function Run-Process($executable, $arguments) {
    $proc = New-Object System.Diagnostics.Process
    $psi = $proc.StartInfo
    $psi.FileName = $executable
    $psi.Arguments = $arguments
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false

    $proc.Start() > $null # will always return $true for non shell-exec cases
    $stdout = $stderr = [string] $null

    [Ansible.Command.NativeUtil]::GetProcessOutput($proc.StandardOutput, $proc.StandardError, [ref] $stdout, [ref] $stderr) > $null
    $proc.WaitForExit() > $null
    $actual_args = $stdout.Substring(0, $stdout.Length - 2) -split "`r`n"

    return $actual_args
}

$tests = @(
    @('abc', 'd', 'e'),
    @('a\\b', 'de fg', 'h'),
    @('a\"b', 'c', 'd'),
    @('a\\b c', 'd', 'e'),
    @('C:\Program Files\file\', 'arg with " quote'),
    @('ADDLOCAL="a,b,c"', '/s', 'C:\\Double\\Backslash')
)

foreach ($expected in $tests) {
    $joined_string = Argv-ToString -arguments $expected
    # We can't used CommandLineToArgvW to test this out as it seems to mangle
    # \, might be something to do with unicode but not sure...
    $actual = Run-Process -executable $exe -arguments $joined_string

    if ($expected.Count -ne $actual.Count) {
        $result.actual = $actual -join "`n"
        $result.expected = $expected -join "`n"
        Fail-Json -obj $result -message "Actual arg count: $($actual.Count) != Expected arg count: $($expected.Count)"
    }
    for ($i = 0; $i -lt $expected.Count; $i++) {
        $expected_arg = $expected[$i]
        $actual_arg = $actual[$i]
        if ($expected_arg -cne $actual_arg) {
            $result.actual = $actual -join "`n"
            $result.expected = $expected -join "`n"
            Fail-Json -obj $result -message "Actual arg: '$actual_arg' != Expected arg: '$expected_arg'"
        }
    }
}

Exit-Json @{ data = 'success' }
