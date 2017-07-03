#!powershell
# (c) 2014, Matt Martz <matt@sivel.net>, and others
#
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

$params = Parse-Args $args  -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"
$extra_args = Get-AnsibleParam -obj $params -name "extra_args" -type "str" -default ""
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $false

$result = @{
    changed = $false
}

if (-not (Test-Path -Path $path)) {
    Fail-Json $result "The MSI file ($path) was not found."
}

if ($creates -and (Test-Path -Path $creates)) {
    Exit-Json $result "The 'creates' file or directory ($creates) already exists."
}

if ($removes -and -not (Test-Path -Path $removes)) {
    Exit-Json $result "The 'removes' file or directory ($removes) does not exist."
}

if (-not $check_mode) {

    $logfile = [IO.Path]::GetTempFileName()
    if ($state -eq "absent") {
        Start-Process -FilePath msiexec.exe -ArgumentList "/x `"$path`" /qn /log $logfile $extra_args" -Verb Runas -Wait:$wait
    } else {
        Start-Process -FilePath msiexec.exe -ArgumentList "/i `"$path`" /qn /log $logfile $extra_args" -Verb Runas -Wait:$wait
    }
    $result.log = Get-Content $logfile | Out-String
    Remove-Item $logfile

}

$result.changed = $true

Exit-Json $result
