#!powershell

# Copyright: (c) 2018, Ansible Project

#Requires -Module Ansible.ModuleUtils.Legacy

$parsed_args = Parse-Args $args

$sleep_delay_sec = Get-AnsibleParam -obj $parsed_args -name "sleep_delay_sec" -type "int" -default 0
$fail_mode = Get-AnsibleParam -obj $parsed_args -name "fail_mode" -type "str" -default "success" -validateset "success","graceful","exception"

If($fail_mode -isnot [array]) {
    $fail_mode = @($fail_mode)
}

$result = @{
    changed = $true
    module_pid = $pid
    module_tempdir = $PSScriptRoot
}

If($sleep_delay_sec -gt 0) {
    Sleep -Seconds $sleep_delay_sec
    $result["slept_sec"] = $sleep_delay_sec
}

If($fail_mode -contains "leading_junk") {
    Write-Output "leading junk before module output"
}

If($fail_mode -contains "graceful") {
    Fail-Json $result "failed gracefully"
}

Try {

    If($fail_mode -contains "exception") {
        Throw "failing via exception"
    }

    Exit-Json $result
}
Finally
{
    If($fail_mode -contains "trailing_junk") {
        Write-Output "trailing junk after module output"
    }
}
