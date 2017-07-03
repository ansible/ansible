#!powershell
# This file is part of Ansible

# Copyright 2017, Michael Eaton <meaton@iforium.com>
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
$firewall_profiles = @('Domain', 'Private', 'Public')

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "list" -default @("Domain", "Private", "Public")
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -failifempty $true -validateset 'disabled','enabled'

$result = @{
    changed = $false
    profiles = $profiles
    state = $state
}

if ($PSVersionTable.PSVersion -lt [Version]"5.0") {
    Fail-Json $result "win_firewall requires Windows Management Framework 5 or higher."
}

Try {

    ForEach ($profile in $firewall_profiles) {

        $currentstate = (Get-NetFirewallProfile -Name $profile).Enabled
        $result.$profile = @{
            enabled = ($currentstate -eq 1)
            considered = ($profiles -contains $profile)
            currentstate = $currentstate
        }

        if ($profiles -notcontains $profile) {
            continue
        }

        if ($state -eq 'enabled') {

            if ($currentstate -eq $false) {
                Set-NetFirewallProfile -name $profile -Enabled true -WhatIf:$check_mode
                $result.changed = $true
                $result.$profile.enabled = $true
            }

        } else {

            if ($currentstate -eq $true) {
                Set-NetFirewallProfile -name $profile -Enabled false -WhatIf:$check_mode
                $result.changed = $true
                $result.$profile.enabled = $false
            }

        }
    }
} Catch {
    Fail-Json $result "an error occurred when attempting to change firewall status for profile $profile $($_.Exception.Message)"
}

Exit-Json $result
