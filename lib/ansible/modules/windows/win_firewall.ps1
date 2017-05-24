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


# get params
$params = Parse-Args $args -supports_check_mode $false

$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "list" -default [ "Public", "Domain", "Private" ]
$wantedstate = Get-AnsibleParam -obj $params -name "state" -type "str" -failifempty $true -validateset 'enabled', 'disabled'

$result = @{
    changed = $false

}

Try {

  ForEach($profile in $profiles)

  {

      $currentstate = (Get-NetFirewallProfile -Name $profile).Enabled

      if ($wantedstate -eq 'enabled')
      {
        if ($currentstate -eq $false)
        {
            Set-NetFirewallProfile -name $profile -Enabled true
            $result.enabled = $true
            $result.changed = $true
        }
      }
      else
      {
        if ($currentstate -eq $true)
        {
           Set-NetFirewallProfile -name $profile -Enabled false
           $result.enabled = $false
           $result.changed = $true
        }

      }

  }
}
Catch {
    Fail-Json $result "an error occurred when attempting to change firewall status for profile $profile $($_.Exception.Message)"
}

Exit-Json $result