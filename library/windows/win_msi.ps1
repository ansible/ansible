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

$result = New-Object psobject;
Set-Attr $result "changed" $false;

If (-not $params.path.GetType)
{
    Fail-Json $result "missing required arguments: path"
}

$extra_args = ""
If ($params.extra_args.GetType)
{
    $extra_args = $params.extra_args;
}

If ($params.creates.GetType -and $params.state.GetType -and $params.state -ne "absent")
{
    If (Test-File $creates)
    {
        Exit-Json $result;
    }
}

$logfile = [IO.Path]::GetTempFileName();
if ($params.state.GetType -and $params.state -eq "absent")
{
    msiexec.exe /x $params.path /qb /l $logfile $extra_args;
}
Else
{
    msiexec.exe /i $params.path /qb /l $logfile $extra_args;
}

Set-Attr $result "changed" $true;

$logcontents = Get-Content $logfile;
Remove-Item $logfile;

Set-Attr $result "log" $logcontents;

Exit-Json $result;
