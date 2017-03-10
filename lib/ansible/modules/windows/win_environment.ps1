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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$value = Get-AnsibleParam -obj $params -name "value" -type "str"
$level = Get-AnsibleParam -obj $params -name "level" -type "str" -validateSet "machine","user","process" -failifempty $true

$before_value = [Environment]::GetEnvironmentVariable($name, $level)

# When removing environment, set value to $null if set
if ($state -eq "absent" -and $value) {
    $value = $null
}

$result = @{
    before_value = $before_value
    changed = $false
    level = $level
    name = $name
    value = $value
}

if ($diff_support) {
    $result.diff = @{}
}

if ($state -eq "present" -and $before_value -ne $value) {
    if (-not $check_mode) {
        [Environment]::SetEnvironmentVariable($name, $value, $level)
    }
    $result.changed = $true

    if ($diff_support) {
        if ($before_value -eq $null) {
            $result.diff.prepared = @"
[$level]
+$NAME = $value
"@
        } else {
            $result.diff.prepared = @"
[$level]
-$NAME = $before_value
+$NAME = $value
"@
        }
    }

} elseif ($state -eq "absent" -and $before_value -ne $null) {
    if (-not $check_mode) {
        [Environment]::SetEnvironmentVariable($name, $null, $level)
    }
    $result.changed = $true

    if ($diff_support) {
        $result.diff.prepared = @"
[$level]
-$NAME = $before_value
"@
    }

}

Exit-Json $result
