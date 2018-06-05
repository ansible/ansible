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
$process_id = Get-AnsibleParam -obj $params -name "process_id" -type "int" -default 0 #pid is a reserved variable in PowerShell.  use process_id instead.
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
    Fail-json $result "sleep parameter is of no effect when waiting for a proces to stop."
}

if (($process_name_exact -or $process_name_pattern) -and $process_id)
{
    Fail-json $result "process_id may not be used with process_name_exact or process_name_pattern"
}
if ($process_name_exact -and $process_name_pattern)
{
    Fail-json $result "process_name_exact and process_name_pattern may not be used at the same time."
}

if (-not ($process_name_exact -or $process_name_pattern -or $process_id -or $owner))
{
    Fail-json $result "at least one of: process_name_exact, process_name_pattern, process_id, or user must be supplied"
}

$module_start = Get-Date

#Get-Process doesn't actually return a UserName value, so get it from WMI.
Function Test-ProcessMatchesFilter {
    [cmdletbinding()]
    Param(
        [parameter(ValueFromPipeline)]
        $WindowsProcess,
        [String]
        $Owner,
        $ProcessNameExact,
        $ProcessNamePattern,
        [int]
        $ProcessId
    )
    Begin {
        $owners = @{}
        Get-WmiObject win32_process | ForEach-Object {$owners[$_.handle] = $_.getowner().user}
    }
    Process {
        $include = $true

        if ([String]::IsNullOrEmpty($WindowsProcess.Owner))
        {
            #always add the owner to proces info so that it's reported back.
            $WindowsProcess = $WindowsProcess | Select-Object -Property *,@{Name="Owner";Expression={$owners[$_.id.tostring()]}} 
        }
        if (-not [String]::IsNullOrEmpty($Owner) )
        {
            # if an owner was specified in the filter, validate that here.
            $include = $include -and ($WindowsProcess.Owner -eq $Owner)
        }
        if(-not [String]::IsNullOrEmpty($ProcessNamePattern))
        {
            #if a process name was specified in the filter, validate that here.
            $include = $include -and ($WindowsProcess.ProcessName -match $ProcessNamePattern)
        }
        if($ProcessNameExact -is [Array] -or (-not [String]::IsNullOrEmpty($ProcessNameExact)))
        {
            #if a process name was specified in the filter, validate that here.
            if ($ProcessNameExact -is [Array] )
            {
                $include = $include -and ($ProcessNameExact -contains $WindowsProcess.ProcessName)
            }
            else {
                $include = $include -and ($ProcessNameExact -eq $WindowsProcess.ProcessName)
            }
        }
        if ($ProcessId -and $ProcessId -ne 0)
        {
            # if a PID was specified in the filger, validate that here.
            $include = $include -and ($WindowsProcess.Id -eq $ProcessId)
        }
       
        if ($include)
        {
           $WindowsProcess
        }
    }
}

Start-Sleep -Seconds $pre_wait_delay
if ($state -eq "present" ) {
    #wait for a process to start
    $Processes = @()
    $attempts = -1
    Do {
        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout)
        {
            Fail-Json $result "timeout while waiting for $process_name to start.  waited $timeout seconds"
        }
       
        $Processes = Get-Process | Test-ProcessMatchesFilter -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id | Select-Object -Property Id, ProcessName, Owner
        Start-Sleep -Seconds $sleep
        $attempts ++
        $ProcessCount = $(if ($Processes -is [array]) { $Processess.count } else{ 1 })
    } While ($ProcessCount -lt $process_min_count)

    if ($attempts -gt 0)
    {
        $result.changed = $true
    }
    $result.matched_processess = $Processes
}
elseif ($state -eq "absent") {
    #wait for a process to stop
    $Processes = Get-Process |  Test-ProcessMatchesFilter -Owner $owner -ProcessNameExact $process_name_exact -ProcessNamePattern $process_name_pattern -ProcessId $process_id | Select-Object -Property ID, ProcessName, Owner
    $result.matched_processes = $Processes
    #Fail-Json $result "faildebug"
    $ProcessCount = $(if ($Processes -is [array]) { $Processes.count } elseif ($Processes){ 1 } else {0})
    if ($ProcessCount -gt 0 )
    {
        try { 
            Wait-Process -Id $($Processes | Select-Object -ExpandProperty Id) -Timeout $timeout -ErrorAction Stop
            $result.changed = $true
        }
        catch {
            Fail-Json $result "$($_.Exception.Message). timeout while waiting for $process_name to stop.  waited $timeout seconds"
        }
    }
    else{
        $result.changed = $false

    }
}
Start-Sleep -Seconds $post_wait_delay
$result.elapsed = ((Get-Date) - $module_start).TotalSeconds
Exit-Json $result