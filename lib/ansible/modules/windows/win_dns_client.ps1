#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# FUTURE: check statically-set values via registry so we can determine difference between DHCP-source values and static values? (prevent spurious changed
# notifications on DHCP-sourced values)

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

Set-Variable -Visibility Public -Option ReadOnly,AllScope,Constant -Name "AddressFamilies" -Value @(
    [System.Net.Sockets.AddressFamily]::InterNetworkV6,
    [System.Net.Sockets.AddressFamily]::InterNetwork
)
$result = @{changed=$false}

$params = Parse-Args -arguments $args -supports_check_mode $true
Set-Variable -Visibility Public -Option ReadOnly,AllScope,Constant -Name "log_path" -Value (
    Get-AnsibleParam $params "log_path"
)
$adapter_names = Get-AnsibleParam $params "adapter_names" -Default "*"
$dns_servers = Get-AnsibleParam $params "dns_servers" -aliases "ipv4_addresses","ip_addresses","addresses" -FailIfEmpty $result
$check_mode = Get-AnsibleParam $params "_ansible_check_mode" -Default $false


Function Write-DebugLog {
    Param(
    [string]$msg
    )

    $DebugPreference = "Continue"
    $ErrorActionPreference = "Continue"
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug $msg
    if($log_path) {
        Add-Content $log_path $msg
    }
}

Function Get-NetAdapterInfo {
    [CmdletBinding()]
    Param (
        [Parameter(ValueFromPipeline=$true)]
        [String]$Name = "*"
    )

    Process {
        if (Get-Command -Name Get-NetAdapter -ErrorAction SilentlyContinue) {
            $adapter_info = Get-NetAdapter @PSBoundParameters | Select-Object -Property Name, InterfaceIndex
        } else {
            # Older hosts 2008/2008R2 don't have Get-NetAdapter, fallback to deprecated Win32_NetworkAdapter
            $cim_params = @{
                ClassName = "Win32_NetworkAdapter"
                Property = "InterfaceIndex", "NetConnectionID"
            }

            if ($Name.Contains("*")) {
                $cim_params.Filter = "NetConnectionID LIKE '$($Name.Replace("*", "%"))'"
            } else {
                $cim_params.Filter = "NetConnectionID = '$Name'"
            }

            $adapter_info = Get-CimInstance @cim_params | Select-Object -Property @(
                @{Name="Name"; Expression={$_.NetConnectionID}},
                @{Name="InterfaceIndex"; Expression={$_.InterfaceIndex}}
            )
        }

        # Need to filter the adapter that are not IPEnabled, while we are at it, also get the DNS config.
        $net_info = $adapter_info | ForEach-Object -Process {
            $cim_params = @{
                ClassName = "Win32_NetworkAdapterConfiguration"
                Filter = "InterfaceIndex = $($_.InterfaceIndex)"
                Property = "DNSServerSearchOrder", "IPEnabled"
            }
            $adapter_config = Get-CimInstance @cim_params
            if ($adapter_config.IPEnabled -eq $false) {
                return
            }

            if (Get-Command -Name Get-DnsClientServerAddress -ErrorAction SilentlyContinue) {
                $dns_servers = Get-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex | Select-Object -Property @(
                    "AddressFamily",
                    "ServerAddresses"
                )
            } else {
                $dns_servers = @(
                    [PSCustomObject]@{
                        AddressFamily = [System.Net.Sockets.AddressFamily]::InterNetwork
                        ServerAddresses = $adapter_config.DNSServerSearchOrder
                    },
                    [PSCustomObject]@{
                        AddressFamily = [System.Net.Sockets.AddressFamily]::InterNetworkV6
                        ServerAddresses = @()  # WMI does not support IPv6 so we just keep it blank.
                    }
                )
            }

            [PSCustomObject]@{
                Name = $_.Name
                InterfaceIndex = $_.InterfaceIndex
                DNSServers = $dns_servers
            }
        }

        if (@($net_info).Count -eq 0 -and -not $Name.Contains("*")) {
            throw "Get-NetAdapterInfo: Failed to find network adapter(s) that are IP enabled with the name '$Name'"
        }

        $net_info
    }
}

# minimal impl of Set-DnsClientServerAddress for 2008/2008R2
Function Set-DnsClientServerAddressLegacy {
    Param(
        [int]$InterfaceIndex,
        [Array]$ServerAddresses=@(),
        [switch]$ResetServerAddresses
    )
    $cim_params = @{
        ClassName = "Win32_NetworkAdapterConfiguration"
        Filter = "InterfaceIndex = $InterfaceIndex"
        KeyOnly = $true
    }
    $adapter_config = Get-CimInstance @cim_params

    If($ResetServerAddresses) {
        $arguments = @{}
    }
    Else {
        $arguments = @{ DNSServerSearchOrder = [string[]]$ServerAddresses }
    }
    $res = Invoke-CimMethod -InputObject $adapter_config -MethodName SetDNSServerSearchOrder -Arguments $arguments

    If($res.ReturnValue -ne 0) {
        throw "Set-DnsClientServerAddressLegacy: Error calling SetDNSServerSearchOrder, code $($res.ReturnValue))"
    }
}

If(-not $(Get-Command Set-DnsClientServerAddress -ErrorAction SilentlyContinue)) {
    New-Alias Set-DnsClientServerAddress Set-DnsClientServerAddressLegacy
}

Function Test-DnsClientMatch {
    Param(
        [PSCustomObject]$AdapterInfo,
        [System.Net.IPAddress[]] $dns_servers
    )
    Write-DebugLog ("Getting DNS config for adapter {0}" -f $AdapterInfo.Name)

    $current_dns = [System.Net.IPAddress[]]($AdapterInfo.DNSServers.ServerAddresses)
    Write-DebugLog ("Current DNS settings: {0}" -f ([string[]]$dns_servers -join ", "))

    if(($null -eq $current_dns) -and ($null -eq $dns_servers)) {
        Write-DebugLog "Neither are dns servers configured nor specified within the playbook."
        return $true
    } elseif ($null -eq $current_dns) {
        Write-DebugLog "There are currently no dns servers specified, but they should be present."
        return $false
    } elseif ($null -eq $dns_servers) {
        Write-DebugLog "There are currently dns servers specified, but they should be absent."
        return $false
    }
    foreach($address in $current_dns) {
        if($address -notin $dns_servers) {
            Write-DebugLog "There are currently fewer dns servers present than specified within the playbook."
            return $false
        }
    }
    foreach($address in $dns_servers) {
        if($address -notin $current_dns) {
            Write-DebugLog "There are currently further dns servers present than specified within the playbook."
            return $false
        }
    }
    Write-DebugLog ("Current DNS settings match ({0})." -f ([string[]]$dns_servers -join ", "))
    return $true
}

Function Assert-IPAddress {
    Param([string] $address)

    $addrout = $null

    return [System.Net.IPAddress]::TryParse($address, [ref] $addrout)
}

Function Set-DnsClientAddresses
{
    Param(
        [PSCustomObject]$AdapterInfo,
        [System.Net.IPAddress[]] $dns_servers
    )

    Write-DebugLog ("Setting DNS addresses for adapter {0} to ({1})" -f $AdapterInfo.Name, ([string[]]$dns_servers -join ", "))

    If ($dns_servers) {
        Set-DnsClientServerAddress -InterfaceIndex $AdapterInfo.InterfaceIndex -ServerAddresses $dns_servers
    } Else {
        Set-DnsClientServerAddress -InterfaceIndex $AdapterInfo.InterfaceIndex -ResetServerAddress
    }
}

if($dns_servers -is [string]) {
    if($dns_servers.Length -gt 0) {
        $dns_servers = @($dns_servers)
    } else {
        $dns_servers = @()
    }
}
# Using object equals here, to check for exact match (without implicit type conversion)
if([System.Object]::Equals($adapter_names, "*")) {
    $adapters = Get-NetAdapterInfo
} else {
    $adapters = $adapter_names | Get-NetAdapterInfo
}

Try {

    Write-DebugLog ("Validating IP addresses ({0})" -f ($dns_servers -join ", "))
    $invalid_addresses = @($dns_servers | Where-Object { -not (Assert-IPAddress $_) })
    if($invalid_addresses.Count -gt 0) {
        throw "Invalid IP address(es): ({0})" -f ($invalid_addresses -join ", ")
    }

    foreach($adapter_info in $adapters) {
        Write-DebugLog ("Validating adapter name {0}" -f $adapter_info.Name)

        if(-not (Test-DnsClientMatch $adapter_info $dns_servers)) {
            $result.changed = $true
            if(-not $check_mode) {
                Set-DnsClientAddresses $adapter_info $dns_servers
            } else {
                Write-DebugLog "Check mode, skipping"
            }
        }
    }

    Exit-Json $result

}
Catch {
    $excep = $_

    Write-DebugLog "Exception: $($excep | out-string)"

    Throw
}
