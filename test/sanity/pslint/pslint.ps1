#!/usr/bin/env pwsh
#Requires -Version 6
#Requires -Modules PSScriptAnalyzer

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$ExcludedRules = PSUseBOMForUnicodeEncodedFile
$Results = @()

ForEach ($Path in $Args) {
    $Results += Invoke-ScriptAnalyzer -Path $Path `
      -Setting $PSScriptRoot/settings.psd1 `
      -ExcludeRule $ExcludedRules
}

ConvertTo-Json -InputObject $Results
