#!powershell

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
#
# This file is part of Ansible
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


# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

# Name parameter
$name = Get-Attr $params "name" $FALSE;
If ($name -eq $FALSE) {
    Fail-Json (New-Object psobject) "missing required argument: name";
}

# State parameter
$state = Get-Attr $params "state" $FALSE;
$valid_states = ('started', 'restarted', 'stopped', 'absent');
If (($state -Ne $FALSE) -And ($state -NotIn $valid_states)) {
  Fail-Json $result "state is '$state'; must be $($valid_states)"
}

# Attributes parameter - Pipe separated list of attributes where
# keys and values are separated by comma (paramA:valyeA|paramB:valueB)
$attributes = @{};
If (Get-Member -InputObject $params -Name attributes) {
  $params.attributes -split '\|' | foreach {
    $key, $value = $_ -split "\:";
    $attributes.Add($key, $value);
  }
}

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $NULL){
  Import-Module WebAdministration
}

# Result
$result = New-Object psobject @{
  changed = $FALSE
  attributes = $attributes
};

# Get pool
$pool = Get-Item IIS:\AppPools\$name

try {
  # Add
  if (-not $pool -and $state -in ('started', 'stopped', 'restarted')) {
    New-WebAppPool $name
    $result.changed = $TRUE
  }

  # Remove
  if ($pool -and $state -eq 'absent') {
    Remove-WebAppPool $name
    $result.changed = $TRUE
  }

  $pool = Get-Item IIS:\AppPools\$name
  if($pool) {
    # Set properties
    $attributes.GetEnumerator() | foreach {
      $newParameter = $_;
      $currentParameter = Get-ItemProperty ("IIS:\AppPools\" + $name) $newParameter.Key
      if(-not $currentParameter -or ($currentParameter.Value -as [String]) -ne $newParameter.Value) {
        Set-ItemProperty ("IIS:\AppPools\" + $name) $newParameter.Key $newParameter.Value
        $result.changed = $TRUE
      }
    }

    # Set run state
    if (($state -eq 'stopped') -and ($pool.State -eq 'Started')) {
      Stop-WebAppPool -Name $name -ErrorAction Stop
      $result.changed = $TRUE
    }
    if ((($state -eq 'started') -and ($pool.State -eq 'Stopped')) -or ($state -eq 'restarted')) {
      Start-WebAppPool -Name $name -ErrorAction Stop
      $result.changed = $TRUE
    }
  }
} catch {
  Fail-Json $result $_.Exception.Message
}

# Result
$pool = Get-Item IIS:\AppPools\$name
if ($pool)
{
  $result.info = @{
    name = $pool.Name
    state = $pool.State
    attributes =  New-Object psobject @{}
  };
  
  $pool.Attributes | ForEach { $result.info.attributes.Add($_.Name, $_.Value)};
}

Exit-Json $result
