#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true

$process_name = Get-AnsibleParam -obj $params -name "process_name" -type "str" 
$sleep = Get-AnsibleParam -obj $params -name "sleep" -type "int" -default 1
$process_min_count = Get-AnsibleParam -obj $params -name "process_min_count" -type "int" -default 1
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 300

$result = @{
    changed = $false
}

# validate the input
if ($state -eq "absent" -and $sleep -ne 1)
{
    Fail-json $result "sleep parameter is of no effet when waiting for a proces to stop."
}

$module_start = Get-Date
if ($state -eq "present" )
{
    #wait for a process to start
    $Processes = @()
    $attempts = -1
    Do {
        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout)
        {
            Fail-Json $result "timeout while waiting for $process_name to start"
        }
        $Processes = Get-Process | Where-Object {$_.ProcessName -match $process_name}
        Start-Sleep -Seconds $sleep
        $attempts ++
    } While ($Processes.count -lt $process_min_count)

    if ($attempts -gt 0)
    {
        $result.changed = $true
    }
    $result.matched_processess = ($Processes.count)
    #$result.processess = $Processes
}
elseif ($state -eq "absent")
{
    #wait for a process to stop
    $Processes = Get-Process | Where-Object {$_.ProcessName -match $process_name} 
    if ($Processes.count -gt 0 )
    {
        try { 
            Wait-Process -Id $($Processes | Select-Object -ExpandProperty ID) -Timeout $timeout -ErrorAction Stop
           
            $result.matched_processess = ($Processes.count)
            $result.changed = $true
        }
        catch {
            Fail-Json $result "timeout while waiting for $process_name to stop"
        }
    }
    else{
        $result.changed = $false

    }
}
$result.elapsed = ((Get-Date) - $module_start).TotalSeconds
Exit-Json $result