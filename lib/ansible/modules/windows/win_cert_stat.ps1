#!powershell

# Copyright: (c) 2019, Micah Hunsberger
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

function ConvertTo-Timestamp($start_date, $end_date) {
    if ($start_date -and $end_date) {
        return (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$store_location_values = ([System.Security.Cryptography.X509Certificates.StoreLocation]).GetEnumValues() | ForEach-Object { $_.ToString() }

$spec = @{
    options = @{
        thumbprint = @{ type = "str"; required = $true }
        store_name = @{ type = "str"; default = "My"; }
        store_location = @{ type = "str"; default = "LocalMachine"; choices = $store_location_values; }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$thumbprint = $module.Params.thumbprint
$store_name = $module.Params.store_name
$store_location = $module.params.store_location

$module.Result.exists = $false

$cert_path = [io.path]::Combine('Cert:\', $store_location, $store_name, $thumbprint)

if (Test-Path -LiteralPath $cert_path)
{
    $epoch_date = Get-Date -Date "01/01/1970"

    $cert = Get-Item -LiteralPath $cert_path
    $module.Result.exists = $true
    $module.Result.friendly_name = $cert.FriendlyName
    $module.Result.thumbprint = $cert.Thumbprint
    $module.Result.subject = $cert.Subject
    $module.Result.issuer = $cert.Issuer
    $module.Result.valid_from = (ConvertTo-Timestamp -start_date $epoch_date -end_date $cert.NotBefore.ToUniversalTime())
    $module.Result.valid_to = (ConvertTo-Timestamp -start_date $epoch_date -end_date $cert.NotAfter.ToUniversalTime())
    $module.Result.serial_number = $cert.SerialNumber
    $module.Result.archived = $cert.Archived
    $module.Result.version = $cert.Version
    $module.Result.has_private_key = $cert.HasPrivateKey
    $module.Result.issued_by = $cert.GetNameInfo('SimpleName', $true)
    $module.Result.issued_to = $cert.GetNameInfo('SimpleName', $false)
    $module.Result.signature_algorithm = $cert.SignatureAlgorithm.FriendlyName
    $module.Result.dns_names = @($module.Result.issued_to)
    $module.Result.raw = [System.Convert]::ToBase64String($cert.GetRawCertData())
    $module.Result.public_key = [System.Convert]::ToBase64String($cert.GetPublicKey())
    $module.Result.extensions = @()
    foreach ($extension in $cert.Extensions)
    {
        $module.Result.extensions += @{
            critical = $extension.Critical
            field = $extension.Oid.FriendlyName
            value = $extension.Format($false)
        }
        if ($extension -is [System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension])
        {
            $module.Result.is_ca = $extension.CertificateAuthority
            $module.Result.path_length_constraint = $extension.PathLengthConstraint
        }
        elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension])
        {
            $module.Result.intended_purposes = $extension.EnhancedKeyUsages.FriendlyName -as [string[]]
        }
        elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension])
        {
            $module.Result.key_usages = $extension.KeyUsages.ToString().Split(',').Trim() -as [string[]]
        }
        elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension])
        {
            $module.Result.ski = $extension.SubjectKeyIdentifier
        }
        elseif ($extension.Oid.value -eq '2.5.29.17')
        {
            $sans = $extension.Format($true).Split("`r`n", [System.StringSplitOptions]::RemoveEmptyEntries)
            foreach($san in $sans)
            {
                $san_parts = $san.Split("=")
                if ($san_parts.Length -ge 2 -and $san_parts[0].Trim() -eq 'DNS Name')
                {
                    $module.Result.dns_names += $san_parts[1].Trim()
                }
            }
        }
    }
}

$module.ExitJson()
