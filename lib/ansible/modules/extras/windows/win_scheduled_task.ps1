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
    $package = $params.name
}
else
{
    Fail-Json $result "missing required argument: name"
}
if ($params.state)
{
  $state = $params.state.ToString()
  if (($state -ne 'Enabled') -and ($state -ne 'Disabled'))
  {
    Fail-Json $result "state is '$state'; must be 'Enabled' or 'Disabled'"
  }
}
else
{
  $state = "Enabled"
}


try
{
  $tasks = Get-ScheduledTask -TaskPath $name
  $tasks_needing_changing |? { $_.State -ne $state }
  if ($tasks_needing_changing -eq $null)
  {
    if ($state -eq 'Disabled')
    {
      $tasks_needing_changing | Disable-ScheduledTask
    }
    elseif ($state -eq 'Enabled')
    {
      $tasks_needing_changing | Enable-ScheduledTask
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
