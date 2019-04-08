#!/usr/bin/env pwsh
#Requires -Version 6
#Requires -Module Pester

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)][System.String]$OutputFile,
    [Parameter(Mandatory=$true)][System.String]$Tests,
    [System.String]$Coverage
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$test_config = ConvertFrom-Json -InputObject $Tests
$include = $test_config.include
$exclude = $test_config.exclude

# Make sure we dot source helpful test functions that each test can use
$modules_path = [System.IO.Path]::GetFullPath(
    [System.IO.Path]::Combine($PSScriptRoot, "..", "..", "units", "pester_functions.ps1")
)
.$modules_path

$exclude_scripts = $exclude | ForEach-Object -Process { Join-Path -Path $pwd -ChildPath $_.path }
$test_scripts = [System.Collections.Generic.List`1[String]]@()
$coverage_scripts = [System.Collections.Generic.HashSet`1[String]]@()

$find_params = @{
    Filter = 'test_*.ps1'
    Force = $true
    Recurse = $true
}
foreach ($include_info in $include) {
    foreach ($module_name in $include_info.modules) {
        $module_path = Find-AnsibleModule -Name $module_name
        $coverage_scripts.Add($module_path) > $null
    }

    Get-ChildItem -LiteralPath $include_info.path @find_params | `
        Where-Object -Property FullName -NotIn $exclude_scripts | `
            ForEach-Object -Process { $test_scripts.Add($_.FullName) }
}

$pester_params = @{
    EnableExit = $false
    OutputFile = $OutputFile
    OutputFormat = "NUnitXml"
    PassThru = $true
    Script = $test_scripts
}

if ($Coverage) {
    $utils_path = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::Combine($PSScriptRoot, "..", "..", "..", "lib", "ansible", "module_utils", "powershell")
    )
    Get-ChildItem -LiteralPath $utils_path -Filter "*.psm1" -Recurse | `
        ForEach-Object -Process { $coverage_scripts.Add($_.FullName) > $null }

    $executor_path = [System.IO.Path]::GetFulLPath(
        [System.IO.Path]::Combine($PSScriptRoot, "..", "..", "..", "lib", "ansible", "executor", "powershell")
    )
    Get-ChildItem -LiteralPath $executor_path -Filter "*.ps1" -Recurse | `
        ForEach-Object -Process { $coverage_scripts.Add($_.FullName) > $null }

    $pester_params.CodeCoverage = $coverage_scripts
    $pester_params.CodeCoverageOutputFile = $Coverage
    $pester_params.CodeCoverageOutputFileFormat = "JaCoCo"
}

$result = Invoke-Pester @pester_params

if ($result.FailedCount -gt 0) {
    Write-Error -Message "Failed pester tests with $($result.FailedCount) failing tests"
    exit 1
} else {
    exit 0
}
