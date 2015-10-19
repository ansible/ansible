#!powershell
# -*- coding: utf-8 -*-

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

# Application
$application = Get-Attr $params "application" $FALSE;

# State parameter
$state = Get-Attr $params "state" "present";
If (($state -ne 'present') -and ($state -ne 'absent')) {
  Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
}

# Path parameter
$physical_path = Get-Attr $params "physical_path" $FALSE;

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
  Import-Module WebAdministration
}

# Result
$result = New-Object psobject @{
  directory = New-Object psobject
  changed = $false
};

# Construct path
$directory_path = if($application) {
  "IIS:\Sites\$($site)\$($application)\$($name)"
} else {
  "IIS:\Sites\$($site)\$($name)"
}

# Directory info
$directory = if($application) {
  Get-WebVirtualDirectory -Site $site -Name $name -Application $application
} else {
  Get-WebVirtualDirectory -Site $site -Name $name
}

try {
  # Add directory
  If(($state -eq 'present') -and (-not $directory)) {
    If ($physical_path -eq $FALSE) {
      Fail-Json (New-Object psobject) "missing required arguments: physical_path"
    }
    If (-not (Test-Path $physical_path)) {
      Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
    }

    $directory_parameters = New-Object psobject @{
      Site = $site
      Name = $name
      PhysicalPath = $physical_path
    };

    If ($application) {
      $directory_parameters.Application = $application
    }

    $directory = New-WebVirtualDirectory @directory_parameters -Force
    $result.changed = $true
  }

  # Remove directory
  If ($state -eq 'absent' -and $directory) {
    Remove-Item $directory_path
    $result.changed = $true
  }

  $directory = Get-WebVirtualDirectory -Site $site -Name $name
  If($directory) {

    # Change Physical Path if needed
    if($physical_path) {
      If (-not (Test-Path $physical_path)) {
        Fail-Json (New-Object psobject) "specified folder must already exist: physical_path"
      }

      $vdir_folder = Get-Item $directory.PhysicalPath
      $folder = Get-Item $physical_path
      If($folder.FullName -ne $vdir_folder.FullName) {
        Set-ItemProperty $directory_path -name physicalPath -value $physical_path
        $result.changed = $true
      }
    }
  }
} catch {
  Fail-Json $result $_.Exception.Message
}

# Result
$directory = Get-WebVirtualDirectory -Site $site -Name $name
$result.directory = New-Object psobject @{
  PhysicalPath = $directory.PhysicalPath
}

Exit-Json $result
