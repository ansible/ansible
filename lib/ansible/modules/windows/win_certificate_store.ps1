#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$store_name_values = ([System.Security.Cryptography.X509Certificates.StoreName]).GetEnumValues()
$store_location_values = ([System.Security.Cryptography.X509Certificates.StoreLocation]).GetEnumValues()

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent", "exported", "present"
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty ($state -eq "present" -or $state -eq "exported")
$thumbprint = Get-AnsibleParam -obj $params -name "thumbprint" -type "str" -failifempty ($state -eq "exported")
$store_name = Get-AnsibleParam -obj $params -name "store_name" -type "str" -default "My" -validateset $store_name_values
$store_location = Get-AnsibleParam -obj $params -name "store_location" -type "str" -default "LocalMachine" -validateset $store_location_values
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$key_exportable = Get-AnsibleParam -obj $params -name "key_exportable" -type "bool" -default $true
$key_storage = Get-AnsibleParam -obj $params -name "key_storage" -type "str" -default "default" -validateset "default", "machine", "user"
$file_type = Get-AnsibleParam -obj $params -name "file_type" -type "str" -default "der" -validateset "der", "pem", "pkcs12"

$result = @{
    changed = $false
    thumbprints = @()
}

Function Get-CertFile($path, $password, $key_exportable, $key_storage) {
    # parses a certificate file and returns X509Certificate2Collection
    if (-not (Test-Path -Path $path -PathType Leaf)) {
        Fail-Json -obj $result -message "File at '$path' either does not exist or is not a file"
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
        Fail-Json -obj $result -message "Failed to load cert from file: $($_.Exception.Message)"
    }

    return $certs
}

Function New-CertFile($cert, $path, $type, $password) {
    $content_type = switch ($type) {
        "pem" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Cert }
        "der" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Cert }
        "pkcs12" { [System.Security.Cryptography.X509Certificates.X509ContentType]::Pkcs12 }
    }
    if ($type -eq "pkcs12") {
        $missing_key = $false
        if ($cert.PrivateKey -eq $null) {
            $missing_key = $true
        } elseif ($cert.PrivateKey.CspKeyContainerInfo.Exportable -eq $false) {
            $missing_key = $true
        }
        if ($missing_key) {
            Fail-Json -obj $result -message "Cannot export cert with key as PKCS12 when the key is not marked as exportable or not accesible by the current user"
        }
    }

    if (Test-Path -Path $path) {
        Remove-Item -Path $path -Force
        $result.changed = $true
    }
    try {
        $cert_bytes = $cert.Export($content_type, $password)
    } catch {
        Fail-Json -obj $result -message "Failed to export certificate as bytes: $($_.Exception.Message)"
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
        $result.key_exported = $false
        if ($cert.PrivateKey -ne $null) {
            $result.key_exportable = $cert.PrivateKey.CspKeyContainerInfo.Exportable
        }
    }
    
    if (-not $check_mode) {
        try {
            [System.IO.File]::WriteAllBytes($path, $cert_bytes)
        } catch [System.ArgumentNullException] {
            Fail-Json -obj $result -message "Failed to write cert to file, cert was null: $($_.Exception.Message)"
        } catch [System.IO.IOException] {
            Fail-Json -obj $result -message "Failed to write cert to file due to IO exception: $($_.Exception.Message)"
        } catch [System.UnauthorizedAccessException, System>Security.SecurityException] {
            Fail-Json -obj $result -message "Failed to write cert to file due to permission: $($_.Exception.Message)"
        } catch {
            Fail-Json -obj $result -message "Failed to write cert to file: $($_.Exception.Message)"
        }
    }
    $result.changed = $true
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

    $file_contents = Get-Content -Path $path -Raw
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

$store_name = [System.Security.Cryptography.X509Certificates.StoreName]::$store_name
$store_location = [System.Security.Cryptography.X509Certificates.Storelocation]::$store_location
$store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
try {
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
} catch [System.Security.Cryptography.CryptographicException] {
    Fail-Json -obj $result -message "Unable to open the store as it is not readable: $($_.Exception.Message)"
} catch [System.Security.SecurityException] {
    Fail-Json -obj $result -message "Unable to open the store with the current permissions: $($_.Exception.Message)"
} catch {
    Fail-Json -obj $result -message "Unable to open the store: $($_.Exception.Message)"
}
$store_certificates = $store.Certificates

try {
    if ($state -eq "absent") {
        $cert_thumbprints = @()
        
        if ($path -ne $null) {
            $certs = Get-CertFile -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
            foreach ($cert in $certs) {
                $cert_thumbprints += $cert.Thumbprint
            }
        } elseif ($thumbprint -ne $null) {
            $cert_thumbprints += $thumbprint
        } else {
            Fail-Json -obj $result -message "Either path or thumbprint must be set when state=absent"
        }

        foreach ($cert_thumbprint in $cert_thumbprints) {
            $result.thumbprints += $cert_thumbprint
            $found_certs = $store_certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $cert_thumbprint, $false)
            if ($found_certs.Count -gt 0) {
                foreach ($found_cert in $found_certs) {
                    try {
                        if (-not $check_mode) {
                            $store.Remove($found_cert)
                        }
                    } catch [System.Security.SecurityException] {
                        Fail-Json -obj $result -message "Unable to remove cert with thumbprint '$cert_thumbprint' with the current permissions: $($_.Exception.Message)"
                    } catch {
                        Fail-Json -obj $result -message "Unable to remove cert with thumbprint '$cert_thumbprint': $($_.Exception.Message)"
                    }
                    $result.changed = $true
                }
            }
        }
    } elseif ($state -eq "exported") {
        # TODO: Add support for PKCS7 and exporting a cert chain
        $result.thumbprints += $thumbprint
        $export = $true
        if (Test-Path -Path $path -PathType Container) {
            Fail-Json -obj $result -message "Cannot export cert to path '$path' as it is a directory"
        } elseif (Test-Path -Path $path -PathType Leaf) {
            $actual_cert_type = Get-CertFileType -path $path -password $password
            if ($actual_cert_type -eq $file_type) {
                try {
                    $certs = Get-CertFile -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
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
                Fail-Json -obj $result -message "Found $($found_certs.Count) certs when only expecting 1"
            }
    
            New-CertFile -cert $found_certs -path $path -type $file_type -password $password
        }
    } else {
        $certs = Get-CertFile -path $path -password $password -key_exportable $key_exportable -key_storage $key_storage
        foreach ($cert in $certs) {
            $result.thumbprints += $cert.Thumbprint
            $found_certs = $store_certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $cert.Thumbprint, $false)
            if ($found_certs.Count -eq 0) {
                try {
                    if (-not $check_mode) {
                        $store.Add($cert)
                    }
                } catch [System.Security.Cryptography.CryptographicException] {
                    Fail-Json -obj $result -message "Unable to import certificate with thumbprint '$($cert.Thumbprint)' with the current permissions: $($_.Exception.Message)"
                } catch {
                    Fail-Json -obj $result -message "Unable to import certificate with thumbprint '$($cert.Thumbprint)': $($_.Exception.Message)"
                }
                $result.changed = $true
            }
        }
    }
} finally {
    $store.Close()
}

Exit-Json -obj $result
