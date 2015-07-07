#!powershell
# This file is part of Ansible
#
# Copyright 2015, Peter Mounce <public@neverrunwithscissors.com>
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

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

if ($params.name)
{
    $name = $params.name
}
else
{
    Fail-Json $result "missing required argument: name"
}
if ($params.state)
{
    $state = $params.state
}
else
{
    Fail-Json $result "missing required argument: state"
}
if ($params.enabled)
{
  $enabled = $params.enabled | ConvertTo-Bool
}
else
{
  $enabled = $true #default
}
if ($params.description)
{
  $description = $params.description
}
else
{
  $description = " "  #default
}
if ($params.execute)
{
  $execute = $params.execute
}
elseif ($state -eq "present")
{
  Fail-Json $result "missing required argument: execute"
}
if( $state -ne "present" -and $state -ne "absent") {
    Fail-Json $result "state must be present or absent"
}
if ($params.path)
{
  $path = "\{0}\" -f $params.path
}
else
{
  $path = "\"  #default
}
if ($params.frequency)
{
  $frequency = $params.frequency
}
elseif($state -eq "present")
{
  Fail-Json $result "missing required argument: frequency"
}
if ($params.time)
{
  $time = $params.time
}
elseif($state -eq "present")
{
  Fail-Json $result "missing required argument: time"
}
if ($params.daysOfWeek)
{
  $daysOfWeek = $params.daysOfWeek
}
elseif ($frequency -eq "weekly")
{
  Fail-Json $result "missing required argument: daysOfWeek"
}

try {
    $task = Get-ScheduledTask -TaskPath "$path" | Where-Object {$_.TaskName -eq "$name"}
    $measure = $task | measure
    if ($measure.count -eq 1 ) {
        $exists = $true
    }
    elseif ($measure.count -eq 0 -and $state -eq "absent" ){
        Set-Attr $result "msg" "Task does not exist"
        Exit-Json $result
    }
    elseif ($measure.count -eq 0){
        $exists = $false
    }
    else {
        # This should never occur
        Fail-Json $result "$measure.count scheduled tasks found"
    }
    Set-Attr $result "exists" "$exists"

    if ($frequency){
        if ($frequency -eq "daily") {
            $trigger =  New-ScheduledTaskTrigger -Daily -At $time
        }
        elseif ($frequency -eq "weekly"){
            $trigger =  New-ScheduledTaskTrigger -Weekly -At $time -DaysOfWeek $daysOfWeek
        }
        else {
            Fail-Json $result "frequency must be daily or weekly"
        }
    }

    if ($state -eq "absent" -and $exists -eq $true) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        $result.changed = $true
        Set-Attr $result "msg" "Deleted task $name"
        Exit-Json $result
    }
    elseif ($state -eq "absent" -and $exists -eq $false) {
        Set-Attr $result "msg" "Task $name does not exist"
        Exit-Json $result
    }

    if ($state -eq "present" -and $exists -eq $false){
        $action = New-ScheduledTaskAction -Execute $execute
        Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $name -Description $description -TaskPath $path
        $task = Get-ScheduledTask -TaskName $name
        Set-Attr $result "msg" "Added new task $name"
        $result.changed = $true
    }
    elseif($state -eq "present" -and $exists -eq $true) {
        if ($task.Description -eq $description -and $task.TaskName -eq $name -and $task.TaskPath -eq $path -and $task.Actions.Execute -eq $execute) {
            #No change in the task yet
            Set-Attr $result "msg" "No change in task $name"
        }
        else {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false
            $action = New-ScheduledTaskAction -Execute $execute
            Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $name -Description $description -TaskPath $path
            $task = Get-ScheduledTask -TaskName $name
            Set-Attr $result "msg" "Updated task $name"
            $result.changed = $true
        }
    }

    if ($state -eq "present" -and $enabled -eq $true -and $task.State -ne "Ready" ){
        $task | Enable-ScheduledTask
        Set-Attr $result "msg" "Enabled task $name"
        $result.changed = $true
    }
    elseif ($state -eq "present" -and $enabled -eq $false -and $task.State -ne "Disabled"){
        $task | Disable-ScheduledTask
        Set-Attr $result "msg" "Disabled task $name"
        $result.changed = $true
    }

    Exit-Json $result;
}
catch
{
  Fail-Json $result $_.Exception.Message
}
