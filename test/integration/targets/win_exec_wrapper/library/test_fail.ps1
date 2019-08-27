#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true

$data = Get-AnsibleParam -obj $params -name "data" -type "str" -default "normal"
$result = @{
    changed = $false
}

<#
This module tests various error events in PowerShell to verify our hidden trap
catches them all and outputs a pretty error message with a traceback to help
users debug the actual issue

normal - normal execution, no errors
fail - Calls Fail-Json like normal
throw - throws an exception
error - Write-Error with ErrorActionPreferenceStop
cmdlet_error - Calls a Cmdlet with an invalid error
dotnet_exception - Calls a .NET function that will throw an error
function_throw - Throws an exception in a function
proc_exit_fine - calls an executable with a non-zero exit code with Exit-Json
proc_exit_fail - calls an executable with a non-zero exit code with Fail-Json
#>

Function Test-ThrowException {
    throw "exception in function"
}

if ($data -eq "normal") {
    Exit-Json -obj $result
} elseif ($data -eq "fail") {
    Fail-Json -obj $result -message "fail message"
} elseif ($data -eq "throw") {
    throw [ArgumentException]"module is thrown"
} elseif ($data -eq "error") {
    Write-Error -Message $data
} elseif ($data -eq "cmdlet_error") {
    Get-Item -Path "fake:\path"
} elseif ($data -eq "dotnet_exception") {
    [System.IO.Path]::GetFullPath($null)
} elseif ($data -eq "function_throw") {
    Test-ThrowException
} elseif ($data -eq "proc_exit_fine") {
    # verifies that if no error was actually fired and we have an output, we
    # don't use the RC to validate if the module failed
    &cmd.exe /c exit 2
    Exit-Json -obj $result
} elseif ($data -eq "proc_exit_fail") {
    &cmd.exe /c exit 2
    Fail-Json -obj $result -message "proc_exit_fail"
}

# verify no exception were silently caught during our tests
Fail-Json -obj $result -message "end of module"

