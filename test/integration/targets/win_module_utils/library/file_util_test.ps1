#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

Function Assert-Equals($actual, $expected) {
    if ($actual -cne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Load-FileUtilFunctions

# Test-AnsiblePath Hidden system file
$actual = Test-AnsiblePath -Path C:\pagefile.sys
Assert-Equals -actual $actual -expected $true

$actual = Test-AnsiblePath -Path "\\?\C:\pagefile.sys"
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath File that doesn't exist
$actual = Test-AnsiblePath -Path C:\fakefile
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath Normal directory
$actual = Test-AnsiblePath -Path C:\Windows
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath Normal file
$actual = Test-AnsiblePath -Path C:\Windows\System32\kernel32.dll

# Test-AnsiblePath fails with wildcard
$failed = $false
try {
    Test-AnsiblePath -Path C:\Windows\*.exe
} catch {
    $failed = $true
    Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"GetAttributes`" with `"1`" argument(s): `"Illegal characters in path.`""
}
Assert-Equals -actual $failed -expected $true

# Get-AnsibleItem file
$actual = Get-AnsibleItem -Path C:\pagefile.sys
Assert-Equals -actual $actual.FullName -expected C:\pagefile.sys
Assert-Equals -actual $actual.Attributes.HasFlag([System.IO.FileAttributes]::Directory) -expected $false
Assert-Equals -actual $actual.Exists -expected $true

# Get-AnsibleItem directory
$actual = Get-AnsibleItem -Path C:\Windows
Assert-Equals -actual $actual.FullName -expected C:\Windows
Assert-Equals -actual $actual.Attributes.HasFlag([System.IO.FileAttributes]::Directory) -expected $true
Assert-Equals -actual $actual.Exists -expected $true

# Get-AnsibleItem doesn't exists
$failed = $false
try {
    $actual = Get-AnsibleItem -Path C:\fakefile
} catch {
    $failed = $true
    Assert-Equals -actual $_.Exception.Message -expected "Cannot find path 'C:\fakefile' because it does not exist."
}
Assert-Equals -actual $failed -expected $true

# Get-AnsibleItem doesn't exist with -ErrorAction SilentlyContinue param
$actual = Get-AnsibleItem -Path C:\fakefile -ErrorAction SilentlyContinue
Assert-Equals -actual $actual -expected $null

# call Get-AnsibleFileHash with invalid algorithm
$failed = $false
try {
    Get-AnsibleFileHash -Path C:\fakefile -Algorithm sha449
} catch {
    $failed = $true
    Assert-Equals -actual ($_.Exception.Message.StartsWith("Cannot find type [System.Security.Cryptography.sha449CryptoServiceProvider]")) -expected $true
}
Assert-Equals -actual $failed -expected $true

$result.data = "success"
Exit-Json -obj $result
