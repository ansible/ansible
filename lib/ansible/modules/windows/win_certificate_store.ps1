#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$store_name_values = ([System.Security.Cryptography.X509Certificates.StoreName]).GetEnumValues() | ForEach-Object { $_.ToString() }
$store_location_values = ([System.Security.Cryptography.X509Certificates.StoreLocation]).GetEnumValues() | ForEach-Object { $_.ToString() }

$spec = @{
    options = @{
        state = @{ type = "str"; default = "present"; choices = "absent", "exported", "present" }
        path = @{ type = "path" }
        thumbprint = @{ type = "str" }
        store_name = @{ type = "str"; default = "My"; choices = $store_name_values }
        store_location = @{ type = "str"; default = "LocalMachine"; choices = $store_location_values }
        password = @{ type = "str"; no_log = $true }
        key_exportable = @{ type = "bool"; default = $true }
        key_storage = @{ type = "str"; default = "default"; choices = "default", "machine", "user" }
        file_type = @{ type = "str"; default = "der"; choices = "der", "pem", "pkcs12" }
    }
    required_if = @(
        @("state", "absent", @("path", "thumbprint"), $true),
        @("state", "exported", @("path", "thumbprint")),
        @("state", "present", @("path"))
    )
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

Function Get-CertFile($module, $path, $password, $key_exportable, $key_storage) {
    # parses a certificate file and returns X509Certificate2Collection
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $module.FailJson("File at '$path' either does not exist or is not a file")
    }

    # must set at least the PersistKeySet flag so that the PrivateKey
    # is stored in a permanent container and not deleted once the handle
    # is gone.
    $store_flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::PersistKeySet

    $key_storage = $key_storage.substring(0,1).ToUpper() + $key_storage.substring(1).ToLower()
    $store_flags = $store_flags -bor [Enum]::Parse([System.Security.Cryptography.X509Certificates.X509KeyStorageFlags], "$($key_storage)KeySet")
    if ($key_exportable) {
        $store_flags = $store_flags -bor [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable
    }

    # TODO: If I'm feeling adventurours, write code to parse PKCS#12 PEM encoded
    # file as .NET does not have an easy way to import this
    $certs = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2Collection

    try {
        $certs.Import($path, $password, $store_flags)
    } catch {
        $module.FailJson("Failed to load cert from file: $($_.Exception.Message)", $_)
    }

    return $certs
}

Function New-CertFile($module, $cert, $path, $type, $password) {
    $content_type = switch ($type) {
        "pem" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Cert }
        "der" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Cert }
        "pkcs12" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Pkcs12 }
    }
    if ($type -eq "pkcs12") {
        $missing_key = $false
        if ($null -eq $cert.PrivateKey) {
            $missing_key = $true
        } elseif ($cert.PrivateKey.CspKeyContainerInfo.Exportable -eq $false) {
            $missing_key = $true
        }
        if ($missing_key) {
            $module.FailJson("Cannot export cert with key as PKCS12 when the key is not marked as exportable or not accesible by the current user")
        }
    }

    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
        $module.Result.changed = $true
    }
    try {
        $cert_bytes = $cert.Export($content_type, $password)
    } catch {
        $module.FailJson("Failed to export certificate as bytes: $($_.Exception.Message)", $_)
    }

    # Need to manually handle a PEM file
    if ($type -eq "pem") {
        $cert_content = "-----BEGIN CERTIFICATE-----`r`n"
        $base64_string = [System.Convert]::ToBase64String($cert_bytes, [System.Base64FormattingOptions]::InsertLineBreaks)
        $cert_content += $base64_string
        $cert_content += "`r`n-----END CERTIFICATE-----"
        $file_encoding = [System.Text.Encoding]::ASCII
        $cert_bytes = $file_encoding.GetBytes($cert_content)
    } elseif ($type -eq "pkcs12") {
        $module.Result.key_exported = $false
        if ($null -ne $cert.PrivateKey) {
            $module.Result.key_exportable = $cert.PrivateKey.CspKeyContainerInfo.Exportable
        }
    }

    if (-not $module.CheckMode) {
        try {
            [System.IO.File]::WriteAllBytes($path, $cert_bytes)
        } catch [System.ArgumentNullException] {
            $module.FailJson("Failed to write cert to file, cert was null: $($_.Exception.Message)", $_)
        } catch [System.IO.IOException] {
            $module.FailJson("Failed to write cert to file due to IO Exception: $($_.Exception.Message)", $_)
        } catch [System.UnauthorizedAccessException] {
            $module.FailJson("Failed to write cert to file due to permissions: $($_.Exception.Message)", $_)
        } catch {
            $module.FailJson("Failed to write cert to file: $($_.Exception.Message)", $_)
        }
    }
    $module.Result.changed = $true
}

Function Get-CertFileType($path, $password) {
    $certs = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2Collection
    try {
        $certs.Import($path, $password, 0)
    } catch [System.Security.Cryptography.CryptographicException] {
        # the file is a pkcs12 we just had the wrong password
        return "pkcs12"
    } catch {
        return "unknown"
    }

    $file_contents = Get-Content -LiteralPath $path -Raw
    if ($file_contents.StartsWith("-----BEGIN CERTIFICATE-----")) {
        return "pem"
    } elseif ($file_contents.StartsWith("-----BEGIN PKCS7-----")) {
        return "pkcs7-ascii"
    } elseif ($certs.Count -gt 1) {
        # multiple certs must be pkcs7
        return "pkcs7-binary"
    } elseif ($certs[0].HasPrivateKey) {
        return "pkcs12"
    } elseif ($path.EndsWith(".pfx") -or $path.EndsWith(".p12")) {
        # no way to differenciate a pfx with a der file so we must rely on the
        # extension
        return "pkcs12"
    } else {
        return "der"
    }
}

$state = $module.Params.state
$path = $module.Params.path
$thumbprint = $module.Params.thumbprint
$store_name = [System.Security.Cryptography.X509Certificates.StoreName]"$($module.Params.store_name)"
$store_location = [System.Security.Cryptography.X509Certificates.Storelocation]"$($module.Params.store_location)"
$password = $module.Params.password
$key_exportable = $module.Params.key_exportable
$key_storage = $module.Params.key_storage
$file_type = $module.Params.file_type

$module.Result.thumbprints = @()

$store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
try {
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
} catch [System.Security.Cryptography.CryptographicException] {
    $module.FailJson("Unable to open the store as it is not readable: $($_.Exception.Message)", $_)
} catch [System.Security.SecurityException] {
    $module.FailJson("Unable to open the store with the current permissions: $($_.Exception.Message)", $_)
} catch {
    $module.FailJson("Unable to open the store: $($_.Exception.Message)", $_)
}
$store_certificates = $store.Certificates

try {
    if ($state -eq "absent") {
        $cert_thumbprints = @()

        if ($null -ne $path) {
            $certs = Get-CertFile -module $module -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
            foreach ($cert in $certs) {
                $cert_thumbprints += $cert.Thumbprint
            }
        } elseif ($null -ne $thumbprint) {
            $cert_thumbprints += $thumbprint
        }

        foreach ($cert_thumbprint in $cert_thumbprints) {
            $module.Result.thumbprints += $cert_thumbprint
            $found_certs = $store_certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $cert_thumbprint, $false)
            if ($found_certs.Count -gt 0) {
                foreach ($found_cert in $found_certs) {
                    try {
                        if (-not $module.CheckMode) {
                            $store.Remove($found_cert)
                        }
                    } catch [System.Security.SecurityException] {
                        $module.FailJson("Unable to remove cert with thumbprint '$cert_thumbprint' with current permissions: $($_.Exception.Message)", $_)
                    } catch {
                        $module.FailJson("Unable to remove cert with thumbprint '$cert_thumbprint': $($_.Exception.Message)", $_)
                    }
                    $module.Result.changed = $true
                }
            }
        }
    } elseif ($state -eq "exported") {
        # TODO: Add support for PKCS7 and exporting a cert chain
        $module.Result.thumbprints += $thumbprint
        $export = $true
        if (Test-Path -LiteralPath $path -PathType Container) {
            $module.FailJson("Cannot export cert to path '$path' as it is a directory")
        } elseif (Test-Path -LiteralPath $path -PathType Leaf) {
            $actual_cert_type = Get-CertFileType -path $path -password $password
            if ($actual_cert_type -eq $file_type) {
                try {
                    $certs = Get-CertFile -module $module -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
                } catch {
                    # failed to load the file so we set the thumbprint to something
                    # that will fail validation
                    $certs = @{Thumbprint = $null}
                }

                if ($certs.Thumbprint -eq $thumbprint) {
                    $export = $false
                }
            }
        }

        if ($export) {
            $found_certs = $store_certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $thumbprint, $false)
            if ($found_certs.Count -ne 1) {
                $module.FailJson("Found $($found_certs.Count) certs when only expecting 1")
            }

            New-CertFile -module $module -cert $found_certs -path $path -type $file_type -password $password
        }
    } else {
        $certs = Get-CertFile -module $module -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
        foreach ($cert in $certs) {
            $module.Result.thumbprints += $cert.Thumbprint
            $found_certs = $store_certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $cert.Thumbprint, $false)
            if ($found_certs.Count -eq 0) {
                try {
                    if (-not $module.CheckMode) {
                        $store.Add($cert)
                    }
                } catch [System.Security.Cryptography.CryptographicException] {
                    $module.FailJson("Unable to import certificate with thumbprint '$($cert.Thumbprint)' with the current permissions: $($_.Exception.Message)", $_)
                } catch {
                    $module.FailJson("Unable to import certificate with thumbprint '$($cert.Thumbprint)': $($_.Exception.Message)", $_)
                }
                $module.Result.changed = $true
            }
        }
    }
} finally {
    $store.Close()
}

$module.ExitJson()
