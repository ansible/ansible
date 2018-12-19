#!/usr/bin/env pwsh
#Requires -Version 6
#Requires -Modules PSScriptAnalyzer

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

$Results = @()

ForEach ($Path in $Args) {
    $Retries = 3

    Do {
        Try {
            $Results += Invoke-ScriptAnalyzer -Path $Path -Setting $PSScriptRoot/settings.psd1 3> $null
            $Retries = 0
        }
        Catch {
            If (--$Retries -le 0) {
                Throw
            }
        }
    }
    Until ($Retries -le 0)
}

ConvertTo-Json -InputObject $Results
