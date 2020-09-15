#!powershell

# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

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
if ($null -eq (Get-Module "WebAdministration" -ErrorAction SilentlyContinue)) {
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
