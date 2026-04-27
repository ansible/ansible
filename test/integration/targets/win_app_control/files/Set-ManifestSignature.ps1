#!/usr/bin/env pwsh

# 0.5.0 fixed BOM-less encoding issues with Unicode
#Requires -Modules @{ ModuleName = 'OpenAuthenticode'; ModuleVersion = '0.5.0' }

using namespace System.Security.Cryptography.X509Certificates

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Path,

    [Parameter(Mandatory)]
    [string]
    $CertPath,

    [Parameter(Mandatory)]
    [string]
    $CertPass
)

$ErrorActionPreference = 'Stop'

$cert = [X509Certificate2]::new($CertPath, $CertPass)
Set-OpenAuthenticodeSignature -FilePath $Path -Certificate $cert -HashAlgorithm SHA256
