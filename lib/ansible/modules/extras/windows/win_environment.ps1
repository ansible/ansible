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
$state = Get-Attr $params "state" $null;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

If ($state) {
    $state = $state.ToString().ToLower()
    If (($state -ne 'present') -and ($state -ne 'absent') ) {
        Fail-Json $result "state is '$state'; must be 'present', or 'absent'"
    }
} else {
    $state = 'present'
}

If ($params.name)
{
    $name = $params.name
} else {
    Fail-Json $result "missing required argument: name"
}

$value = $params.value

If ($params.level) {
    $level = $params.level.ToString().ToLower()
    If (( $level -ne 'machine') -and ( $level -ne 'user' ) -and ( $level -ne 'process')) {
        Fail-Json $result "level is '$level'; must be 'machine', 'user', or 'process'"
    }
}

$before_value = [Environment]::GetEnvironmentVariable($name, $level)

if ($state -eq "present" ) {
   [Environment]::SetEnvironmentVariable($name, $value, $level)
} Elseif ($state -eq "absent") {
   [Environment]::SetEnvironmentVariable($name, $null, $level)
}

$after_value = [Environment]::GetEnvironmentVariable($name, $level)

Set-Attr $result "name" $name;
Set-Attr $result "before_value" $before_value;
Set-Attr $result "value" $after_value;
Set-Attr $result "level" $level;
if ($before_value -ne $after_value) {
   Set-Attr $result "changed" $true;
}

Exit-Json $result;
