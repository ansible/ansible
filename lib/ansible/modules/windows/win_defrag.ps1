#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$include_volumes = Get-AnsibleParam -obj $params -name "include_volumes" -type "list"
$exclude_volumes = Get-AnsibleParam -obj $params -name "exclude_volumes" -type "list"
$freespace_consolidation = Get-AnsibleParam -obj $params -name "freespace_consolidation" -type "bool" -default $false
$priority = Get-AnsibleParam -obj $params -name "priority" -type "str" -default "low" -validateset "low","normal"
$parallel = Get-AnsibleParam -obj $params -name "parallel" -type "bool" -default $false

$result = @{
    changed = $false
}

$executable = "defrag.exe"

if (-not (Get-Command -Name $executable -ErrorAction SilentlyContinue)) {
    Fail-Json $result "Command '$executable' not found in $env:PATH."
}

$arguments = @()

if ($include_volumes) {
    foreach ($volume in $include_volumes) {
        if ($volume.Length -eq 1) {
            $arguments += "$($volume):"
        } else {
            $arguments += $volume
        }
    }
} else {
    $arguments += "/C"
}

if ($exclude_volumes) {
    $arguments += "/E"
    foreach ($volume in $exclude_volumes) {
        if ($volume.Length -eq 1) {
            $arguments += "$($volume):"
        } else {
            $arguments += $volume
        }
    }
}

if ($check_mode) {
    $arguments += "/A"
} elseif ($freespace_consolidation) {
    $arguments += "/X"
}

if ($priority -eq "normal") {
    $arguments += "/H"
}

if ($parallel) {
    $arguments += "/M"
}

$arguments += "/V"

$argument_string = Argv-ToString -arguments $arguments

$start_datetime = [DateTime]::UtcNow
$result.cmd = "$executable $argument_string"

$command_result = Run-Command -command "$executable $argument_string"

$end_datetime = [DateTime]::UtcNow

$result.stdout = $command_result.stdout
$result.stderr = $command_result.stderr
$result.rc = $command_result.rc

$result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

$result.changed = $true

Exit-Json $result
