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

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name"
}

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'started') -and ($state -ne 'stopped') -and ($state -ne 'restarted')) {
        Fail-Json $result "state is '$state'; must be 'started', 'stopped', or 'restarted'"
    }
}

If ($params.start_mode) {
    $startMode = $params.start_mode.ToString().ToLower()
    If (($startMode -ne 'auto') -and ($startMode -ne 'manual') -and ($startMode -ne 'disabled')) {
        Fail-Json $result "start mode is '$startMode'; must be 'auto', 'manual', or 'disabled'"
    }
}

$svcName = $params.name
$svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
If (-not $svc) {
    Fail-Json $result "Service '$svcName' not installed"
}
# Use service name instead of display name for remaining actions.
If ($svcName -ne $svc.ServiceName) {
    $svcName = $svc.ServiceName
}

Set-Attr $result "name" $svc.ServiceName
Set-Attr $result "display_name" $svc.DisplayName

$svcMode = Get-WmiObject -Class Win32_Service -Property StartMode -Filter "Name='$svcName'"
If ($startMode) {
    If ($svcMode.StartMode.ToLower() -ne $startMode) {
        Set-Service -Name $svcName -StartupType $startMode
        Set-Attr $result "changed" $true
        Set-Attr $result "start_mode" $startMode
    }
    Else {
        Set-Attr $result "start_mode" $svcMode.StartMode.ToLower()
    }
}
Else {
    Set-Attr $result "start_mode" $svcMode.StartMode.ToLower()
}

If ($state) {
    If ($state -eq "started" -and $svc.Status -ne "Running") {
        try {
            Start-Service -Name $svcName -ErrorAction Stop
        }
        catch {
            Fail-Json $result $_.Exception.Message
        }
        Set-Attr $result "changed" $true;
    }
    ElseIf ($state -eq "stopped" -and $svc.Status -ne "Stopped") {
        try {
            Stop-Service -Name $svcName -ErrorAction Stop
        }
        catch {
            Fail-Json $result $_.Exception.Message
        }
        Set-Attr $result "changed" $true;
    }
    ElseIf ($state -eq "restarted") {
        try {
            Restart-Service -Name $svcName -ErrorAction Stop
        }
        catch {
            Fail-Json $result $_.Exception.Message
        }
        Set-Attr $result "changed" $true;
    }
}
$svc.Refresh()
Set-Attr $result "state" $svc.Status.ToString().ToLower()

Exit-Json $result;
