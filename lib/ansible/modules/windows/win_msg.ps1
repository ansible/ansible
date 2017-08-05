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

$display_seconds = Get-AnsibleParam -obj $params -name "display_seconds" -type "int" -default "10"
$msg = Get-AnsibleParam -obj $params -name "msg" -type "str" -default "Hello world!"
$to = Get-AnsibleParam -obj $params -name "to" -type "str" -default "*"
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $false

$result = @{
    changed = $false
    display_seconds = $display_seconds
    msg = $msg
    wait = $wait
}

$msg_args = @($to, "/TIME:$display_seconds")

if ($wait) {
    $msg_args += "/W"
}

$msg_args += $msg
if (-not $check_mode) {
    $output = & msg.exe $msg_args 2>&1
    $result.rc = $LASTEXITCODE
}

$endsend_at = Get-Date| Out-String
$stopwatch.Stop()

$result.changed = $true
$result.runtime_seconds = $stopwatch.Elapsed.TotalSeconds
$result.sent_localtime = $endsend_at.Trim()

if ($result.rc -ne 0 ) {
    Fail-Json -obj $result -message "$output"
}
  
Exit-Json $result
