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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$site = Get-AnsibleParam -obj $params -name "site" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$physical_path = Get-AnsibleParam -obj $params -name "physical_path" -type "str" -aliases "path"
$application_pool = Get-AnsibleParam -obj $params -name "application_pool" -type "str"

$result = @{
  application_pool = $application_pool
  changed = $false
  physical_path = $physical_path
}

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
  Import-Module WebAdministration
}

# Application info
$application = Get-WebApplication -Site $site -Name $name

try {
  # Add application
  if (($state -eq 'present') -and (-not $application)) {
    if (-not $physical_path) {
      Fail-Json $result "missing required arguments: path"
    }
    if (-not (Test-Path -Path $physical_path)) {
      Fail-Json $result "specified folder must already exist: path"
    }

    $application_parameters = @{
      Name = $name
      PhysicalPath = $physical_path
      Site = $site
    }

    if ($application_pool) {
      $application_parameters.ApplicationPool = $application_pool
    }

    if (-not $check_mode) {
        $application = New-WebApplication @application_parameters -Force
    }
    $result.changed = $true
  }

  # Remove application
  if ($state -eq 'absent' -and $application) {
    $application = Remove-WebApplication -Site $site -Name $name -WhatIf:$check_mode
    $result.changed = $true
  }

  $application = Get-WebApplication -Site $site -Name $name
  if ($application) {

    # Change Physical Path if needed
    if ($physical_path) {
      if (-not (Test-Path -Path $physical_path)) {
        Fail-Json $result "specified folder must already exist: path"
      }

      $app_folder = Get-Item $application.PhysicalPath
      $folder = Get-Item $physical_path
      if ($folder.FullName -ne $app_folder.FullName) {
        Set-ItemProperty "IIS:\Sites\$($site)\$($name)" -name physicalPath -value $physical_path -WhatIf:$check_mode
        $result.changed = $true
      }
    }

    # Change Application Pool if needed
    if ($application_pool) {
      if ($application_pool -ne $application.applicationPool) {
        Set-ItemProperty "IIS:\Sites\$($site)\$($name)" -name applicationPool -value $application_pool -WhatIf:$check_mode
        $result.changed = $true
      }
    }
  }
} catch {
  Fail-Json $result $_.Exception.Message
}

# When in check-mode or on removal, this may fail
$application = Get-WebApplication -Site $site -Name $name
if ($application) {
  $result.physical_path = $application.PhysicalPath
  $result.application_pool = $application.ApplicationPool
}

Exit-Json $result
