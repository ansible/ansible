#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.FileUtil

# TODO: add check mode support

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

# Cleanse CLIXML from stderr (sift out error stream data, discard others for now)
Function Cleanse-Stderr($raw_stderr) {
    Try {
        # NB: this regex isn't perfect, but is decent at finding CLIXML amongst other stderr noise
        If($raw_stderr -match "(?s)(?<prenoise1>.*)#< CLIXML(?<prenoise2>.*)(?<clixml><Objs.+</Objs>)(?<postnoise>.*)") {
            $clixml = [xml]$matches["clixml"]

            $merged_stderr = "{0}{1}{2}{3}" -f @(
               $matches["prenoise1"],
               $matches["prenoise2"],
               # filter out just the Error-tagged strings for now, and zap embedded CRLF chars
               ($clixml.Objs.ChildNodes | Where-Object  { $_.Name -eq 'S' } | Where-Object { $_.S -eq 'Error' } | ForEach-Object { $_.'#text'.Replace('_x000D__x000A_','') } | Out-String),
               $matches["postnoise"]) | Out-String

            return $merged_stderr.Trim()

            # FUTURE: parse/return other streams
        }
        Else {
            $raw_stderr
        }
    }
    Catch {
        "***EXCEPTION PARSING CLIXML: $_***" + $raw_stderr
    }
}

$params = Parse-Args $args -supports_check_mode $false

$raw_command_line = Get-AnsibleParam -obj $params -name "_raw_params" -type "str" -failifempty $true
$chdir = Get-AnsibleParam -obj $params -name "chdir" -type "path"
$executable = Get-AnsibleParam -obj $params -name "executable" -type "path"
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"
$stdin = Get-AnsibleParam -obj $params -name "stdin" -type "str"
$no_profile = Get-AnsibleParam -obj $params -name "no_profile" -type "bool" -default $false

$raw_command_line = $raw_command_line.Trim()

$result = @{
    changed = $true
    cmd = $raw_command_line
}

if ($creates -and $(Test-AnsiblePath -Path $creates)) {
    Exit-Json @{msg="skipped, since $creates exists";cmd=$raw_command_line;changed=$false;skipped=$true;rc=0}
}

if ($removes -and -not $(Test-AnsiblePath -Path $removes)) {
    Exit-Json @{msg="skipped, since $removes does not exist";cmd=$raw_command_line;changed=$false;skipped=$true;rc=0}
}

$exec_args = $null
If(-not $executable -or $executable -eq "powershell") {
    $exec_application = "powershell.exe"

    # force input encoding to preamble-free UTF8 so PS sub-processes (eg, Start-Job) don't blow up
    $raw_command_line = "[Console]::InputEncoding = New-Object Text.UTF8Encoding `$false; " + $raw_command_line

    # Base64 encode the command so we don't have to worry about the various levels of escaping
    $encoded_command = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($raw_command_line))

    if ($stdin) {
        $exec_args = "-encodedcommand $encoded_command"
    } else {
        $exec_args = "-noninteractive -encodedcommand $encoded_command"
    }

    if ($no_profile) {
        $exec_args = "-noprofile $exec_args"
    }
}
Else {
    # FUTURE: support arg translation from executable (or executable_args?) to process arguments for arbitrary interpreter?
    $exec_application = $executable
    if (-not ($exec_application.EndsWith(".exe"))) {
        $exec_application = "$($exec_application).exe"
    }
    $exec_args = "/c $raw_command_line"
}

$command = "`"$exec_application`" $exec_args"
$run_command_arg = @{
    command = $command
}
if ($chdir) {
    $run_command_arg['working_directory'] = $chdir
}
if ($stdin) {
    $run_command_arg['stdin'] = $stdin
}

$start_datetime = [DateTime]::UtcNow
try {
    $command_result = Run-Command @run_command_arg
} catch {
    $result.changed = $false
    try {
        $result.rc = $_.Exception.NativeErrorCode
    } catch {
        $result.rc = 2
    }
    Fail-Json -obj $result -message $_.Exception.Message
}

# TODO: decode CLIXML stderr output (and other streams?)
$result.stdout = $command_result.stdout
$result.stderr = Cleanse-Stderr $command_result.stderr
$result.rc = $command_result.rc

$end_datetime = [DateTime]::UtcNow
$result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

If ($result.rc -ne 0) {
    Fail-Json -obj $result -message "non-zero return code"
}

Exit-Json $result
