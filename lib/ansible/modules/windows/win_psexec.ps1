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

$command = Get-AnsibleParam -obj $params -name "command" -failifempty $true
$executable = Get-AnsibleParam -obj $params -name "executable" -default "psexec.exe"
$hostnames = Get-AnsibleParam -obj $params -name "hostnames"
$username = Get-AnsibleParam -obj $params -name "username"
$password = Get-AnsibleParam -obj $params -name "password"
$chdir = Get-AnsibleParam -obj $params -name "chdir" -type "path"
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $true
$noprofile = Get-AnsibleParam -obj $params -name "noprofile" -type "bool" -default $false
$elevated = Get-AnsibleParam -obj $params -name "elevated" -type "bool" -default $false
$limited = Get-AnsibleParam -obj $params -name "limited" -type "bool" -default $false
$system = Get-AnsibleParam -obj $params -name "system" -type "bool" -default $false
$interactive = Get-AnsibleParam -obj $params -name "interactive" -type "bool" -default $false
$priority = Get-AnsibleParam -obj $params -name "priority" -validateset "background","low","belownormal","abovenormal","high","realtime"
$timeout = Get-AnsibleParam -obj $params -name "timeout"
$extra_opts = Get-AnsibleParam -obj $params -name "extra_opts" -default @()

$result = @{
    changed = $true
}

$arguments = ""

# Supports running on local system if not hostname is specified
If ($hostnames -ne $null) {
  $arguments = " \\" + $($hostnames | sort -Unique) -join ','
}

# Username is optional
If ($username -ne $null) {
    $arguments += " -u \"$username\""
}

# Password is optional
If ($password -ne $null) {
    $arguments += " -p \"$password\""
}

If ($chdir -ne $null) {
    $arguments += " -w \"$chdir\""
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
ForEach ($opt in $extra_opts) {
    $arguments += " $opt"
}

$arguments += " -accepteula"

$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName = $executable
$pinfo.RedirectStandardError = $true
$pinfo.RedirectStandardOutput = $true
$pinfo.UseShellExecute = $false
# TODO: psexec has a limit to the argument length of 260 (?)
$pinfo.Arguments = "$arguments $command"

$result.psexec_command = "$executable$arguments $command"

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $pinfo
$proc.Start() | Out-Null
# TODO: Fix the possible deadlock
$result.stdout = $proc.StandardOutput.ReadToEnd()
$result.stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
$result.rc = $proc.ExitCode

If ($result.rc -eq 0) {
    $result.failed = $false
} Else {
    $result.failed = $true
}

Exit-Json $result
