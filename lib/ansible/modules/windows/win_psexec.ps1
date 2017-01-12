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

$params = Parse-Args $args;

$result = New-Object PSObject @{
    changed = $true
}

$command = Get-AnsibleParam -obj $params -name "command" -default "whoami.exe"
$executable = Get-AnsibleParam -obj $params -name "executable" -default "psexec.exe"
$hostnames = Get-AnsibleParam -obj $params -name "hostnames"
$username = Get-AnsibleParam -obj $params -name "username"
$password = Get-AnsibleParam -obj $params -name "password" -failifempty $true
$chdir = Get-AnsibleParam -obj $params -name "chdir"
$noprofile = Get-AnsibleParam -obj $params -name "noprofile"
$elevated = Get-AnsibleParam -obj $params -name "elevated"
$limited = Get-AnsibleParam -obj $params -name "limited"
$system = Get-AnsibleParam -obj $params -name "system"
$priority = Get-AnsibleParam -obj $params -name "priority" -validateset "background","low","belownormal","abovenormal","high","realtime"
$timeout = Get-AnsibleParam -obj $params -name "timeout"
$extra_opts = Get-AnsibleParam -obj $params -name "extra_opts" -default @()

$args = ""

# Supports running on local system if not hostname is specified
If ($hostnames -ne $null) {
  $args = " \\" + $($hostnames | sort -Unique) -join ','
}

$pinfo = New-Object System.Diagnostics.ProcessStartInfo

$pinfo.FileName = $executable
$pinfo.RedirectStandardError = $true
$pinfo.RedirectStandardOutput = $true
$pinfo.UseShellExecute = $false

# Username is optional
If ($username -ne $null) {
    $args += " -u " + $username
}

# Password is required
If ($password -eq $null) {
    Fail-Json $result "The 'password' parameter is a required parameter."
} Else {
    $args += " -p " + $password
}

If ($chdir -ne $null) {
    $args += " -w " + $chdir
}

If ($noprofile -ne $null) {
    $args += " -e"
}

If ($elevated -ne $null) {
    $args += " -h"
}

If ($system -ne $null) {
    $args += " -s"
}

If ($limited -ne $null) {
    $args += " -l"
}

If ($priority -ne $null) {
    $args += " -" + $priority
}

If ($timeout -ne $null) {
    $args += " -n " + $timeout
}

$args += " -accepteula"

# Add additional advanced options
ForEach ($opt in $extra_opts) {
    $args += " " + $opt
}

# Defaults to whoami.exe, but also accepts a script instead of command
$args += " " + $command

# TODO: psexec has a limit to the argument length of 260 (?)
$pinfo.Arguments = $args

$p = New-Object System.Diagnostics.Process
$p.StartInfo = $pinfo
$p.Start() | Out-Null
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$rc = $p.ExitCode

If ($rc -eq 0) {
    Set-Attr $result "failed" $false
} Else {
    Set-Attr $result "failed" $true
}

Set-Attr $result "cmd" ($executable + $args)
Set-Attr $result "rc" $rc
Set-Attr $result "stdout" $stdout
Set-Attr $result "stderr" $stderr

Exit-Json $result