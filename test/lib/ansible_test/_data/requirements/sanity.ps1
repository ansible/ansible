#!/usr/bin/env pwsh
param (
    [Switch]
    $IsContainer
)

#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module -Name PSScriptAnalyzer -RequiredVersion 1.18.0 -Scope CurrentUser

if ($IsContainer) {
    # PSScriptAnalyzer contain lots of json files for the UseCompatibleCommands check. We don't use this rule so by
    # removing the contents we can save 200MB in the docker image (or more in the future).
    # https://github.com/PowerShell/PSScriptAnalyzer/blob/master/RuleDocumentation/UseCompatibleCommands.md
    $pssaPath = (Get-Module -ListAvailable -Name PSScriptAnalyzer).ModuleBase
    $compatPath = Join-Path -Path $pssaPath -ChildPath compatibility_profiles -AdditionalChildPath '*'
    Remove-Item -Path $compatPath -Recurse -Force
}

# Installed the PSCustomUseLiteralPath rule
Install-Module -Name PSSA-PSCustomUseLiteralPath -RequiredVersion 0.1.1 -Scope CurrentUser
