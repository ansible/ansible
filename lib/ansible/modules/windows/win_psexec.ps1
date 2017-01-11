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

$commandline = Get-AnsibleParam -obj $params -name "commandline" -default "whoami.exe"
$executable = Get-AnsibleParam -obj $params -name "executable" -default "psexec.exe"
$hostname = Get-AnsibleParam -obj $params -name "hostname"
$username = Get-AnsibleParam -obj $params -name "username"
$password = Get-AnsibleParam -obj $params -name "password" -failifempty $true
$chdir = Get-AnsibleParam -obj $params -name "chdir"
$timeout = Get-AnsibleParam -obj $params -name "timeout"
# TODO: Implement priority options
#$priority = Get-AnsibleParam -obj $params -name "priority"
$extra_opts = Get-AnsibleParam -obj $params -name "extra_opts" -default @()

$args = ""

# Supports running on local system if not hostname is specified
If ($hostname -Ne $Null) {
  $args = "\\" + $hostname
}

$pinfo = New-Object System.Diagnostics.ProcessStartInfo

$pinfo.FileName = $executable
$pinfo.RedirectStandardError = $true
$pinfo.RedirectStandardOutput = $true
$pinfo.UseShellExecute = $false

# Username is optional
If ($username -Ne $null) {
    $args += " -u " + $username
}

# Password is required
If ($password -Eq $null) {
    Fail-Json @{msg="The 'password' parameter is a required parameter."}
} Else {
    $args += " -p " + $password
}

If ($chdir -ne $null) {
    $args += " -w " + $chdir
}

If ($timeout -ne $null) {
    $args += " -n " + $timeout
}

$args += " -accepteula"

# Add additional advanced options
ForEach ($opt in $extra_opts){
    $args += " " + $opt
}

# Defaults to whoami.exe, but also accepts a script instead of commandline
$args += " " + $commandline

# TODO: psexec has a limit to the argument length of 260 (?)
$pinfo.Arguments = $args

$p = New-Object System.Diagnostics.Process
$p.StartInfo = $pinfo
$p.Start() | Out-Null
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$rc = $p.ExitCode

If ($rc -Eq 0) {
    Set-Attr $result "failed" $False
} Else {
    Set-Attr $result "failed" $True
}

Set-Attr $result "cmd" ( $executable + " " + $args )
Set-Attr $result "rc" $rc
Set-Attr $result "stdout" $stdout
Set-Attr $result "stderr" $stderr

Exit-Json $result