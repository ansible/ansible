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

$params = Parse-Args $args;

$destip = Get-Attr $params "destination_ip" -failifempty $true;
$mask = Get-Attr $params "subnet_mask" -failifempty $true;
$gateway = Get-Attr $params "gateway" -failifempty $true;
$metric = Get-Attr $params "metric" -default 1;
$state = Get-Attr $params "state" -default "present" -validateSet "present","absent";
$result = New-Object PSObject @{"changed" = $false; "output" = ""};

Function Test-SubnetMask {
    Param (
        [Parameter(Mandatory=$True)]
        [string]$SubnetMask
    )
    # Validate and convert Subnet Mask to prefix Lenght.
    Switch ($SubnetMask) {
      "255.255.255.255" {$true}
      "255.255.255.254" {$true}
      "255.255.255.252" {$true}
      "255.255.255.248" {$true}
      "255.255.255.240" {$true}
      "255.255.255.224" {$true}
      "255.255.255.192" {$true}
      "255.255.255.128" {$true}
      "255.255.255.0" {$true}
      "255.255.254.0" {$true}
      "255.255.252.0" {$true}
      "255.255.248.0" {$true}
      "255.255.240.0" {$true}
      "255.255.224.0" {$true}
      "255.255.192.0" {$true}
      "255.255.128.0" {$true}
      "255.255.0.0" {$true}
      "255.254.0.0" {$true}
      "255.252.0.0" {$true}
      "255.248.0.0" {$true}
      "255.240.0.0" {$true}
      "255.224.0.0" {$true}
      "255.192.0.0" {$true}
      "255.128.0.0" {$true}
      "255.0.0.0" {$true}
      "254.0.0.0" {$true}
      "252.0.0.0" {$true}
      "248.0.0.0" {$true}
      "240.0.0.0" {$true}
      "224.0.0.0" {$true}
      "192.0.0.0" {$true}
      "128.0.0.0" {$true}
      "0.0.0.0" {$true}
      default {$ErrorMessage = "$SubnetMask is not a valid subnet mask"; 
               Fail-Json $result $ErrorMessage}
      }
}

Function Test-IpAddress {
    Param (
        [string]$IpAddress
        )

    # Test if is a valid ip address
    try {
        [ipaddress]$IpAddress|Out-Null
        return $true
    }
    catch {
        Fail-Json $result $($_.Exception.Message)
    }
    
}


Function Add-Route {
  Param (
    [Parameter(Mandatory=$True)]
    [string]$DestinationIP,
    [Parameter(Mandatory=$True)]
    [string]$SubnetMask,
    [Parameter(Mandatory=$True)]
    [string]$Gateway,
    [Parameter(Mandatory=$True)]
    [int]$Metric
    )

    
  # Check if the static route is already present
  $route = Get-CimInstance win32_ip4PersistedrouteTable -Filter "Destination = '$($DestinationIP)'"
  if (!($route)){
    try {
      # Add a new static route
      Start-Process "route.exe" -ArgumentList "ADD $DestinationIp MASK $SubnetMask $Gateway METRIC $metric -p" -NoNewWindow -Wait
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
    [Parameter(Mandatory=$True)]
    [string]$DestinationIP
    )
  $route = Get-CimInstance win32_ip4PersistedrouteTable -Filter "Destination = '$($DestinationIP)'"
  if ($route){
    try {
      # remove the static route
      Start-Process "route.exe" -ArgumentList "DELETE $DestinationIp" -NoNewWindow -Wait
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


# Test if there are invalid ip address or subnet masks
Test-IpAddress -IpAddress $destip
Test-IpAddress -IpAddress $gateway
Test-SubnetMask -SubnetMask $mask


if ($state -eq "present"){

  Add-Route -DestinationIP $destip -SubnetMask $mask -Gateway $gateway -Metric $metric

}
else {

  Remove-Route -DestinationIP $destip

}

Exit-Json $result