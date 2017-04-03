#!powershell
# This file is part of Ansible

# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
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


$result = @{
    changed = $false
}

# get params
$params = Parse-Args $args -supports_check_mode $false

$profile = Get-AnsibleParam -obj $params -name "profile" -type "str" -failifempty $true
$wantedstatus = Get-AnsibleParam -obj $params -name "enabled" -type "str" -default $true

Try {

    # get current profile status

    $currentstatus = Get-NetFirewallProfile -name $profile | select -ExpandProperty Enabled

    # if the current status is the same as wanted status, then no change is required.
    if ($currentstatus -eq $wantedstatus)
    {
        $result.changed = $false;
        Exit-Json $result
    }
    # status needs to be changed..
    else {
        Set-NetFirewallProfile -name $profile -Enabled $wantedstatus
        $result.changed = $true;
    }
  }
Catch {
    Fail-Json $result "an error occurred when attempting to change firewall status for profile $profile $($_.Exception.Message)"
}

Exit-Json $result