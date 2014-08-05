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


$msipath = get-attr -obj $params -name "path"
if ($msipath -eq $null)
{
    Fail-Json $result "missing required arguments: path"
}

if (!(test-path $params.path))
{
    Fail-Json $result "couldn't find a file at $msipath"
}

$extra_args = get-attr -obj $params -name "extra_args"
$MsiVersionString = get-attr -obj $params -name "msiversionString"
$State = get-attr -obj $params -name "state"

if ($state -eq $null)
{
    $State = "present"
}
Elseif (($state -ne "present") -and ($state -ne "absent"))
{
    Fail-Json $result "need to set state to absent or present"
}

$MsiName = get-attr -obj $params -name "MsiName"

if (($MsiVersionString) -and (!($MsiName)))
{
    #If msiversionstring is specified, we need msiname as well
    Fail-Json $result "missing required arguments: MsiName"
}


If (($params.creates) -and ($params.state -ne "absent"))
{
    If (Test-Path ($params.creates))
    {
        $exitreason = New-Object psobject @{
        name = "File specified in creates parameter already exists"
        }
        Set-Attr $result "exit_reason" $exitreason
        Exit-Json $result;
    }
}


If (($MsiName) -and ($MsiVersionString))
{
    $AlreadyInstalledMsi = Get-WmiObject -Query "Select * from win32_product" | where {($_.Name -eq $MsiName) -and ($_.version -eq $MsiVersionString)}
}
Elseif ($MsiName)
{
    $AlreadyInstalledMsi = Get-WmiObject -Query "Select * from win32_product" | where {$_.Name -eq $MsiName}
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

$logfile = [IO.Path]::GetTempFileName();

if (($AlreadyInstalledMsi) -and ($params.state -eq "absent"))
{
    #Already installed, perform uninstall
    $msiresult = Start-Process msiexec.exe -ArgumentList "/x $($params.path) /qn /log $logfile $extra_args" -Wait -PassThru
}
Elseif((!$AlreadyInstalledMsi) -and ($params.state -eq "present"))
{
    #Not already installed, perform the install
    $msiresult = Start-Process msiexec.exe -ArgumentList "/i $($params.path) /qn /log $logfile $extra_args" -Wait -PassThru
}
Elseif(($AlreadyInstalledMsi) -and ($params.state -eq "present"))
{
    #Do nothing
    $exitreason = New-Object psobject @{
        name = "state set to present, msi name and version specified already present"
        }
        Set-Attr $result "exit_reason" $exitreason
    Exit-Json $result;
}
Elseif((!$AlreadyInstalledMsi) -and ($params.state -eq "absent"))
{
    #Do nothing
    $exitreason = New-Object psobject @{
        name = "state set to absent, msi name and version specified already non-present"
        }
        Set-Attr $result "exit_reason" $exitreason
    Exit-Json $result;
}
Else
{
    $exitreason = New-Object psobject @{
        name = "I have no idea what just happened."
        }
        Set-Attr $result "exit_reason" $exitreason
    Exit-Json $result;
}

if (($msiresult) -and ($msiresult.ExitCode -ne 0))
{
    Fail-Json $result "msiexec failed with exit code $($msiresult.ExitCode)"
}

Set-Attr $result "changed" $true;

$logcontents = Get-Content $logfile;

Set-Attr $result "log" $logfile;

Exit-Json $result;
