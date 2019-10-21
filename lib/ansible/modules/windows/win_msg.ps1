#!powershell

# Copyright: (c) 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#
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

if ($msg.Length -gt 255) {
    Fail-Json -obj $result -message "msg length must be less than 256 characters, current length: $($msg.Length)"
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
