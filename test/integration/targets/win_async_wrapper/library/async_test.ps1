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

$parsed_args = Parse-Args $args

$sleep_delay_sec = Get-AnsibleParam -obj $parsed_args -name "sleep_delay_sec" -type "int" -default 0
$fail_mode = Get-AnsibleParam -obj $parsed_args -name "fail_mode" -type "str" -default "success" -validateset "success","graceful","exception"

If($fail_mode -isnot [array]) {
    $fail_mode = @($fail_mode)
}

$result = @{
    changed = $true
    module_pid = $pid
    module_tempdir = $PSScriptRoot
}

If($sleep_delay_sec -gt 0) {
    Sleep -Seconds $sleep_delay_sec
    $result["slept_sec"] = $sleep_delay_sec
}

If($fail_mode -contains "leading_junk") {
    Write-Output "leading junk before module output"
}

If($fail_mode -contains "graceful") {
    Fail-Json $result "failed gracefully"
}

Try {

    If($fail_mode -contains "exception") {
        Throw "failing via exception"
    }

    Exit-Json $result
}
Finally
{
    If($fail_mode -contains "trailing_junk") {
        Write-Output "trailing junk after module output"
    }
}
