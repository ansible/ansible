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
$state.ToString().ToLower();
If (($state -ne $FALSE) -and ($state -ne 'started') -and ($state -ne 'stopped') -and ($state -ne 'restarted') -and ($state -ne 'absent')) {
  Fail-Json (New-Object psobject) "state is '$state'; must be 'started', 'restarted', 'stopped' or 'absent'"
}

# Path parameter
$physical_path = Get-Attr $params "physical_path" $FALSE;

# Application Pool Parameter
$application_pool = Get-Attr $params "application_pool" $FALSE;

# Binding Parameters
$bind_port = Get-Attr $params "port" $FALSE;
$bind_ip = Get-Attr $params "ip" $FALSE;
$bind_hostname = Get-Attr $params "hostname" $FALSE;
$bind_ssl = Get-Attr $params "ssl" $FALSE;

# Custom site Parameters from string where properties
# are seperated by a pipe and property name/values by colon.
# Ex. "foo:1|bar:2"
$parameters = Get-Attr $params "parameters" $null;
if($parameters -ne $null) {
  $parameters = @($parameters -split '\|' | ForEach {
    return ,($_ -split "\:", 2);
  })
}


# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
  Import-Module WebAdministration
}

# Result
$result = New-Object psobject @{
  site = New-Object psobject
  changed = $false
};

# Site info
$site = Get-Website | Where { $_.Name -eq $name }

Try {
  # Add site
  If(($state -ne 'absent') -and (-not $site)) {
    If ($physical_path -eq $FALSE) {
      Fail-Json (New-Object psobject) "missing required arguments: physical_path"
    }
    ElseIf (-not (Test-Path $physical_path)) {
      Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
    }

    $site_parameters = New-Object psobject @{
      Name = $name
      PhysicalPath = $physical_path
    };

    If ($application_pool) {
      $site_parameters.ApplicationPool = $application_pool
    }

    If ($bind_port) {
      $site_parameters.Port = $bind_port
    }

    If ($bind_ip) {
      $site_parameters.IPAddress = $bind_ip
    }

    If ($bind_hostname) {
      $site_parameters.HostHeader = $bind_hostname
    }

    $site = New-Website @site_parameters -Force
    $result.changed = $true
  }

  # Remove site
  If ($state -eq 'absent' -and $site) {
    $site = Remove-Website -Name $name
    $result.changed = $true
  }

  $site = Get-Website | Where { $_.Name -eq $name }
  If($site) {
    # Change Physical Path if needed
    if($physical_path) {
      If (-not (Test-Path $physical_path)) {
        Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
      }

      $folder = Get-Item $physical_path
      If($folder.FullName -ne $site.PhysicalPath) {
        Set-ItemProperty "IIS:\Sites\$($site.Name)" -name physicalPath -value $folder.FullName
        $result.changed = $true
      }
    }

    # Change Application Pool if needed
    if($application_pool) {
      If($application_pool -ne $site.applicationPool) {
        Set-ItemProperty "IIS:\Sites\$($site.Name)" -name applicationPool -value $application_pool
        $result.changed = $true
      }
    }

    # Set properties
    if($parameters) {
      $parameters | foreach {
        $parameter_value = Get-ItemProperty "IIS:\Sites\$($site.Name)" $_[0]
        if((-not $parameter_value) -or ($parameter_value.Value -as [String]) -ne $_[1]) {
          Set-ItemProperty "IIS:\Sites\$($site.Name)" $_[0] $_[1]
          $result.changed = $true
        }
      }
    }

    # Set run state
    if (($state -eq 'stopped') -and ($site.State -eq 'Started'))
    {
      Stop-Website -Name $name -ErrorAction Stop
      $result.changed = $true
    }
    if ((($state -eq 'started') -and ($site.State -eq 'Stopped')) -or ($state -eq 'restarted'))
    {
      Start-Website -Name $name -ErrorAction Stop
      $result.changed = $true
    }
  }
}
Catch
{
  Fail-Json (New-Object psobject) $_.Exception.Message
}

$site = Get-Website | Where { $_.Name -eq $name }
$result.site = New-Object psobject @{
  Name = $site.Name
  ID = $site.ID
  State = $site.State
  PhysicalPath = $site.PhysicalPath
  ApplicationPool = $site.applicationPool
  Bindings = @($site.Bindings.Collection | ForEach-Object { $_.BindingInformation })
}


Exit-Json $result
