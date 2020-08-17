#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args
$exe = Get-AnsibleParam -obj $params -name "exe" -type "path" -failifempty $true

$result = @{
    changed = $false
}

$exe_directory = Split-Path -Path $exe -Parent
$exe_filename = Split-Path -Path $exe -Leaf
$test_name = $null

Function Assert-Equals($actual, $expected) {
    if ($actual -cne $expected) {
        Fail-Json -obj $result -message "Test $test_name failed`nActual: '$actual' != Expected: '$expected'"
    }
}

$test_name = "full exe path"
$actual = Run-Command -command "`"$exe`" arg1 arg2 `"arg 3`""
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "arg1`r`narg2`r`narg 3`r`n"
Assert-Equals -actual $actual.stderr -expected ""
Assert-Equals -actual $actual.executable -expected $exe

$test_name = "exe in special char dir"
$tmp_dir = Join-Path -Path $env:TEMP -ChildPath "ansible .ÅÑŚÌβŁÈ [$!@^&test(;)]"
try {
    New-Item -Path $tmp_dir -ItemType Directory > $null
    $exe_special = Join-Path $tmp_dir -ChildPath "PrintArgv.exe"
    Copy-Item -LiteralPath $exe -Destination $exe_special
    $actual = Run-Command -command "`"$exe_special`" arg1 arg2 `"arg 3`""
} finally {
    Remove-Item -LiteralPath $tmp_dir -Force -Recurse
}
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "arg1`r`narg2`r`narg 3`r`n"
Assert-Equals -actual $actual.stderr -expected ""
Assert-Equals -actual $actual.executable -expected $exe_special

$test_name = "invalid exe path"
try {
    $actual = Run-Command -command "C:\fakepath\$exe_filename arg1"
    Fail-Json -obj $result -message "Test $test_name failed`nCommand should have thrown an exception"
} catch {
    Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"SearchPath`" with `"1`" argument(s): `"Could not find file 'C:\fakepath\$exe_filename'.`""
}

$test_name = "exe in current folder"
$actual = Run-Command -command "$exe_filename arg1" -working_directory $exe_directory
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "arg1`r`n"
Assert-Equals -actual $actual.stderr -expected ""
Assert-Equals -actual $actual.executable -expected $exe

$test_name = "no working directory set"
$actual = Run-Command -command "cmd.exe /c cd"
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "$($pwd.Path)`r`n"
Assert-Equals -actual $actual.stderr -expected ""
Assert-Equals -actual $actual.executable.ToUpper() -expected "$env:SystemRoot\System32\cmd.exe".ToUpper()

$test_name = "working directory override"
$actual = Run-Command -command "cmd.exe /c cd" -working_directory $env:SystemRoot
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "$env:SystemRoot`r`n"
Assert-Equals -actual $actual.stderr -expected ""
Assert-Equals -actual $actual.executable.ToUpper() -expected "$env:SystemRoot\System32\cmd.exe".ToUpper()

$test_name = "working directory invalid path"
try {
    $actual = Run-Command -command "doesn't matter" -working_directory "invalid path here"
    Fail-Json -obj $result -message "Test $test_name failed`nCommand should have thrown an exception"
} catch {
    Assert-Equals -actual $_.Exception.Message -expected "invalid working directory path 'invalid path here'"
}

$test_name = "invalid arguments"
$actual = Run-Command -command "ipconfig.exe /asdf"
Assert-Equals -actual $actual.rc -expected 1

$test_name = "test stdout and stderr streams"
$actual = Run-Command -command "cmd.exe /c echo stdout && echo stderr 1>&2"
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "stdout `r`n"
Assert-Equals -actual $actual.stderr -expected "stderr `r`n"

$test_name = "Test UTF8 output from stdout stream"
$actual = Run-Command -command "powershell.exe -ExecutionPolicy ByPass -Command `"Write-Host '💩'`""
Assert-Equals -actual $actual.rc -expected 0
Assert-Equals -actual $actual.stdout -expected "💩`n"
Assert-Equals -actual $actual.stderr -expected ""

$test_name = "test default environment variable"
Set-Item -LiteralPath env:TESTENV -Value "test"
$actual = Run-Command -command "cmd.exe /c set"
$env_present = $actual.stdout -split "`r`n" | Where-Object { $_ -eq "TESTENV=test" }
if ($null -eq $env_present) {
    Fail-Json -obj $result -message "Test $test_name failed`nenvironment variable TESTENV not found in stdout`n$($actual.stdout)"
}

$test_name = "test custom environment variable1"
$actual = Run-Command -command "cmd.exe /c set" -environment @{ TESTENV2 = "testing" }
$env_not_present = $actual.stdout -split "`r`n" | Where-Object { $_ -eq "TESTENV=test" }
$env_present = $actual.stdout -split "`r`n" | Where-Object { $_ -eq "TESTENV2=testing" }
if ($null -ne $env_not_present) {
    Fail-Json -obj $result -message "Test $test_name failed`nenvironment variabel TESTENV found in stdout when it should be`n$($actual.stdout)"
}
if ($null -eq $env_present) {
    Fail-json -obj $result -message "Test $test_name failed`nenvironment variable TESTENV2 not found in stdout`n$($actual.stdout)"
}

$test_name = "input test"
$wrapper = @"
begin {
    `$string = ""
} process {
    `$current_input = [string]`$input
    `$string += `$current_input
} end {
    Write-Host `$string
}
"@
$encoded_wrapper = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($wrapper))
$actual = Run-Command -command "powershell.exe -ExecutionPolicy ByPass -EncodedCommand $encoded_wrapper" -stdin "Ansible"
Assert-Equals -actual $actual.stdout -expected "Ansible`n"

$result.data = "success"
Exit-Json -obj $result
