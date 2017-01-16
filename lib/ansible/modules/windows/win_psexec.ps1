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

$command = Get-AnsibleParam -obj $params -name "command" -default "whoami.exe"
$executable = Get-AnsibleParam -obj $params -name "executable" -default "psexec.exe"
$hostnames = Get-AnsibleParam -obj $params -name "hostnames"
$username = Get-AnsibleParam -obj $params -name "username"
$password = Get-AnsibleParam -obj $params -name "password" -failifempty $true
$chdir = Get-AnsibleParam -obj $params -name "chdir" -type "path"
$noprofile = Get-AnsibleParam -obj $params -name "noprofile"
$elevated = Get-AnsibleParam -obj $params -name "elevated"
$limited = Get-AnsibleParam -obj $params -name "limited"
$system = Get-AnsibleParam -obj $params -name "system"
$priority = Get-AnsibleParam -obj $params -name "priority" -validateset "background","low","belownormal","abovenormal","high","realtime"
$timeout = Get-AnsibleParam -obj $params -name "timeout"
$extra_opts = Get-AnsibleParam -obj $params -name "extra_opts" -default @()

$result = @{
    changed = $true
}

$extra_args = ""

# Supports running on local system if not hostname is specified
If ($hostnames -ne $null) {
  $extra_args = " \\" + $($hostnames | sort -Unique) -join ','
}

# Username is optional
If ($username -ne $null) {
    $extra_args += " -u " + $username
}

# Password is required
If ($password -eq $null) {
    Fail-Json $result "The 'password' parameter is a required parameter."
} Else {
    $extra_args += " -p " + $password
}

If ($chdir -ne $null) {
    $extra_args += " -w " + $chdir
}

If ($noprofile -ne $null) {
    $extra_args += " -e"
}

If ($elevated -ne $null) {
    $extra_args += " -h"
}

If ($system -ne $null) {
    $extra_args += " -s"
}

If ($limited -ne $null) {
    $extra_args += " -l"
}

If ($priority -ne $null) {
    $extra_args += " -" + $priority
}

If ($timeout -ne $null) {
    $extra_args += " -n " + $timeout
}

$extra_args += " -accepteula"

# Add additional advanced options
ForEach ($opt in $extra_opts) {
    $extra_args += " " + $opt
}

$extra_args += " " + $command

$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName = $executable
$pinfo.RedirectStandardError = $true
$pinfo.RedirectStandardOutput = $true
$pinfo.UseShellExecute = $false
# TODO: psexec has a limit to the argument length of 260 (?)
$pinfo.Arguments = $extra_args

$result.psexec_command = ($executable + $extra_args)

$p = New-Object System.Diagnostics.Process
$p.StartInfo = $pinfo
$p.Start() | Out-Null
$result.stdout = $p.StandardOutput.ReadToEnd()
$result.stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$result.rc = $p.ExitCode

If ($result.rc -eq 0) {
    $result.failed = $false
} Else {
    $result.failed = $true
}

Exit-Json $result