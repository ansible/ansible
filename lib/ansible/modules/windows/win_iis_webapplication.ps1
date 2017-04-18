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

# Site
$site = Get-Attr $params "site" $FALSE;
If ($site -eq $FALSE) {
    Fail-Json (New-Object psobject) "missing required argument: site";
}

# State parameter
$state = Get-Attr $params "state" "present";
$state.ToString().ToLower();
If (($state -ne 'present') -and ($state -ne 'absent')) {
  Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
}

# Path parameter
$physical_path = Get-Attr $params "physical_path" $FALSE;

# Application Pool Parameter
$application_pool = Get-Attr $params "application_pool" $FALSE;


# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
  Import-Module WebAdministration
}

# Result
$result = New-Object psobject @{
  application = New-Object psobject
  changed = $false
};

# Application info
$application = Get-WebApplication -Site $site -Name $name

try {
  # Add application
  If(($state -eq 'present') -and (-not $application)) {
    If ($physical_path -eq $FALSE) {
      Fail-Json (New-Object psobject) "missing required arguments: physical_path"
    }
    If (-not (Test-Path $physical_path)) {
      Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
    }

    $application_parameters = New-Object psobject @{
      Site = $site
      Name = $name
      PhysicalPath = $physical_path
    };

    If ($application_pool) {
      $application_parameters.ApplicationPool = $application_pool
    }

    $application = New-WebApplication @application_parameters -Force
    $result.changed = $true

  }

  # Remove application
  if ($state -eq 'absent' -and $application) {
    $application = Remove-WebApplication -Site $site -Name $name
    $result.changed = $true
  }

  $application = Get-WebApplication -Site $site -Name $name
  If($application) {

    # Change Physical Path if needed
    if($physical_path) {
      If (-not (Test-Path $physical_path)) {
        Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
      }

      $app_folder = Get-Item $application.PhysicalPath
      $folder = Get-Item $physical_path
      If($folder.FullName -ne $app_folder.FullName) {
        Set-ItemProperty "IIS:\Sites\$($site)\$($name)" -name physicalPath -value $physical_path
        $result.changed = $true
      }
    }

    # Change Application Pool if needed
    if($application_pool) {
      If($application_pool -ne $application.applicationPool) {
        Set-ItemProperty "IIS:\Sites\$($site)\$($name)" -name applicationPool -value $application_pool
        $result.changed = $true
      }
    }
  }
} catch {
  Fail-Json $result $_.Exception.Message
}

# Result
$application = Get-WebApplication -Site $site -Name $name
$result.application = New-Object psobject @{
  PhysicalPath = $application.PhysicalPath
  ApplicationPool = $application.applicationPool
}

Exit-Json $result
