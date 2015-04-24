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
$valid_states = ($FALSE, 'present', 'absent');
If ($state -NotIn $valid_states) {
  Fail-Json $result "state is '$state'; must be $($valid_states)"
}

$binding_parameters = New-Object psobject @{
  Name = $name
};

If ($params.host_header) {
  $binding_parameters.HostHeader = $params.host_header
}

If ($params.protocol) {
  $binding_parameters.Protocol = $params.protocol
}

If ($params.port) {
  $binding_parameters.Port = $params.port
}

If ($params.ip) {
  $binding_parameters.IPAddress = $params.ip
}

$certificateHash = Get-Attr $params "certificate_hash" $FALSE;
$certificateStoreName = Get-Attr $params "certificate_store_name" "MY";

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

      $ip = $binding_parameters.IPAddress
      if((!$ip) -or ($ip -eq "*")) {
        $ip = "0.0.0.0"
      }

      $port = $binding_parameters.Port
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
