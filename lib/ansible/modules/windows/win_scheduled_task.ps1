#!powershell
# This file is part of Ansible
#
# Copyright 2015, Peter Mounce <public@neverrunwithscissors.com>
# Michael Perzel <michaelperzel@gmail.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

$ErrorActionPreference = "Stop"

# WANT_JSON
# POWERSHELL_COMMON

$result = @{
    changed = $false
}

function Invoke-TaskPathCheck {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param($Path, [Switch]$Remove)

    $pathResults = @{
        PathExists = $null
        RemovedPath = $false
    }

    if ($path -ne "\") {
        $trimmedPath = $Path.TrimEnd("\")
    }
    else {
        $trimmedPath = $Path
    }

    $scheduleObject = New-Object -ComObject Schedule.Service
    $scheduleObject.Connect()

    try {
        $targetFolder = $scheduleObject.GetFolder($trimmedPath)
        $pathResults.PathExists = $true
    }
    catch {
        $pathResults.PathExists = $false
    }

    if ($Remove -and $pathResults.PathExists) {
        $childFolders = $targetFolder.GetFolders($null)
        $childTasks = $targetFolder.GetTasks($null)

        if ($childFolders.Count -eq 0 -and $childTasks.Count -eq 0) {
            if ($PSCmdlet.ShouldProcess($trimmedPath, "Remove task path")) {
                $rootFolder = $scheduleObject.GetFolder("\")
                $rootFolder.DeleteFolder($trimmedPath, $null)
            }
            $pathResults.RemovedPath = $true
        }
    }

    return $pathResults
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$arguments = Get-AnsibleParam -obj $params -name "arguments" -type "str" -aliases "argument"
$description = Get-AnsibleParam -obj $params -name "description" -type "str" -default "No description."
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool" -default $true
$path = Get-AnsibleParam -obj $params -name "path" -type "str" -default '\'

# Required vars
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"

# Vars conditionally required
$present = $state -eq "present"
$executable = Get-AnsibleParam -obj $params -name "executable" -type "str" -aliases "execute" -failifempty $present
$frequency = Get-AnsibleParam -obj $params -name "frequency" -type "str" -validateset "once","daily","weekly" -failifempty $present
$time = Get-AnsibleParam -obj $params -name "time" -type "str" -failifempty $present

$user = Get-AnsibleParam -obj $params -name "user" -default "$env:USERDOMAIN\$env:USERNAME" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$runlevel = Get-AnsibleParam -obj $params -name "runlevel" -default "limited" -type "str" -validateset "limited", "highest"
$store_password = Get-AnsibleParam -obj $params -name "store_password" -default $true -type "bool"

$weekly = $frequency -eq "weekly"
$days_of_week = Get-AnsibleParam -obj $params -name "days_of_week" -type "str" -failifempty $weekly


try {
    $task = Get-ScheduledTask | Where-Object {$_.TaskName -eq $name -and $_.TaskPath -eq $path}

    # Correlate task state to enable variable, used to calculate if state needs to be changed
    $taskState = if ($task) { $task.State } else { $null }
    if ($taskState -eq "Ready"){
        $taskState = $true
    }
    elseif($taskState -eq "Disabled"){
        $taskState = $false
    }
    else
    {
        $taskState = $null
    }

    $measure = $task | measure
    if ($measure.count -eq 1 ) {
        $exists = $true
    }
    elseif ( ($measure.count -eq 0) -and ($state -eq "absent") ){
        # Nothing to do
        $result.exists = $false
        $result.msg = "Task does not exist"

        Exit-Json $result
    }
    elseif ($measure.count -eq 0){
        $exists = $false
    }
    else {
        # This should never occur
        Fail-Json $result "$($measure.count) scheduled tasks found"
    }

    $result.exists = $exists

    if ($frequency){
        if ($frequency -eq "once") {
            $trigger = New-ScheduledTaskTrigger -Once -At $time
        }
        elseif ($frequency -eq "daily") {
            $trigger = New-ScheduledTaskTrigger -Daily -At $time
        }
        elseif ($frequency -eq "weekly"){
            $trigger = New-ScheduledTaskTrigger -Weekly -At $time -DaysOfWeek $days_of_week
        }
        else {
            Fail-Json $result "frequency must be daily or weekly"
        }
    }

    if ( ($state -eq "absent") -and ($exists) ) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false -WhatIf:$check_mode
        $result.changed = $true
        $result.msg = "Deleted task $name"

        # Remove task path if it exists
        $pathResults = Invoke-TaskPathCheck -Path $path -Remove -WhatIf:$check_mode

        if ($pathResults.RemovedPath) {
            $result.msg += " and task path $path removed"
        }

        Exit-Json $result
    }
    elseif ( ($state -eq "absent") -and (-not $exists) ) {
        $result.msg = "Task $name does not exist"
        Exit-Json $result
    }

    # Handle RunAs/RunLevel options for the task

    if ($store_password) {
        # Specify direct credential and run-level values to add to Register-ScheduledTask
        $registerRunOptionParams = @{
            User = $user
            RunLevel = $runlevel
        }
        if ($password) {
            $registerRunOptionParams.Password = $password
        }
    }
    else {
        # Create a ScheduledTaskPrincipal for the task to run under
        $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType S4U -RunLevel $runlevel -Id Author
        $registerRunOptionParams = @{Principal = $principal}
    }

    if ($enabled){
        $settings = New-ScheduledTaskSettingsSet
    }
    else {
        $settings = New-ScheduledTaskSettingsSet -Disable
    }

    if ($arguments) {
        $action = New-ScheduledTaskAction -Execute $executable -Argument $arguments
    }
    else {
        $action = New-ScheduledTaskAction -Execute $executable
    }

    if ( ($state -eq "present") -and (-not $exists) ){
        # Check task path prior to registering
        $pathResults = Invoke-TaskPathCheck -Path $path

        if (-not $check_mode) {
            Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $name -Description $description -TaskPath $path -Settings $settings @registerRunOptionParams
        }

        $result.changed = $true
        $result.msg = "Added new task $name"

        if (!$pathResults.PathExists) {
            $result.msg += " and task path $path created"
        }
    }
    elseif( ($state -eq "present") -and ($exists) ) {
        # Check task path prior to registering
        $pathResults = Invoke-TaskPathCheck -Path $path

        if ((!$store_password -and $task.Principal.LogonType -in @("S4U", "ServiceAccount")) -or ($store_password -and $task.Principal.LogonType -notin @("S4U", "Password") -and !$password)) {
            $passwordStoreConsistent = $true
        }
        else {
            $passwordStoreConsistent = $false
        }

        if ($task.Description -eq $description -and $task.TaskName -eq $name -and $task.TaskPath -eq $path -and $task.Actions.Execute -eq $executable -and
        $taskState -eq $enabled -and $task.Principal.UserId -eq $user -and $task.Principal.RunLevel -eq $runlevel -and $passwordStoreConsistent) {
            # No change in the task
            $result.msg = "No change in task $name"
        }
        else {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false -WhatIf:$check_mode

            if (-not $check_mode) {
                $oldPathResults = Invoke-TaskPathCheck -Path $task.TaskPath -Remove
                Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $name -Description $description -TaskPath $path -Settings $settings @registerRunOptionParams
            }
            $result.changed = $true
            $result.msg = "Updated task $name"

            if (!$pathResults.PathExists) {
                $result.msg += " and task path $path created"
            }
        }
    }

    Exit-Json $result
}
catch
{
  Fail-Json $result $_.Exception.Message
}
