#!powershell

# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.SID

$spec = @{
    options = @{
        process_name_exact = @{ type='list' }
        process_name_pattern = @{ type='str' }
        pid = @{ type='int'; default=0 }
        owner = @{ type='str' }
        sleep = @{ type='int'; default=1 }
        pre_wait_delay = @{ type='int'; default=0 }
        post_wait_delay = @{ type='int'; default=0 }
        process_min_count = @{ type='int'; default=1 }
        state = @{ type='str'; default='present'; choices=@( 'absent', 'present' ) }
        timeout = @{ type='int'; default=300 }
    }
    mutually_exclusive = @(
        @( 'pid', 'process_name_exact' ),
        @( 'pid', 'process_name_pattern' ),
        @( 'process_name_exact', 'process_name_pattern' )
    )
    required_one_of = @(
        ,@( 'owner', 'pid', 'process_name_exact', 'process_name_pattern' )
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$process_name_exact = $module.Params.process_name_exact
$process_name_pattern = $module.Params.process_name_pattern
$process_id = $module.Params.pid  # pid is a reserved variable in PowerShell, using process_id instead
$owner = $module.Params.owner
$sleep = $module.Params.sleep
$pre_wait_delay = $module.Params.pre_wait_delay
$post_wait_delay = $module.Params.post_wait_delay
$process_min_count = $module.Params.process_min_count
$state = $module.Params.state
$timeout = $module.Params.timeout

$module.Result.changed = $false
$module.Result.elapsed = 0
$module.Result.matched_processes = @()

# Validate the input
if ($state -eq "absent" -and $sleep -ne 1) {
    $module.Warn("Parameter 'sleep' has no effect when waiting for a process to stop.")
}

if ($state -eq "absent" -and $process_min_count -ne 1) {
    $module.Warn("Parameter 'process_min_count' has no effect when waiting for a process to stop.")
}

if ($owner -and ("IncludeUserName" -notin (Get-Command -Name Get-Process).Parameters.Keys)) {
    $module.FailJson("This version of Powershell does not support filtering processes by 'owner'.")
}

Function Get-FilteredProcesses {
    [cmdletbinding()]
    Param(
        [String]
        $Owner,
        $ProcessNameExact,
        $ProcessNamePattern,
        [int]
        $ProcessId
    )

    $FilteredProcesses = @()

    try {
        $Processes = Get-Process -IncludeUserName
        $SupportsUserNames = $true
    } catch [System.Management.Automation.ParameterBindingException] {
        $Processes = Get-Process
        $SupportsUserNames = $false
    }

    foreach ($Process in $Processes) {

        # If a process name was specified in the filter, validate that here.
        if ($ProcessNamePattern) {
            if ($Process.ProcessName -notmatch $ProcessNamePattern) {
                continue
            }
        }

        # If a process name was specified in the filter, validate that here.
        if ($ProcessNameExact -is [Array]) {
            if ($ProcessNameExact -notcontains $Process.ProcessName) {
                continue
            }
        } elseif ($ProcessNameExact) {
            if ($ProcessNameExact -ne $Process.ProcessName) {
                continue
            }
        }

        # If a PID was specified in the filter, validate that here.
        if ($ProcessId -and $ProcessId -ne 0) {
            if ($ProcessId -ne $Process.Id) {
                continue
            }
        }

        # If an owner was specified in the filter, validate that here.
        if ($Owner) {
            if (-not $Process.UserName) {
                continue
            } elseif ((Convert-ToSID($Owner)) -ne (Convert-ToSID($Process.UserName))) {  # NOTE: This is rather expensive
                continue
            }
        }

        if ($SupportsUserNames -eq $true) {
            $FilteredProcesses += @{ name = $Process.ProcessName; pid = $Process.Id; owner = $Process.UserName }
        } else {
            $FilteredProcesses += @{ name = $Process.ProcessName; pid = $Process.Id }
        }
    }

    return ,$FilteredProcesses
}

$module_start = Get-Date
Start-Sleep -Seconds $pre_wait_delay

if ($state -eq "present" ) {

    # Wait for a process to start
    do {

        $Processes = Get-FilteredProcesses -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id
        $module.Result.matched_processes = $Processes

        if ($Processes.count -ge $process_min_count) {
            break
        }

        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout) {
            $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $module.FailJson("Timed out while waiting for process(es) to start")
        }

        Start-Sleep -Seconds $sleep

    } while ($true)

} elseif ($state -eq "absent") {

    # Wait for a process to stop
    $Processes = Get-FilteredProcesses -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id
    $module.Result.matched_processes = $Processes

    if ($Processes.count -gt 0 ) {
        try {
            # This may randomly fail when used on specially protected processes (think: svchost)
            Wait-Process -Id $Processes.pid -Timeout $timeout
        } catch [System.TimeoutException] {
            $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $module.FailJson("Timeout while waiting for process(es) to stop")
        }
    }

}

Start-Sleep -Seconds $post_wait_delay
$module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds

$module.ExitJson()
