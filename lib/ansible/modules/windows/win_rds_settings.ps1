#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$certificate = Get-AnsibleParam $params -name "certificate_hash" -type "str"
$max_connections = Get-AnsibleParam $params -name "max_connections" -type "int"
# TODO Add support of more settings ?

$result = @{
  changed = $false
}
$diff_text = $null

# Ensure RemoteDesktopServices module is loaded
if ((Get-Module -Name RemoteDesktopServices -ErrorAction SilentlyContinue) -eq $null) {
    Import-Module -Name RemoteDesktopServices
}

if ($null -ne $certificate)
{
    # Validate cert path
    $cert_path = "cert:\LocalMachine\My\$certificate"
    If (-not (Test-Path $cert_path) )
    {
        Fail-Json -obj $result -message "Unable to locate certificate at $cert_path"
    }

    # Get current certificate hash
    $current_cert = (Get-Item -Path "RDS:\GatewayServer\SSLCertificate\Thumbprint").CurrentValue
    if ($current_cert -ne $certificate) {
        Set-Item -Path "RDS:\GatewayServer\SSLCertificate\Thumbprint" -Value $certificate -WhatIf:$check_mode
        $diff_text += "-Certificate = $current_cert`n+Certificate = $certificate`n"
        $result.changed = $true
    }
}

if ($null -ne $max_connections)
{
    # Set the correct value for unlimited connections
    # TODO Use a more explicit value, maybe a string (ex: "max", "none" or "unlimited")
    If ($max_connections -eq -1)
    {
        $max_connections = (Get-Item -Path "RDS:\GatewayServer\MaxConnectionsAllowed").CurrentValue
    }

    # Get current connections limit
    $current_max_connections = (Get-Item -Path "RDS:\GatewayServer\MaxConnections").CurrentValue
    if ($current_max_connections -ne $max_connections) {
        Set-Item -Path "RDS:\GatewayServer\MaxConnections" -Value $max_connections -WhatIf:$check_mode
        $diff_text += "-MaxConnections = $current_max_connections`n+MaxConnections = $max_connections`n"
        $result.changed = $true
    }
}

if ($diff_mode -and $result.changed -eq $true) {
    $result.diff = @{
        prepared = $diff_text
    }
}

Exit-Json $result