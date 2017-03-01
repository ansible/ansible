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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$display_seconds = Get-AnsibleParam -obj $params -name display_seconds -default "10" -failifempty $False -resultobj $result
$msg = Get-AnsibleParam -obj $params -name msg -default "Hello world!" -resultobj $result
$to = Get-AnsibleParam -obj $params -name to -default "*" -failifempty $False -resultobj $result
$wait = Get-AnsibleParam -obj $params -name wait -default $False -failifempty $False -resultobj $result

$result = @{
    changed = $false
}


$msg_args = @($to, "/TIME:$display_seconds")

If ($wait) {
  $msg_args += "/W"
}

$msg_args += $msg
if (-not $check_mode) {
  $ret = & msg.exe $msg_args 2>&1
  $result.rc = $LASTEXITCODE
}

$endsend_at = Get-Date| Out-String
$stopwatch.Stop()

$result.changed = $True
$result.display_seconds = $display_seconds
$result.msg = $msg
$result.runtime_seconds = $stopwatch.Elapsed.TotalSeconds
$result.sent_localtime = $endsend_at.Trim()
$result.wait = $wait

If (-not $result.rc -eq 0 ) {
    Fail-Json $result "$ret"
}
  
Exit-Json $result
