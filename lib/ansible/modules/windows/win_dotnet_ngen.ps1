#!powershell

# Copyright: (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$result = @{
    changed = $false
}

Function Invoke-Ngen($architecture="") {
    $cmd = "$($env:windir)\Microsoft.NET\Framework$($architecture)\v4.0.30319\ngen.exe"

    if (Test-Path -LiteralPath $cmd) {
        $arguments = "update /force"
        if ($check_mode) {
            $ngen_result = @{
                rc = 0
                stdout = "check mode output for $cmd $arguments"
            }
        } else {
            try {
                $ngen_result = Run-Command -command "$cmd $arguments"
            } catch {
                Fail-Json -obj $result -message "failed to execute '$cmd $arguments': $($_.Exception.Message)"
            }
        }
        $result."dotnet_ngen$($architecture)_update_exit_code" = $ngen_result.rc
        $result."dotnet_ngen$($architecture)_update_output" = $ngen_result.stdout

        $arguments = "executeQueuedItems"
        if ($check_mode) {
            $executed_queued_items = @{
                rc = 0
                stdout = "check mode output for $cmd $arguments"
            }
        } else {
            try {
                $executed_queued_items = Run-Command -command "$cmd $arguments"
            } catch {
                Fail-Json -obj $result -message "failed to execute '$cmd $arguments': $($_.Exception.Message)"
            }
        }
        $result."dotnet_ngen$($architecture)_eqi_exit_code" = $executed_queued_items.rc
        $result."dotnet_ngen$($architecture)_eqi_output" = $executed_queued_items.stdout
        $result.changed = $true
    }
}

Invoke-Ngen
Invoke-Ngen -architecture "64"

Exit-Json -obj $result
