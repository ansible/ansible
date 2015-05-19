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
if ($params.enabled)
{
  $enabled = $params.enabled | ConvertTo-Bool
}
else
{
  $enabled = $true
}
$target_state = @{$true = "Enabled"; $false="Disabled"}[$enabled]

try
{
  $tasks = Get-ScheduledTask -TaskPath $name
  $tasks_needing_changing = $tasks |? { $_.State -ne $target_state }
  if (-not($tasks_needing_changing -eq $null))
  {
    if ($enabled)
    {
      $tasks_needing_changing | Enable-ScheduledTask
    }
    else
    {
      $tasks_needing_changing | Disable-ScheduledTask
    }
    Set-Attr $result "tasks_changed" ($tasks_needing_changing | foreach { $_.TaskPath + $_.TaskName })
    $result.changed = $true
  }
  else
  {
    Set-Attr $result "tasks_changed" @()
    $result.changed = $false
  }

  Exit-Json $result;
}
catch
{
  Fail-Json $result $_.Exception.Message
}
