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

If (!($params.path))
{
    Fail-Json $result "missing required arguments: path"
}

if (!(test-path $params.path))
{
    Fail-Json $result "couldn't find a file at $($params.path)"
}


If ($params.extra_args)
{
    $extra_args = $params.extra_args;
}
Else
{
    $extra_args = ""
}

if ($params.MsiVersionString)
{
    $MsiVersionString = $params.MsiVersionString
}

if ($params.MsiName)
{
    $MsiName = $params.MsiName
}

if (($MsiVersionString) -and (!($MsiName)))
{
    #If msiversionstring is specified, we need msiname as well
    Fail-Json $result "missing required arguments: MsiName"
}


If (($params.creates) -and ($params.state -ne "absent"))
{
    If (Test-Path ($params.creates))
    {
        Exit-Json $result;
    }
}

if ($MsiName)
{
    $AlreadyInstalledMsi = Get-WmiObject -Query "Select * from win32_product" | where {$_.Name -eq $MsiName}
}
ElseIf (($MsiName) -and ($MsiVersionString))
{
    $AlreadyInstalledMsi = Get-WmiObject -Query "Select * from win32_product" | where {($_.Name -eq $MsiName) -and ($_.version -eq $MsiVersionString)}
}
Else
{
    if ($params.state -eq "absent")
    {
        #existing msi check not specify, assume msi does exist
        $AlreadyInstalledMsi = $true
    }
    if ($params.state -eq "present")
    {
        #existing msi check not specify, assume msi does exist
        $AlreadyInstalledMsi = $false
    }
}

if (($AlreadyInstalledMsi) -and ($params.state -eq "absent"))
{
    #Already installed, perform uninstall
    msiexec.exe /x $params.path /qb /l $logfile $extra_args;
}
Elseif((!$AlreadyInstalledMsi) -and ($params.state -eq "present"))
{
    #Not already installed, perform the install
    $logfile = [IO.Path]::GetTempFileName();
    msiexec.exe /i $params.path /qb /l $logfile $extra_args;
}
Else
{
    #Do nothing
    Exit-Json $result;
}

Set-Attr $result "changed" $true;

$logcontents = Get-Content $logfile;
Remove-Item $logfile;

Set-Attr $result "log" $logcontents;

Exit-Json $result;
