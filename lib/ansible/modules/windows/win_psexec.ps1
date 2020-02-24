#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

# See also: https://technet.microsoft.com/en-us/sysinternals/pxexec.aspx

$spec = @{
    options = @{
        command = @{ type='str'; required=$true }
        executable = @{ type='path'; default='psexec.exe' }
        hostnames = @{ type='list' }
        username = @{ type='str' }
        password = @{ type='str'; no_log=$true }
        chdir = @{ type='path' }
        wait = @{ type='bool'; default=$true }
        nobanner = @{ type='bool'; default=$false }
        noprofile = @{ type='bool'; default=$false }
        elevated = @{ type='bool'; default=$false }
        limited = @{ type='bool'; default=$false }
        system = @{ type='bool'; default=$false }
        interactive = @{ type='bool'; default=$false }
        session = @{ type='int' }
        priority = @{ type='str'; choices=@( 'background', 'low', 'belownormal', 'abovenormal', 'high', 'realtime' ) }
        timeout = @{ type='int' }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$command = $module.Params.command
$executable = $module.Params.executable
$hostnames = $module.Params.hostnames
$username = $module.Params.username
$password = $module.Params.password
$chdir = $module.Params.chdir
$wait = $module.Params.wait
$nobanner = $module.Params.nobanner
$noprofile = $module.Params.noprofile
$elevated = $module.Params.elevated
$limited = $module.Params.limited
$system = $module.Params.system
$interactive = $module.Params.interactive
$session = $module.Params.session
$priority = $module.Params.Priority
$timeout = $module.Params.timeout

$module.Result.changed = $true

If (-Not (Get-Command $executable -ErrorAction SilentlyContinue)) {
    $module.FailJson("Executable '$executable' was not found.")
}

$arguments = [System.Collections.Generic.List`1[String]]@($executable)

If ($nobanner -eq $true) {
    $arguments.Add("-nobanner")
}

# Support running on local system if no hostname is specified
If ($hostnames) {
    $hostname_argument = ($hostnames | sort -Unique) -join ','
    $arguments.Add("\\$hostname_argument")
}

# Username is optional
If ($null -ne $username) {
    $arguments.Add("-u")
    $arguments.Add($username)
}

# Password is optional
If ($null -ne $password) {
    $arguments.Add("-p")
    $arguments.Add($password)
}

If ($null -ne $chdir) {
    $arguments.Add("-w")
    $arguments.Add($chdir)
}

If ($wait -eq $false) {
    $arguments.Add("-d")
}

If ($noprofile -eq $true) {
    $arguments.Add("-e")
}

If ($elevated -eq $true) {
    $arguments.Add("-h")
}

If ($system -eq $true) {
    $arguments.Add("-s")
}

If ($interactive -eq $true) {
    $arguments.Add("-i")
    If ($null -ne $session) {
        $arguments.Add($session)
    }
}

If ($limited -eq $true) {
    $arguments.Add("-l")
}

If ($null -ne $priority) {
    $arguments.Add("-$priority")
}

If ($null -ne $timeout) {
    $arguments.Add("-n")
    $arguments.Add($timeout)
}

$arguments.Add("-accepteula")

$argument_string = Argv-ToString -arguments $arguments

# Add the command at the end of the argument string, we don't want to escape
# that as psexec doesn't expect it to be one arg
$argument_string += " $command"

$start_datetime = [DateTime]::UtcNow
$module.Result.psexec_command = $argument_string

$command_result = Run-Command -command $argument_string

$end_datetime = [DateTime]::UtcNow

$module.Result.stdout = $command_result.stdout
$module.Result.stderr = $command_result.stderr

If ($wait -eq $true) {
    $module.Result.rc = $command_result.rc
} else {
    $module.Result.rc = 0
    $module.Result.pid = $command_result.rc
}

$module.Result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$module.Result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$module.Result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

$module.ExitJson()
