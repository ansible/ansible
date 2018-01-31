#!powershell
# This file is part of Ansible
#
# Copyright 2014, Chris Hoffman <choffman@chathamfinancial.com>
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
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$description = Get-AnsibleParam -obj $params -name "description" -type "str"

$result = @{
    changed = $false
}

$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"
$group = $adsi.Children | Where-Object {$_.SchemaClassName -eq 'group' -and $_.Name -eq $name }

try {
    If ($state -eq "present") {
        If (-not $group) {
            If (-not $check_mode) {
                $group = $adsi.Create("Group", $name)
                $group.SetInfo()
            }

            $result.changed = $true
        }

        If ($null -ne $description) {
            IF (-not $group.description -or $group.description -ne $description) {
                $group.description = $description
                If (-not $check_mode) {
                    $group.SetInfo()
                }
                $result.changed = $true
            }
        }
    }
    ElseIf ($state -eq "absent" -and $group) {
        If (-not $check_mode) {
            $adsi.delete("Group", $group.Name.Value)
        }
        $result.changed = $true
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result
