using namespace System.IO
using namespace System.Net
using namespace System.Reflection
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

$currentProtocol = [ServicePointManager]::SecurityProtocol
if ([SecurityProtocolType].GetMember("Tls13")) {
    # If the Tls13 member is present we are on .NET Framework 4.8+ so using
    # the SystemDefault setting will use the OS policies. If it's not set
    # to SystemDefault already we are running in a PSRemoting WSMan host
    # and need some reflection to reconfigure the policies to get it to use
    # the OS policies.

    if ($currentProtocol -ne 'SystemDefault') {
        # https://learn.microsoft.com/en-us/dotnet/framework/network-programming/tls#switchsystemnetdontenablesystemdefaulttlsversions
        $disableSystemTlsField = [ServicePointManager].GetField(
            's_disableSystemDefaultTlsVersions',
            [BindingFlags]'NonPublic, Static')
        if ($disableSystemTlsField -and $disableSystemTlsField.GetValue($null)) {
            $disableSystemTlsField.SetValue($null, $false)
        }

        [ServicePointManager]::SecurityProtocol = [SecurityProtocolType]::SystemDefault
    }
}
else {
    # We are on .NET 4.7 or older, as TLS 1.2 is the max version we can
    # use here regardless of the OS, manually enable the protocols known to
    # the runtime.
    if ([SecurityProtocolType].GetMember("Tls11")) {
        $currentProtocol = $currentProtocol -bor [SecurityProtocolType]::Tls11
    }
    if ([SecurityProtocolType].GetMember("Tls12")) {
        $currentProtocol = $currentProtocol -bor [SecurityProtocolType]::Tls12
    }
    [ServicePointManager]::SecurityProtocol = $currentProtocol
}

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
