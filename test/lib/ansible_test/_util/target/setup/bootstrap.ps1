using namespace System.IO
using namespace System.Text

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $PowerShellVersion,
    [Parameter(Mandatory)]
    [string]
    $PowerShellDownloadUri
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$installDir = [Path]::Combine($env:ProgramFiles, "Ansible", "PowerShell", $PowerShellVersion)
$pwshExe = [Path]::Combine($installDir, 'pwsh.exe')

if (Test-Path -LiteralPath $pwshExe) {
    return $pwshExe
}

# We use the zip installation method to allow side-by-side installs without
# affecting existing PowerShell installations.
$zipFilename = "PowerShell-$PowerShellVersion.zip"
$zipPath = [Path]::Combine([Path]::GetTempPath(), $zipFilename)

if (-not (Test-Path -LiteralPath $zipPath)) {
    $attempts = 0

    while ($true) {
        try {
            Invoke-WebRequest -Uri $PowerShellDownloadUri -OutFile $zipPath -UseBasicParsing
        }

        catch {
            $attempts++

            if ($attempts -gt 5) {
                throw "Failed to download PowerShell from $PowerShellDownloadUri after $attempts attempts."
            }

            Start-Sleep -Seconds 5
            continue
        }

        break
    }
}

if (-not (Test-Path -LiteralPath $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

Expand-Archive -LiteralPath $zipPath -DestinationPath $installDir -Force

$null = & $pwshExe -Command "exit"

if ($LASTEXITCODE -ne 0) {
    throw "PowerShell installation verification failed with exit code $LASTEXITCODE"
}

return $pwshExe
