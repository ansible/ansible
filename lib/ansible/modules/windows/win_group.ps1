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

$result = New-Object PSObject;
Set-Attr $result "changed" $false;

If (-not $params.name.GetType) {
    Fail-Json $result "missing required arguments: name"
}

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne "present") -and ($state -ne "absent")) {
        Fail-Json $result "state is '$state'; must be 'present' or 'absent'"
    }
}
Elseif (-not $params.state) {
    $state = "present"
}

$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"
$group = $adsi.Children | Where-Object {$_.SchemaClassName -eq 'group' -and $_.Name -eq $params.name }

try {
    If ($state -eq "present") {
        If (-not $group) {
            $group = $adsi.Create("Group", $params.name)
            $group.SetInfo()

            Set-Attr $result "changed" $true
        }

        If ($params.description.GetType) {
            IF (-not $group.description -or $group.description -ne $params.description) {
                $group.description = $params.description
                $group.SetInfo()
                Set-Attr $result "changed" $true
            }
        }
    }
    ElseIf ($state -eq "absent" -and $group) {
        $adsi.delete("Group", $group.Name.Value)
        Set-Attr $result "changed" $true
    }
}
catch {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result
