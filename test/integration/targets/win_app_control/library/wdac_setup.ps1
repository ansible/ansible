#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        cert_pw = @{
            type = 'str'
            required = $true
            no_log = $true
        }
        remote_tmp_dir = @{
            type = 'path'
            required = $true
        }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$testPrefix = 'Ansible-WDAC'
$certPassword = ConvertTo-SecureString -String $module.Params.cert_pw -Force -AsPlainText
$remoteTmpDir = $module.Params.remote_tmp_dir

$module.Result.changed = $true

$enhancedKeyUsage = [Security.Cryptography.OidCollection]::new()
$null = $enhancedKeyUsage.Add('1.3.6.1.5.5.7.3.3')  # Code Signing
$caParams = @{
    Extension = @(
        [Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($true, $false, 0, $true),
        [Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new('KeyCertSign', $false),
        [Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension ]::new($enhancedKeyUsage, $false)
    )
    CertStoreLocation = 'Cert:\CurrentUser\My'
    NotAfter = (Get-Date).AddDays(1)
    Type = 'Custom'
}
$ca = New-SelfSignedCertificate @caParams -Subject "CN=$testPrefix-Root"

$certParams = @{
    CertStoreLocation = 'Cert:\CurrentUser\My'
    KeyUsage = 'DigitalSignature'
    TextExtension = @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    Type = 'Custom'
}
$cert = New-SelfSignedCertificate @certParams -Subject "CN=$testPrefix-Signed" -Signer $ca
$null = $cert | Export-PfxCertificate -Password $certPassword -FilePath "$remoteTmpDir\signing.pfx"
$cert.Export('Cert') | Set-Content -LiteralPath "$remoteTmpDir\signing.cer" -Encoding Byte

$certUntrusted = New-SelfSignedCertificate @certParams -Subject "CN=$testPrefix-Untrusted"
$null = $certUntrusted | Export-PfxCertificate -Password $certPassword -FilePath "$remoteTmpDir\untrusted.pfx"

$caWithoutKey = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($ca.Export('Cert'))
$certWithoutKey = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($cert.Export('Cert'))

Remove-Item -LiteralPath "Cert:\CurrentUser\My\$($ca.Thumbprint)" -DeleteKey -Force
Remove-Item -LiteralPath "Cert:\CurrentUser\My\$($cert.Thumbprint)" -DeleteKey -Force
Remove-Item -LiteralPath "Cert:\CurrentUser\My\$($certUntrusted.Thumbprint)" -DeleteKey -Force

$root = Get-Item -LiteralPath Cert:\LocalMachine\Root
$root.Open('ReadWrite')
$root.Add($caWithoutKey)
$root.Dispose()

$trustedPublisher = Get-Item -LiteralPath Cert:\LocalMachine\TrustedPublisher
$trustedPublisher.Open('ReadWrite')
$trustedPublisher.Add($certWithoutKey)
$trustedPublisher.Dispose()

$module.Result.ca_thumbprint = $caWithoutKey.Thumbprint
$module.Result.thumbprint = $certWithoutKey.Thumbprint
$module.Result.untrusted_thumbprint = $certUntrusted.Thumbprint

$module.ExitJson()
