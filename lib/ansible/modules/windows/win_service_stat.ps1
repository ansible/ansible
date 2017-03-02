#!powershell
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

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name 'name' -type 'str' -failifempty $true

$result = @{
    changed = $false
}

$svc = Get-Service -Name $name -ErrorAction SilentlyContinue
if ($svc) {
    $wmi_svc = Get-WmiObject Win32_Service | Where-Object { $_.Name -eq $svc.Name }

    # Delayed start_mode is in reality Automatic (Delayed), need to check reg key for type
    $delayed_key = "HKLM:\System\CurrentControlSet\Services\$name"
    try {
        $delayed = ConvertTo-Bool ((Get-ItemProperty -Path $delayed_key).DelayedAutostart)
    } catch {
        $delayed = $false
    }
    $actual_start_mode = $wmi_svc.StartMode.ToString().ToLower() 
    if ($delayed -and $actual_start_mode -eq 'auto') {
        $actual_start_mode = 'delayed'
    }

    $existing_depenencies = @()
    $existing_depended_by = @()
    if ($svc.ServicesDependedOn.Count -gt 0) {
        foreach ($dependency in $svc.ServicesDependedOn.Name) {
            $existing_depenencies += $dependency
        }
    }
    if ($svc.DependentServices.Count -gt 0) {
        foreach ($dependency in $svc.DependentServices.Name) {
            $existing_depended_by += $dependency
        }
    }

    $description = $wmi_svc.Description
    if ($description -eq $null) {
        $description = ""
    }

    $result.exists = $true
    $result.name = $svc.Name
    $result.display_name = $svc.DisplayName
    $result.state = $svc.Status.ToString().ToLower()
    $result.start_mode = $actual_start_mode
    $result.path = $wmi_svc.PathName
    $result.description = $description
    $result.username = $wmi_svc.startname
    $result.desktop_interact = (ConvertTo-Bool $wmi_svc.DesktopInteract)
    $result.dependencies = $existing_depenencies
    $result.depended_by = $existing_depended_by
} else {
    $result.exists = $false
}

Exit-Json $result
