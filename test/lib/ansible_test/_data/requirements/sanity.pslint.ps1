param (
    [Switch]
    $IsContainer
)

#Requires -Version 7

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

Function Install-PSModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [String]
        $Name,

        [Parameter(Mandatory = $true)]
        [Version]
        $RequiredVersion
    )

    # In case PSGallery is down we check if the module is already installed.
    $installedModule = Get-Module -Name $Name -ListAvailable | Where-Object Version -eq $RequiredVersion
    if (-not $installedModule) {
        Install-Module -Name $Name -RequiredVersion $RequiredVersion -Scope CurrentUser
    }
}

# Versions changes should be made first in ansible-test which is then synced to
# the default-test-container over time
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-PSModule -Name PSScriptAnalyzer -RequiredVersion 1.21.0

if ($IsContainer) {
    # PSScriptAnalyzer contain lots of json files for the UseCompatibleCommands check. We don't use this rule so by
    # removing the contents we can save 200MB in the docker image (or more in the future).
    # https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/UseCompatibleCommands.md
    $pssaPath = (Get-Module -ListAvailable -Name PSScriptAnalyzer).ModuleBase
    $compatPath = Join-Path -Path $pssaPath -ChildPath compatibility_profiles -AdditionalChildPath '*'
    Remove-Item -Path $compatPath -Recurse -Force
}

# Installed the PSCustomUseLiteralPath rule
Install-PSModule -Name PSSA-PSCustomUseLiteralPath -RequiredVersion 0.1.1
