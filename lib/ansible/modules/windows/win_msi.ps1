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

# TODO: Add check-mode support

$params = Parse-Args $args

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$extra_args = Get-AnsibleParam -obj $params -name "extra_args" -type "str" -default ""
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $false

$result = @{
    changed = $false
}

if (($creates -ne $null) -and ($state -ne "absent") -and (Test-Path $creates)) {
    Exit-Json $result
}

if (-not (Test-Path $path)) {
	Fail-Json $result "Cannot find $path."
}

$logfile = [IO.Path]::GetTempFileName()
if ($state -eq "absent") {

    if ($wait) {
        Start-Process -FilePath msiexec.exe -ArgumentList "/x `"$path`" /qn /l $logfile $extra_args" -Verb Runas -Wait
    } else {
        Start-Process -FilePath msiexec.exe -ArgumentList "/x `"$path`" /qn /l $logfile $extra_args" -Verb Runas
    }

} else {

    if ($wait) {
        Start-Process -FilePath msiexec.exe -ArgumentList "/i `"$path`" /qn /l $logfile $extra_args" -Verb Runas -Wait
    } else {
        Start-Process -FilePath msiexec.exe -ArgumentList "/i `"$path`" /qn /l $logfile $extra_args" -Verb Runas
    }

}

$result.changed = $true
$result.log = Get-Content $logfile | Out-String
Remove-Item $logfile

Exit-Json $result