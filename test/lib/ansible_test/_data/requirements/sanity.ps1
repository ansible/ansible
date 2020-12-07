#!/usr/bin/env pwsh
#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

Function Install-PSModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [String]
        $Name,

        [Parameter(Mandatory=$true)]
        [Version]
        $RequiredVersion
    )

    # In case PSGallery is down we check if the module is already installed.
    $installedModule = Get-Module -Name $Name -ListAvailable | Where-Object Version -eq $RequiredVersion
    if (-not $installedModule) {
        Install-Module -Name $Name -RequiredVersion $RequiredVersion -Scope CurrentUser
   }
}

Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-PSModule -Name PSScriptAnalyzer -RequiredVersion 1.18.0

# Installed the PSCustomUseLiteralPath rule
Install-PSModule -Name PSSA-PSCustomUseLiteralPath -RequiredVersion 0.1.1
