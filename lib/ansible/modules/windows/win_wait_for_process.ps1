#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true

$process_name_exact = Get-AnsibleParam -obj $params -name "process_name_exact" -type "list"
$process_name_pattern = Get-AnsibleParam -obj $params -name "process_name_pattern" -type "str"
$process_id = Get-AnsibleParam -obj $params -name "pid" -type "int" -default 0 #pid is a reserved variable in PowerShell.  use process_id instead.
$owner = Get-AnsibleParam -obj $params -name "owner" -type "str"
$sleep = Get-AnsibleParam -obj $params -name "sleep" -type "int" -default 1
$pre_wait_delay = Get-AnsibleParam -obj $params -name "pre_wait_delay" -type "int" -default 0
$post_wait_delay = Get-AnsibleParam -obj $params -name "post_wait_delay" -type "int" -default 0
$process_min_count = Get-AnsibleParam -obj $params -name "process_min_count" -type "int" -default 1
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 300

$result = @{
    changed = $false
}

# validate the input
if ($state -eq "absent" -and $sleep -ne 1)
{
    Add-Warning -obj $result -message "sleep parameter has no effect when waiting for a process to stop."
}

if ($state -eq "absent" -and $process_min_count -ne 1)
{
    Add-Warning -obj $result -message "process_min_count parameter has no effect when waiting for a process to stop."
}

if (($process_name_exact -or $process_name_pattern) -and $process_id)
{
    Fail-json -obj $result -message "process_id may not be used with process_name_exact or process_name_pattern."
}
if ($process_name_exact -and $process_name_pattern)
{
    Fail-json -obj $result -message "process_name_exact and process_name_pattern may not be used at the same time."
}

if (-not ($process_name_exact -or $process_name_pattern -or $process_id -or $owner))
{
    Fail-json -obj $result -message "at least one of: process_name_exact, process_name_pattern, process_id, or owner must be supplied."
}

$module_start = Get-Date

#Get-Process doesn't actually return a UserName value, so get it from WMI.
Function Get-ProcessMatchesFilter {
    [cmdletbinding()]
    Param(
        [String]
        $Owner,
        $ProcessNameExact,
        $ProcessNamePattern,
        [int]
        $ProcessId
    )

    $CIMProcesses = Get-CimInstance Win32_Process
    foreach ($CIMProcess in $CIMProcesses)
    {
        $include = $true
        if(-not [String]::IsNullOrEmpty($ProcessNamePattern))
        {
            #if a process name was specified in the filter, validate that here.
            $include = $include -and ($CIMProcess.ProcessName -match $ProcessNamePattern)
        }
        if($ProcessNameExact -is [Array] -or (-not [String]::IsNullOrEmpty($ProcessNameExact)))
        {
            #if a process name was specified in the filter, validate that here.
            if ($ProcessNameExact -is [Array] )
            {
                $include = $include -and ($ProcessNameExact -contains $CIMProcess.ProcessName)
            }
            else {
                $include = $include -and ($ProcessNameExact -eq $CIMProcess.ProcessName)
            }
        }
        if ($ProcessId -and $ProcessId -ne 0)
        {
            # if a PID was specified in the filger, validate that here.
            $include = $include -and ($CIMProcess.ProcessId -eq $ProcessId)
        }
        if (-not [String]::IsNullOrEmpty($Owner) )
        {
            # if an owner was specified in the filter, validate that here.
            $include = $include -and ($($(Invoke-CimMethod -InputObject $CIMProcess -MethodName GetOwner).User) -eq $Owner)
        }

        if ($include)
        {
            $CIMProcess | Select-Object -Property ProcessId, ProcessName, @{name="Owner";Expression={$($(Invoke-CimMethod -InputObject $CIMProcess -MethodName GetOwner).User)}}
        }
    }
}

Start-Sleep -Seconds $pre_wait_delay
if ($state -eq "present" ) {
    #wait for a process to start
    $Processes = @()
    $attempts = 0
    Do {
        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout)
        {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            Fail-Json -obj $result -message "timeout while waiting for $process_name to start.  waited $timeout seconds"
        }

        $Processes = Get-ProcessMatchesFilter -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id
        Start-Sleep -Seconds $sleep
        $attempts ++
        $ProcessCount = $null
        if ($Processes -is [array]) {
            $ProcessCount = $Processes.count
        }
        elseif ($null -ne $Processes) {
            $ProcessCount = 1
        }
        else {
            $ProcessCount = 0
        }
    } While ($ProcessCount -lt $process_min_count)

    if ($Processes -is [array]) {
        $result.matched_processes = $Processes
    } elseif ($null -ne $Processes) {
        $result.matched_processes = ,$Processes
    } else {
        $result.matched_processes = @()
    }
}
elseif ($state -eq "absent") {
    #wait for a process to stop
    $Processes = Get-ProcessMatchesFilter -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id
    if ($Processes -is [array]) {
        $result.matched_processes = $Processes
    } elseif ($null -ne $Processes) {
        $result.matched_processes = ,$Processes
    } else {
        $result.matched_processes = @()
    }
    $ProcessCount = $(if ($Processes -is [array]) { $Processes.count } elseif ($Processes){ 1 } else {0})
    if ($ProcessCount -gt 0 )
    {
        try {
            Wait-Process -Id $($Processes | Select-Object -ExpandProperty ProcessId) -Timeout $timeout -ErrorAction Stop
        }
        catch {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            Fail-Json -obj $result -message "$($_.Exception.Message). timeout while waiting for $process_name to stop.  waited $timeout seconds"
        }
    }
}
Start-Sleep -Seconds $post_wait_delay
$result.elapsed = ((Get-Date) - $module_start).TotalSeconds
Exit-Json -obj $result
