#!/usr/bin/env pwsh
#Requires -Version 6
#Requires -Modules PSScriptAnalyzer, PSSA-PSCustomUseLiteralPath

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

# Until https://github.com/PowerShell/PSScriptAnalyzer/issues/1217 is fixed we need to import Pester if it's
# available.
if (Get-Module -Name Pester -ListAvailable -ErrorAction SilentlyContinue) {
    Import-Module -Name Pester
}

$LiteralPathRule = Import-Module -Name PSSA-PSCustomUseLiteralPath -PassThru
$LiteralPathRulePath = Join-Path -Path $LiteralPathRule.ModuleBase -ChildPath $LiteralPathRule.RootModule

$PSSAParams = @{
    CustomRulePath = @($LiteralPathRulePath)
    IncludeDefaultRules = $true
    Setting = (Join-Path -Path $PSScriptRoot -ChildPath "settings.psd1")
}

$Results = @()

ForEach ($Path in $Args) {
    $Retries = 3

    Do {
        Try {
            $Results += Invoke-ScriptAnalyzer -Path $Path @PSSAParams 3> $null
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
