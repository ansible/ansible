#!powershell

# Copyright: (c) 2019, Micah Hunsberger
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

function ConvertTo-Timestamp($start_date, $end_date)
{
    if ($start_date -and $end_date)
    {
        return (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

function Format-Date([DateTime]$date)
{
    return $date.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssK')
}

function Get-CertificateInfo ($cert)
{
    $epoch_date = Get-Date -Date "01/01/1970"

    $cert_info = @{ extensions = @() }
    $cert_info.friendly_name = $cert.FriendlyName
    $cert_info.thumbprint = $cert.Thumbprint
    $cert_info.subject = $cert.Subject
    $cert_info.issuer = $cert.Issuer
    $cert_info.valid_from = (ConvertTo-Timestamp -start_date $epoch_date -end_date $cert.NotBefore.ToUniversalTime())
    $cert_info.valid_from_iso8601 = Format-Date -date $cert.NotBefore
    $cert_info.valid_to = (ConvertTo-Timestamp -start_date $epoch_date -end_date $cert.NotAfter.ToUniversalTime())
    $cert_info.valid_to_iso8601 = Format-Date -date $cert.NotAfter
    $cert_info.serial_number = $cert.SerialNumber
    $cert_info.archived = $cert.Archived
    $cert_info.version = $cert.Version
    $cert_info.has_private_key = $cert.HasPrivateKey
    $cert_info.issued_by = $cert.GetNameInfo('SimpleName', $true)
    $cert_info.issued_to = $cert.GetNameInfo('SimpleName', $false)
    $cert_info.signature_algorithm = $cert.SignatureAlgorithm.FriendlyName
    $cert_info.dns_names = [System.Collections.Generic.List`1[String]]@($cert_info.issued_to)
    $cert_info.raw = [System.Convert]::ToBase64String($cert.GetRawCertData())
    $cert_info.public_key = [System.Convert]::ToBase64String($cert.GetPublicKey())
    if ($cert.Extensions.Count -gt 0)
    {
        [array]$cert_info.extensions = foreach ($extension in $cert.Extensions)
        {
            $extension_info = @{
                critical = $extension.Critical
                field    = $extension.Oid.FriendlyName
                value    = $extension.Format($false)
            }
            if ($extension -is [System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension])
            {
                $cert_info.is_ca = $extension.CertificateAuthority
                $cert_info.path_length_constraint = $extension.PathLengthConstraint
            }
            elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension])
            {
                $cert_info.intended_purposes = $extension.EnhancedKeyUsages.FriendlyName -as [string[]]
            }
            elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension])
            {
                $cert_info.key_usages = $extension.KeyUsages.ToString().Split(',').Trim() -as [string[]]
            }
            elseif ($extension -is [System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension])
            {
                $cert_info.ski = $extension.SubjectKeyIdentifier
            }
            elseif ($extension.Oid.value -eq '2.5.29.17')
            {
                $sans = $extension.Format($true).Split("`r`n", [System.StringSplitOptions]::RemoveEmptyEntries)
                foreach ($san in $sans)
                {
                    $san_parts = $san.Split("=")
                    if ($san_parts.Length -ge 2 -and $san_parts[0].Trim() -eq 'DNS Name')
                    {
                        $cert_info.dns_names.Add($san_parts[1].Trim())
                    }
                }
            }
            $extension_info
        }
    }
    return $cert_info
}

$store_location_values = ([System.Security.Cryptography.X509Certificates.StoreLocation]).GetEnumValues() | ForEach-Object { $_.ToString() }

$spec = @{
    options = @{
        thumbprint     = @{ type = "str"; required = $false }
        store_name     = @{ type = "str"; default = "My"; }
        store_location = @{ type = "str"; default = "LocalMachine"; choices = $store_location_values; }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$thumbprint = $module.Params.thumbprint
$store_name = $module.Params.store_name
$store_location = [System.Security.Cryptography.X509Certificates.Storelocation]"$($module.Params.store_location)"

$store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
$store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)

$module.Result.exists = $false
$module.Result.certificates = @()

try
{
    if ($null -ne $thumbprint)
    {
        $found_certs = $store.Certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $thumbprint, $false)
    }
    else
    {
        $found_certs = $store.Certificates
    }

    if ($found_certs.Count -gt 0)
    {
        $module.Result.exists = $true
        [array]$module.Result.certificates = $found_certs | ForEach-Object { Get-CertificateInfo -cert $_ } | Sort-Object -Property { $_.thumbprint }
    }
}
finally
{
    $store.Close()
}

$module.ExitJson()
