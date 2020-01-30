#!powershell

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$spec = @{
    options = @{
        packages = @{
            type = "list"
            elements = "dict"
            options = @{
                identity = @{ type = "str"; required = $true }
                version = @{ type = "str"; required = $true }
                architecture = @{ type = "str" }
                resource_id = @{ type = "str" }
                min_version = @{ type = "str"; default = "10.0.17763.0" }
                max_version = @{ type = "str"; default = "10.0.18362.0" }
                filename = @{ type = "str"; required = $true }
            }
        }
        bundles = @{
            type = "list"
            elements = "dict"
            options = @{
                files = @{ type = "list"; elements = "str"; required = $true }
                filename = @{ type = "str"; required = $true }
            }
        }
        publisher = @{ type = "str"; required = $true }
        path = @{ type = "str"; required = $true }
        makeappx_path = @{ type = "str"; required = $true }
        signtool_path = @{ type = "str"; required = $true }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$packages = $module.Params.packages
$bundles = $module.Params.bundles
$publisher = $module.Params.publisher
$path = $module.Params.path
$makeappxPath = $module.Params.makeappx_path
$signtoolPath = $module.Params.signtool_path

if (-not (Test-Path -LiteralPath $path)) {
    $module.FailJson("The path at '$path' does not exist")
}

$manifest = @'
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10" xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10" xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
    <Identity Name="{0}" Version="{1}" Publisher="{2}"{3}{4} />
    <Properties>
        <DisplayName>{0}DisplayName</DisplayName>
        <PublisherDisplayName>PublisherDisplayName</PublisherDisplayName>
        <Description>Test MSIX Package for win_package</Description>
        <Logo>icon.png</Logo>
    </Properties>
    <Resources>
        <Resource Language="en-us" />
    </Resources>
    <Dependencies>
        <TargetDeviceFamily Name="Windows.Desktop" MinVersion="{5}" MaxVersionTested="{6}" />
    </Dependencies>
    <Capabilities>
        <rescap:Capability Name="runFullTrust"/>
    </Capabilities>
    <Applications>
        <Application Id="MsixPackage" Executable="test.exe" EntryPoint="Windows.FullTrustApplication">
            <uap:VisualElements DisplayName="{0}AppDisplayName" Description="Description" Square150x150Logo="icon.png" Square44x44Logo="icon.png" BackgroundColor="#464646"/>
        </Application>
    </Applications>
</Package>
'@

# bytes of http://1x1px.me/000000-0.png
$iconBytes = [System.Convert]::FromBase64String('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNiYAAAAAkAAxkR2eQAAAAASUVORK5CYII=')

$certParams = @{
    # Can only create in the My store, so store it there temporarily.
    CertStoreLocation = 'Cert:\CurrentUser\My'
    FriendlyName = 'win_package test'
    KeyUsage = 'DigitalSignature'
    Subject = $publisher
    TextExtension = @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    Type = 'Custom'
}
$cert = New-SelfSignedCertificate @certParams

try {
    # Need to create a temporary pfx for signtool.exe and we need to import the cert to the Trusted Root store.
    $module.Result.thumbprint = $cert.Thumbprint
    $certPath = Join-Path -Path $module.Tmpdir -ChildPath 'cert.pfx'
    $certPassword = ([char[]]([char]33..[char]126) | Sort-Object {Get-Random})[0..16] -join ''
    $certPasswordSS = ConvertTo-SecureString -String $certPassword -AsPlainText -Force
    $null = $cert |  Export-PfxCertificate -FilePath $certPath -Password $certPasswordSS

    $importParams = @{
        FilePath = $certPath
        CertStoreLocation = 'Cert:\LocalMachine\Root'
        Password = $certPasswordSS
    }
    $null = Import-PfxCertificate @importParams
} finally {
    $cert | Remove-Item -Force
}

$module.Result.changed = $true

foreach ($info in $packages) {
    $architectureAttribute = ""
    if ($info.architecture) {
        $architectureAttribute = " ProcessorArchitecture=`"$($info.architecture)`""
    }

    $resourceIdAttribute = ""
    if ($info.resource_id) {
        $resourceIdAttribute = " ResourceId=`"$($info.resource_id)`""
    }

    $xml = $manifest -f @(
        $info.identity, $info.version, $publisher, $architectureAttribute, $resourceIdAttribute, $info.min_version,
        $info.max_version
    )

    $tempDir = Join-Path -Path $module.Tmpdir -ChildPath ([System.IO.Path]::GetRandomFileName())
    New-Item -Path $tempDir -ItemType Directory > $null
    Set-Content -LiteralPath (Join-Path -Path $tempDir -ChildPath 'AppxManifest.xml') -Value $xml
    Set-Content -LiteralPath (Join-Path -Path $tempDir -ChildPath 'icon.png') -Value $iconBytes
    Set-Content -LiteralPath (Join-Path -Path $tempDir -ChildPath 'test.exe') -Value ''

    $outPath = Join-Path -Path $path -ChildPath $info.filename
    $makeArguments = @($makeappxPath, 'pack', '/d', $tempDir, '/p', $outPath, '/o')
    $res = Run-Command -command (Argv-ToString -arguments $makeArguments)

    if ($res.rc -ne 0) {
        $module.Result.rc = $res.rc
        $module.Result.stdout = $res.stdout
        $module.Result.stderr = $res.stderr
        $module.FailJson("Failed to make package for $($info.filename): see stdout and stderr for more info")
    }

    Remove-Item -Literalpath $tempDir -Force -Recurse

    $signArguments = @($signtoolPath, 'sign', '/a', '/v', '/fd', 'SHA256', '/f', $certPath, '/p', $certPassword,
        $outPath)
    $res = Run-Command -command (Argv-ToString -arguments $signArguments)

    if ($res.rc -ne 0) {
        $module.Result.rc = $res.rc
        $module.Result.stdout = $res.stdout
        $module.Result.stderr = $res.stderr
        $module.FailJson("Failed to sign package for $($info.filename): see stdout and stderr for more info")
    }
}

foreach ($info in $bundles) {
    $tempDir = Join-Path -Path $module.Tmpdir -ChildPath ([System.IO.Path]::GetRandomFileName())
    New-Item -Path $tempDir -ItemType Directory > $null
    foreach ($name in $info.files) {
        $sourcePath = Join-Path -Path $path -ChildPath $name
        $targetPath = Join-Path -Path $tempDir -ChildPath $name
        Move-Item -LiteralPath $sourcePath -Destination $targetPath
    }
    $outPath = Join-Path -Path $path -ChildPath $info.filename
    $makeArguments = @($makeappxPath, 'bundle', '/d', $tempDir, '/p', $outPath, '/o')
    $res = Run-Command -command (Argv-ToString -arguments $makeArguments)

    if ($res.rc -ne 0) {
        $module.Result.rc = $res.rc
        $module.Result.stdout = $res.stdout
        $module.Result.stderr = $res.stderr
        $module.FailJson("Failed to make bundle for $($info.filename): see stdout and stderr for more info")
    }

    Remove-Item -LiteralPath $tempDir -Force -Recurse

    $signArguments = @($signtoolPath, 'sign', '/a', '/v', '/fd', 'SHA256', '/f', $certPath, '/p', $certPassword,
        $outPath)
    $res = Run-Command -command (Argv-ToString -arguments $signArguments)

    if ($res.rc -ne 0) {
        $module.Result.rc = $res.rc
        $module.Result.stdout = $res.stdout
        $module.Result.stderr = $res.stderr
        $module.FailJson("Failed to sign bundle for $($info.filename): see stdout and stderr for more info")
    }
}

$module.ExitJson()
