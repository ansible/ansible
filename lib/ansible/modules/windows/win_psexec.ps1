#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

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

$arguments = @()

If ($nobanner -eq $true) {
    $arguments += "-nobanner"
}

# Support running on local system if no hostname is specified
If ($hostnames) {
    $hostname_argument = ($hostnames | sort -Unique) -join ','
    $arguments += "\\$hostname_argument"
}

# Username is optional
If ($username -ne $null) {
    $arguments += "-u"
    $arguments += $username
}

# Password is optional
If ($password -ne $null) {
    $arguments += "-p"
    $arguments += $password
}

If ($chdir -ne $null) {
    $arguments += "-w"
    $arguments += $chdir
}

If ($wait -eq $false) {
    $arguments += "-d"
}

If ($noprofile -eq $true) {
    $arguments += "-e"
}

If ($elevated -eq $true) {
    $arguments += "-h"
}

If ($system -eq $true) {
    $arguments += "-s"
}

If ($interactive -eq $true) {
    $arguments += "-i"
}

If ($limited -eq $true) {
    $arguments += "-l"
}

If ($priority -ne $null) {
    $arguments += "-$priority"
}

If ($timeout -ne $null) {
    $arguments += "-n"
    $arguments += $timeout
}

# Add additional advanced options
If ($extra_opts) {
    ForEach ($opt in $extra_opts) {
        $arguments += $opt
    }
}

$arguments += "-accepteula"
$arguments += $command

$argument_string = Argv-ToString -arguments $arguments

$start_datetime = [DateTime]::UtcNow
$result.psexec_command = "$executable $argument_string"

$command_result = Run-Command -command "$executable $argument_string"

$end_datetime = [DateTime]::UtcNow

$result.stdout = $command_result.stdout
$result.stderr = $command_result.stderr

If ($wait -eq $true) {
    $result.rc = $command_result.rc
} else {
    $result.rc = 0
    $result.pid = $command_result.rc
}

$result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

Exit-Json $result
