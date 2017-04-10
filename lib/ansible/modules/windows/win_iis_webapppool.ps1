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
$params = Parse-Args $args

# Name parameter
$name = Get-AnsibleParam -obj $params -name "name" -type "string" -failifempty $true


# State parameter
$state = Get-AnsibleParam -obj $params -name "state" -default "present" -validateSet "started","restarted","stopped","absent"

# Attributes parameter - Pipe separated list of attributes where
# keys and values are separated by comma (paramA:valyeA|paramB:valueB)
$attributes = @{};
$attrs = Get-AnsibleParam -obj $params -name "attributes" -type "string" -failifempty $false
If ($attrs) {
  $attrs -split '\|' | foreach {
    $key, $value = $_ -split "\:"
    $attributes.Add($key, $value)
  }
}

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $NULL){
  Import-Module WebAdministration
  $web_admin_dll_path = Join-Path $env:SystemRoot system32\inetsrv\Microsoft.Web.Administration.dll 
  Add-Type -Path $web_admin_dll_path
  $t = [Type]"Microsoft.Web.Administration.ApplicationPool"
}

# Result
$result = @{
  changed = $FALSE
#  attributes = $attributes
}

$result.attributes = $attributes

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
      $newParameter = $_
      $currentParameter = Get-ItemProperty ("IIS:\AppPools\" + $name) $newParameter.Key
      $currentParamVal = ""
      try {
        $currentParamVal = $currentParameter
      } catch {
        $currentParamVal = $currentParameter.Value
      }
      if(-not $currentParamVal -or ($currentParamVal -as [String]) -ne $newParameter.Value) {
        Set-ItemProperty ("IIS:\AppPools\" + $name) $newParameter.Key $newParameter.Value
        $result.changed = $TRUE
      }
    }

    # Set run state
    if (($state -eq 'stopped') -and ($pool.State -eq 'Started')) {
      Stop-WebAppPool -Name $name -ErrorAction Stop
      $result.changed = $TRUE
    }
    if (($state -eq 'started') -and ($pool.State -eq 'Stopped')) {
      Start-WebAppPool -Name $name -ErrorAction Stop
      $result.changed = $TRUE
    }
    if ($state -eq 'restarted') {
     switch ($pool.State)
       { 
         'Stopped' { Start-WebAppPool -Name $name -ErrorAction Stop }
         default { Restart-WebAppPool -Name $name -ErrorAction Stop }
       }
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
    attributes =  @{}
  };

  $pool.Attributes | ForEach {
     # lookup name if enum
     if ($_.Schema.Type -eq 'enum') {
        $propertyName = $_.Name.Substring(0,1).ToUpper() + $_.Name.Substring(1)
        $enum = [Microsoft.Web.Administration.ApplicationPool].GetProperty($propertyName).PropertyType.FullName
        $enum_names = [Enum]::GetNames($enum)
        $result.info.attributes.Add($_.Name, $enum_names[$_.Value])
     } else {
        $result.info.attributes.Add($_.Name, $_.Value);
     }
  }

}

Exit-Json $result

