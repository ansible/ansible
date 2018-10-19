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

Function Get-PagefilePath() {
    $pagefile = $null
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem
    if ($cs.AutomaticManagedPagefile) {
        $pagefile = "$($env:SystemRoot.Substring(0, 1)):\pagefile.sys"
    } else {
        $pf = Get-CimInstance -ClassName Win32_PageFileSetting
        if ($null -ne $pf) {
            $pagefile = $pf[0].Name
        }
    }
    return $pagefile
}

$pagefile = Get-PagefilePath
if ($pagefile) {
    # Test-AnsiblePath Hidden system file
    $actual = Test-AnsiblePath -Path $pagefile
    Assert-Equals -actual $actual -expected $true

    # Get-AnsibleItem file
    $actual = Get-AnsibleItem -Path $pagefile
    Assert-Equals -actual $actual.FullName -expected $pagefile
    Assert-Equals -actual $actual.Attributes.HasFlag([System.IO.FileAttributes]::Directory) -expected $false
    Assert-Equals -actual $actual.Exists -expected $true
}

# Test-AnsiblePath File that doesn't exist
$actual = Test-AnsiblePath -Path C:\fakefile
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath Directory that doesn't exist
$actual = Test-AnsiblePath -Path C:\fakedirectory
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath file in non-existant directory
$actual = Test-AnsiblePath -Path C:\fakedirectory\fakefile.txt
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath Normal directory
$actual = Test-AnsiblePath -Path C:\Windows
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath Normal file
$actual = Test-AnsiblePath -Path C:\Windows\System32\kernel32.dll
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath fails with wildcard
$failed = $false
try {
    Test-AnsiblePath -Path C:\Windows\*.exe
} catch {
    $failed = $true
    Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"GetAttributes`" with `"1`" argument(s): `"Illegal characters in path.`""
}
Assert-Equals -actual $failed -expected $true

# Test-AnsiblePath on non file PS Provider object
$actual = Test-AnsiblePath -Path Cert:\LocalMachine\My
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath on environment variable
$actual = Test-AnsiblePath -Path env:SystemDrive
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath on environment variable that does not exist
$actual = Test-AnsiblePath -Path env:FakeEnvValue
Assert-Equals -actual $actual -expected $false

# Get-AnsibleItem doesn't exist with -ErrorAction SilentlyContinue param
$actual = Get-AnsibleItem -Path C:\fakefile -ErrorAction SilentlyContinue
Assert-Equals -actual $actual -expected $null

# Get-AnsibleItem directory
$actual = Get-AnsibleItem -Path C:\Windows
Assert-Equals -actual $actual.FullName -expected C:\Windows
Assert-Equals -actual $actual.Attributes.HasFlag([System.IO.FileAttributes]::Directory) -expected $true
Assert-Equals -actual $actual.Exists -expected $true

# ensure Get-AnsibleItem doesn't fail in a try/catch and -ErrorAction SilentlyContinue - stop's a trap from trapping it
try {
    $actual = Get-AnsibleItem -Path C:\fakepath -ErrorAction SilentlyContinue
} catch {
    Fail-Json -obj $result -message "this should not fire"
}
Assert-Equals -actual $actual -expected $null

$result.data = "success"
Exit-Json -obj $result
