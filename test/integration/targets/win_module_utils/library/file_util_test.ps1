#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

Function Assert-Equals($actual, $expected) {
    if ($actual -cne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

# Test-FilePath Hidden system file
$actual = Test-FilePath -path C:\pagefile.sys
Assert-Equals -actual $actual -expected $true

# Test-FilePath File that doesn't exist
$actual = Test-FilePath -path C:\fakefile
Assert-Equals -actual $actual -expected $false

# Test-FilePath Normal directory
$actual = Test-FilePath -path C:\Windows
Assert-Equals -actual $actual -expected $true

# Test-FilePath Normal file
$actual = Test-FilePath -path C:\Windows\System32\kernel32.dll

# Test-FilePath fails with wildcard
try {
    Test-FilePath -Path C:\Windows\*.exe
    Fail-Json @{} "exception was not thrown with wildcard search for Test-FilePath"
} catch {
    Assert-Equals -actual $_.Exception.Message -expected "found multiple files at path 'C:\Windows\*.exe', make sure no wildcards are set in the path"
}

# Get-FileItem file
$actual = Get-FileItem -path C:\pagefile.sys
Assert-Equals -actual $actual.FullName -expected C:\pagefile.sys
Assert-Equals -actual $actual.PSIsContainer -expected $false
Assert-Equals -actual $actual.Exists -expected $true

# Get-FileItem directory
$actual = Get-FileItem -path C:\Windows
Assert-Equals -actual $actual.FullName -expected C:\Windows
Assert-Equals -actual $actual.PSIsContainer -expected $true
Assert-Equals -actual $actual.Exists -expected $true

# Get-FileItem doesn't exists
$actual = Get-FileItem -path C:\fakefile
Assert-Equals -actual $actual -expected $null

# Get-FileItem fails with wildcard
try {
    Get-FileItem -Path C:\Windows\*.exe
    Fail-Json @{} "exception was not thrown with wildcard search for Get-FileItem"
} catch {
    Assert-Equals -actual $_.Exception.Message -expected "found multiple files at path 'C:\Windows\*.exe', make sure no wildcards are set in the path"
}

Exit-Json @{ data = 'success' }
