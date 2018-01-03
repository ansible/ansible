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

Import-FileUtil

$pagefile = Get-PagefilePath
if ($pagefile) {
    # Test-AnsiblePath Hidden system file
    $actual = Test-AnsiblePath -Path $pagefile
    Assert-Equals -actual $actual -expected $true

    $actual = Test-AnsiblePath -Path "\\?\$pagefile"
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

# Test-AnsiblePath Normal directory with Container type
$actual = Test-AnsiblePath -Path C:\Windows -PathType Container
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath Normal directory with Leaf type
$actual = Test-AnsiblePath -Path C:\Windows -PathType Leaf
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath Normal file
$actual = Test-AnsiblePath -Path C:\Windows\System32\kernel32.dll
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath Normal file with Container type
$actual = Test-AnsiblePath -Path C:\Windows\System32\kernel32.dll -PathType Container
Assert-Equals -actual $actual -expected $false

# Test-AnsiblePath Normal file with Leaf type
$actual = Test-AnsiblePath -Path C:\Windows\System32\kernel32.dll -PathType Leaf
Assert-Equals -actual $actual -expected $true

# Test-AnsiblePath works with wildcard (this works in Test-Path so we should replicate it here)
$actual = Test-AnsiblePath -Path C:\Windows\*.exe
Assert-Equals -actual $actual -expected $true

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

# Get-AnsibleItem doesn't exists
$failed = $false
try {
    $actual = Get-AnsibleItem -Path C:\fakefile
} catch {
    $failed = $true
    Assert-Equals -actual $_.Exception.Message -expected "Cannot find path 'C:\fakefile' because it does not exist."
}
Assert-Equals -actual $failed -expected $true

# call Get-AnsibleFileHash with invalid algorithm
$failed = $false
try {
    Get-AnsibleFileHash -Path C:\fakefile -Algorithm sha449
} catch {
    $failed = $true
    Assert-Equals -actual ($_.Exception.Message.StartsWith("Cannot find type [System.Security.Cryptography.sha449CryptoServiceProvider]")) -expected $true
}
Assert-Equals -actual $failed -expected $true

# call Get-AnsibleFileHash with various algorithms
$tmp_file = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText($tmp_file, "Hello World", [System.Text.Encoding]::ASCII)

    $actual = Get-AnsibleFileHash -Path $tmp_file -Algorithm md5
    Assert-Equals -actual $actual -expected "b10a8db164e0754105b7a99be72e3fe5"

    $actual = Get-AnsibleFileHash -Path $tmp_file -Algorithm sha1
    Assert-Equals -actual $actual -expected "0a4d55a8d778e5022fab701977c5d840bbc486d0"

    $actual = Get-AnsibleFileHash -Path $tmp_file -Algorithm sha256
    Assert-Equals -actual $actual -expected "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"

    $actual = Get-AnsibleFileHash -Path $tmp_file -Algorithm sha384
    Assert-Equals -actual $actual -expected "99514329186b2f6ae4a1329e7ee6c610a729636335174ac6b740f9028396fcc803d0e93863a7c3d90f86beee782f4f3f"

    $actual = Get-AnsibleFileHash -Path $tmp_file -Algorithm sha512
    Assert-Equals -actual $actual -expected "2c74fd17edafd80e8447b0d46741ee243b7eb74dd2149a0ab1b9246fb30382f27e853d8585719e0e67cbda0daa8f51671064615d645ae27acb15bfb1447f459b"
} finally {
    Remove-Item -Path $tmp_file -Force > $null
}

$result.data = "success"
Exit-Json -obj $result
