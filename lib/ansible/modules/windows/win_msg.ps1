#!powershell
# This file is part of Ansible
#
# Copyright 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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

$stopwatch = [system.diagnostics.stopwatch]::startNew()

$params = Parse-Args $args
$result = New-Object PSObject
Set-Attr $result "changed" $False
$to = Get-Attr -obj $params -name to -default "*" -failifempty $False -resultobj $result
$display_seconds = Get-Attr -obj $params -name display_seconds -default "10" -failifempty $False -resultobj $result
$wait = Get-Attr -obj $params -name wait -default $False -failifempty $False -resultobj $result
$msg = Get-Attr -obj $params -name msg -failifempty $True -resultobj $result

If($msg.Length -lt 1) {

    Fail-Json $result "msg was empty, please supply message text"
}

$msg_args = @($to, "/TIME:$display_seconds")

If ($wait) 
{
  $msg_args += "/W"
}

$msg_args += $msg
$ret = & msg.exe $msg_args 2>&1
Set-Attr $result "rc" $LASTEXITCODE
$endsend_at = Get-Date| Out-String
$stopwatch.Stop()
If ($LASTEXITCODE -eq 0) 
{
    Set-Attr $result "changed" $True
    Set-Attr $result "runtime_seconds" $stopwatch.Elapsed.TotalSeconds
    Set-Attr $result "display_seconds" $display_seconds
    Set-Attr $result "msg" $msg
    Set-Attr $result "sent_localtime" $endsend_at.Trim()
    Set-Attr $result "wait" $wait
} 
Else 
{
    Fail-Json $result "$ret"
}
  
Exit-Json $result

