#!powershell
# This file is part of Ansible
#
# Copyright 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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
$state = Get-AnsibleParam -obj $params -name "state" -default "present" -validateSet "present","absent"
$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true
$level = Get-AnsibleParam -obj $params -name "level" -validateSet "machine","process","user" -failifempty $true
$value = Get-AnsibleParam -obj $params -name "value"

If ($level) {
    $level = $level.ToString().ToLower()
}

$before_value = [Environment]::GetEnvironmentVariable($name, $level)

$state = $state.ToString().ToLower()
if ($state -eq "present" ) {
   [Environment]::SetEnvironmentVariable($name, $value, $level)
} Elseif ($state -eq "absent") {
   [Environment]::SetEnvironmentVariable($name, $null, $level)
}

$after_value = [Environment]::GetEnvironmentVariable($name, $level)

$result = New-Object PSObject;
Set-Attr $result "changed" $false;
Set-Attr $result "name" $name;
Set-Attr $result "before_value" $before_value;
Set-Attr $result "value" $after_value;
Set-Attr $result "level" $level;
if ($before_value -ne $after_value) {
   Set-Attr $result "changed" $true;
}

Exit-Json $result;
