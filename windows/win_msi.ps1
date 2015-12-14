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

$params = Parse-Args $args;

$path = Get-Attr $params "path" -failifempty $true
$state = Get-Attr $params "state" "present"
$creates = Get-Attr $params "creates" $false
$extra_args = Get-Attr $params "extra_args" ""

$result = New-Object psobject @{
    changed = $false
};

If (($creates -ne $false) -and ($state -ne "absent") -and (Test-Path $creates))
{
    Exit-Json $result;
}

$logfile = [IO.Path]::GetTempFileName();
if ($state -eq "absent")
{
    msiexec.exe /x $path /qn /l $logfile $extra_args
}
Else
{
    msiexec.exe /i $path /qn /l $logfile $extra_args
}

Set-Attr $result "changed" $true;

$logcontents = Get-Content $logfile | Out-String;
Remove-Item $logfile;

Set-Attr $result "log" $logcontents;

Exit-Json $result;
