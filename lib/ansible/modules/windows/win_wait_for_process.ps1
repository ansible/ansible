#!powershell

# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

# NOTE: Ensure we get proper debug information when things fall over
trap {
    if ($null -eq $result) { $result = @{} }
    $result.exception = "$($_ | Out-String)`r`n$($_.ScriptStackTrace)"
    Fail-Json -obj $result -message "Uncaught exception: $($_.Exception.Message)"
}

$params = Parse-Args -arguments $args -supports_check_mode $true

$process_name_exact = Get-AnsibleParam -obj $params -name "process_name_exact" -type "list"
$process_name_pattern = Get-AnsibleParam -obj $params -name "process_name_pattern" -type "str"
$process_id = Get-AnsibleParam -obj $params -name "pid" -type "int" -default 0  # pid is a reserved variable in PowerShell, using process_id instead.
$owner = Get-AnsibleParam -obj $params -name "owner" -type "str"
$sleep = Get-AnsibleParam -obj $params -name "sleep" -type "int" -default 1
$pre_wait_delay = Get-AnsibleParam -obj $params -name "pre_wait_delay" -type "int" -default 0
$post_wait_delay = Get-AnsibleParam -obj $params -name "post_wait_delay" -type "int" -default 0
$process_min_count = Get-AnsibleParam -obj $params -name "process_min_count" -type "int" -default 1
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 300

$result = @{
    changed = $false
    elapsed = 0
    matched_processes = @()
}

# Validate the input
if ($state -eq "absent" -and $sleep -ne 1) {
    Add-Warning -obj $result -message "Parameter 'sleep' has no effect when waiting for a process to stop."
}

if ($state -eq "absent" -and $process_min_count -ne 1) {
    Add-Warning -obj $result -message "Parameter 'process_min_count' has no effect when waiting for a process to stop."
}

if (($process_name_exact -or $process_name_pattern) -and $process_id) {
    Fail-Json -obj $result -message "Parameter 'pid' may not be used with process_name_exact or process_name_pattern."
}
if ($process_name_exact -and $process_name_pattern) {
    Fail-Json -obj $result -message "Parameter 'process_name_exact' and 'process_name_pattern' may not be used at the same time."
}

if (-not ($process_name_exact -or $process_name_pattern -or $process_id -or $owner)) {
    Fail-Json -obj $result -message "At least one of 'process_name_exact', 'process_name_pattern', 'pid' or 'owner' must be supplied."
}

if ($owner -and ("IncludeUserName" -notin (Get-Command -Name Get-Process).Parameters.Keys)) {
    Fail-Json -obj $result -message "This version of Powershell does not support filtering processes by 'owner'."
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
        $result.matched_processes = $Processes

        if ($Processes.count -ge $process_min_count) {
            break
        }

        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            Fail-Json -obj $result -message "Timed out while waiting for process(es) to start"
        }

        Start-Sleep -Seconds $sleep

    } while ($true)

} elseif ($state -eq "absent") {

    # Wait for a process to stop
    $Processes = Get-FilteredProcesses -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id
    $result.matched_processes = $Processes

    if ($Processes.count -gt 0 ) {
        try {
            # This may randomly fail when used on specially protected processes (think: svchost)
            Wait-Process -Id $Processes.pid -Timeout $timeout
        } catch [System.TimeoutException] {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            Fail-Json -obj $result -message "Timeout while waiting for process(es) to stop"
        }
    }

}

Start-Sleep -Seconds $post_wait_delay
$result.elapsed = ((Get-Date) - $module_start).TotalSeconds

Exit-Json -obj $result
