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

$name = Get-AnsibleParam $params -name "name" -failifempty $true
$state = Get-AnsibleParam $params "state" -default "present" -validateSet "present","absent"
$host_header = Get-AnsibleParam $params -name "host_header"
$protocol = Get-AnsibleParam $params -name "protocol"
$port = Get-AnsibleParam $params -name "port"
$ip = Get-AnsibleParam $params -name "ip"
$certificatehash = Get-AnsibleParam $params -name "certificate_hash" -default $false
$certificateStoreName = Get-AnsibleParam $params -name "certificate_store_name" -default "MY"

$binding_parameters = New-Object psobject @{
  Name = $name
};

If ($host_header) {
  $binding_parameters.HostHeader = $host_header
}

If ($protocol) {
  $binding_parameters.Protocol = $protocol
}

If ($port) {
  $binding_parameters.Port = $port
}

If ($ip) {
  $binding_parameters.IPAddress = $ip
}

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null){
  Import-Module WebAdministration
}

function Create-Binding-Info {
  return New-Object psobject @{
    "bindingInformation" = $args[0].bindingInformation
    "certificateHash" = $args[0].certificateHash
    "certificateStoreName" = $args[0].certificateStoreName
    "isDsMapperEnabled" = $args[0].isDsMapperEnabled
    "protocol" = $args[0].protocol
    "sslFlags" = $args[0].sslFlags
  }
}

# Result
$result = New-Object psobject @{
  changed = $false
  parameters = $binding_parameters
  matched = @()
  removed = @()
  added = @()
};

# Get bindings matching parameters
$curent_bindings = Get-WebBinding @binding_parameters
$curent_bindings | Foreach {
  $result.matched += Create-Binding-Info $_
}

try {
  # Add
  if (-not $curent_bindings -and $state -eq 'present') {
    New-WebBinding @binding_parameters -Force

    # Select certificat
    if($certificateHash -ne $FALSE) {

      $ip = $binding_parameters["IPAddress"]
      if((!$ip) -or ($ip -eq "*")) {
        $ip = "0.0.0.0"
      }

      $port = $binding_parameters["Port"]
      if(!$port) {
        $port = 443
      }

      $result.port = $port
      $result.ip = $ip

      Push-Location IIS:\SslBindings\
      Get-Item Cert:\LocalMachine\$certificateStoreName\$certificateHash | New-Item  "$($ip)!$($port)"
      Pop-Location
    }

    $result.added += Create-Binding-Info (Get-WebBinding @binding_parameters)
    $result.changed = $true
  }

  # Remove
  if ($curent_bindings -and $state -eq 'absent') {
    $curent_bindings | foreach {
      Remove-WebBinding -InputObject $_
      $result.removed += Create-Binding-Info $_
    }
    $result.changed = $true
  }


}
catch {
  Fail-Json $result $_.Exception.Message
}

Exit-Json $result
