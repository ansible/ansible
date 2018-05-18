#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true

$process_name = Get-AnsibleParam -obj $params -name "process_name" -type "str" 
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

if ($process_name -and $process_id)
{
    Fail-json $result "process_id and process_name may not be used at the same time."
}
if (-not ($process_name -or $process_id -or $user))
{
    Fail-json $result "at least one of: process_name, process_id, or user must be supplied"
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
        [String]
        $ProcessName,
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
            #always add the owner to proces info so that it's reported back
            $WindowsProcess = $WindowsProcess | Select-Object -Property *,@{Name="Owner";Expression={$owners[$_.id.tostring()]}} 
        }
        if (-not [String]::IsNullOrEmpty($user) )
        {
            $include = $include -and ($WindowsProcess.Owner -eq $user)
        }
        if(-not [String]::IsNullOrEmpty($process_name))
        {
            $include = $include -and ($WindowsProcess.ProcessName -match $ProcessName)
        }
        if ($process_id -and $process_id -ne 0)
        {
            $include = $include -and ($WindowsProcess.Id -eq $ProcessId)
        }
       
        if ($include)
        {
           $WindowsProcess
        }
    }
}

if ($state -eq "present" )
{
    #wait for a process to start
    $Processes = @()
    $attempts = -1
    Do {
        if (((Get-Date) - $module_start).TotalSeconds -gt $timeout)
        {
            Fail-Json $result "timeout while waiting for $process_name to start.  waited $timeout seconds"
        }
       
        $Processes = Get-Process | Test-ProcessMatchesFilter -Owner $owner -ProcessName $process_name -ProcessId $process_id | Select-Object -Property Id, ProcessName, Owner
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
elseif ($state -eq "absent")
{
    #wait for a process to stop
    $Processes = Get-Process | Test-ProcessMatchesFilter -Owner $owner -ProcessName $process_name -ProcessId $process_id | Select-Object -Property ID, ProcessName, Owner
    $result.matched_processess = $Processes
    Fail-Json $result "faildebug"
    $ProcessCount = $(if ($Processes -is [array]) { $Processess.count } else{ 1 })
    if ($ProcessCount -gt 0 )
    {
        try { 
            Wait-Process -Id $($Processes | Select-Object -ExpandProperty ID) -Timeout $timeout -ErrorAction Stop
           
            $result.matched_processess = $Processes
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
$result.elapsed = ((Get-Date) - $module_start).TotalSeconds
Exit-Json $result