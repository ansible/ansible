#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$spec = @{
    options = @{
        include_volumes = @{ type='list' }
        exclude_volumes = @{ type='list' }
        freespace_consolidation = @{ type='bool'; default=$false }
        priority = @{ type='str'; default='low'; choices=@( 'low', 'normal') }
        parallel = @{ type='bool'; default=$false }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$include_volumes = $module.Params.include_volumes
$exclude_volumes = $module.Params.exclude_volumes
$freespace_consolidation = $module.Params.freespace_consolidation
$priority = $module.Params.priority
$parallel = $module.Params.parallel

$module.Result.changed = $false

$executable = "defrag.exe"

if (-not (Get-Command -Name $executable -ErrorAction SilentlyContinue)) {
    $module.FailJson("Command '$executable' not found in $env:PATH.")
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

if ($module.CheckMode) {
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
$module.Result.cmd = "$executable $argument_string"

$command_result = Run-Command -command "$executable $argument_string"

$end_datetime = [DateTime]::UtcNow

$module.Result.stdout = $command_result.stdout
$module.Result.stderr = $command_result.stderr
$module.Result.rc = $command_result.rc

$module.Result.start = $start_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$module.Result.end = $end_datetime.ToString("yyyy-MM-dd hh:mm:ss.ffffff")
$module.Result.delta = $($end_datetime - $start_datetime).ToString("h\:mm\:ss\.ffffff")

$module.Result.changed = $true

$module.ExitJson()
