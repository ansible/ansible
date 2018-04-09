#!powershell
# This file is part of Ansible
#
# Copyright 2016, Daniele Lazzari <lazzari@mailup.com>
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

# win_route (Add or remove a network static route)

$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false
$dest = Get-AnsibleParam -obj $params -name "destination" -type "str" -failifempty $true
$gateway = Get-AnsibleParam -obj $params -name "gateway" -type "str"
$metric = Get-AnsibleParam -obj $params -name "metric" -type "int" -default 1
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateSet "present","absent"
$result = @{
             "changed" = $false
             "output" = ""
           }

Function Add-Route {
  Param (
    [Parameter(Mandatory=$true)]
    [string]$Destination,
    [Parameter(Mandatory=$true)]
    [string]$Gateway,
    [Parameter(Mandatory=$true)]
    [int]$Metric,
    [Parameter(Mandatory=$true)]
    [bool]$CheckMode
    )


  $IpAddress = $Destination.split('/')[0]

  # Check if the static route is already present
  $Route = Get-CimInstance win32_ip4PersistedrouteTable -Filter "Destination = '$($IpAddress)'"
  if (!($Route)){
    try {
      # Find Interface Index
      $InterfaceIndex = Find-NetRoute -RemoteIPAddress $IpAddress | Select -First 1 -ExpandProperty InterfaceIndex

      # Add network route
      New-NetRoute -DestinationPrefix $Destination -NextHop $Gateway -InterfaceIndex $InterfaceIndex -RouteMetric $Metric -ErrorAction Stop -WhatIf:$CheckMode|out-null 
      $result.changed = $true
      $result.output = "Route added"
      
    }
    catch {
      $ErrorMessage = $_.Exception.Message
      Fail-Json $result $ErrorMessage
    }
  }
  else {
    $result.output = "Static route already exists"
  }
  
}

Function Remove-Route {
  Param (
    [Parameter(Mandatory=$true)]
    [string]$Destination,
    [bool]$CheckMode
    )
  $IpAddress = $Destination.split('/')[0]
  $Route = Get-CimInstance win32_ip4PersistedrouteTable -Filter "Destination = '$($IpAddress)'"
  if ($Route){
    try {

      Remove-NetRoute -DestinationPrefix $Destination -Confirm:$false -ErrorAction Stop -WhatIf:$CheckMode 
      $result.changed = $true
      $result.output = "Route removed"
    }
    catch {
      $ErrorMessage = $_.Exception.Message
      Fail-Json $result $ErrorMessage
    }
  }
  else {
    $result.output = "No route to remove"
  }

}

# Set gateway if null 
if(!($gateway)){
  $gateway = "0.0.0.0"
}


if ($state -eq "present"){

  Add-Route -Destination $dest -Gateway $gateway -Metric $metric -CheckMode $check_mode

}
else {

  Remove-Route -Destination $dest -CheckMode $check_mode

}

Exit-Json $result