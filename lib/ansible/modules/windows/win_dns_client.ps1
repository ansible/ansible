#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

Set-Variable -Visibility Public -Option ReadOnly,AllScope,Constant -Name "AddressFamilies" -Value @{
    [System.Net.Sockets.AddressFamily]::InterNetworkV6 = 'IPv6'
    [System.Net.Sockets.AddressFamily]::InterNetwork = 'IPv4'
}

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

Function Get-OptionalProperty {
    <#
        .SYNOPSIS
        Retreives a property that may not exist from an object that may be null.
        Optionally returns a default value.
        Optionally coalesces to a new type with -as.
        May return null, but will not throw.
    #>
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [Object]
        $InputObject ,

        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [String]
        $Name ,

        [Parameter()]
        [AllowNull()]
        [Object]
        $Default ,

        [Parameter()]
        [System.Type]
        $As
    )

    Process {
        if ($null -eq $InputObject) {
            return $null
        }

        $value = if ($InputObject.PSObject.Properties.Name -contains $Name) {
            $InputObject.$Name
        } else {
            $Default
        }

        if ($As) {
            return $value -as $As
        }

        return $value
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
                Property = "DNSServerSearchOrder", "IPEnabled", "SettingID"
            }
            $adapter_config = Get-CimInstance @cim_params |
                Select-Object -Property DNSServerSearchOrder, IPEnabled, @{
                    Name = 'InterfaceGuid'
                    Expression = { $_.SettingID }
                }

            if ($adapter_config.IPEnabled -eq $false) {
                return
            }

            $reg_info = $adapter_config | Get-RegistryNameServerInfo

            [PSCustomObject]@{
                Name = $_.Name
                InterfaceIndex = $_.InterfaceIndex
                InterfaceGuid = $adapter_config.InterfaceGuid
                RegInfo = $reg_info
            }
        }

        if (@($net_info).Count -eq 0 -and -not $Name.Contains("*")) {
            throw "Get-NetAdapterInfo: Failed to find network adapter(s) that are IP enabled with the name '$Name'"
        }

        $net_info
    }
}

Function Get-RegistryNameServerInfo {
    [CmdletBinding()]
    Param (
        [Parameter(ValueFromPipeline=$true,ValueFromPipelineByPropertyName=$true,Mandatory=$true)]
        [System.Guid]
        $InterfaceGuid
    )

    Begin {
        $protoItems = @{
            [System.Net.Sockets.AddressFamily]::InterNetwork = @{
                Interface = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{{{0}}}'
                StaticNameServer = 'NameServer'
                DhcpNameServer = 'DhcpNameServer'
                EnableDhcp = 'EnableDHCP'
            }

            [System.Net.Sockets.AddressFamily]::InterNetworkV6 = @{
                Interface = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters\Interfaces\{{{0}}}'
                StaticNameServer = 'NameServer'
                DhcpNameServer = 'Dhcpv6DNSServers'
                EnableDhcp = 'EnableDHCP'
            }
        }
    }

    Process {
        foreach ($addrFamily in $AddressFamilies.Keys) {
            $items = $protoItems[$addrFamily]
            $regPath = $items.Interface -f $InterfaceGuid

            if (($iface = Get-Item -LiteralPath $regPath -ErrorAction Ignore)) {
                $iprop = $iface | Get-ItemProperty
                $famInfo = @{
                    AddressFamily = $addrFamily
                    UsingDhcp = Get-OptionalProperty -InputObject $iprop -Name $items.EnableDhcp -As bool
                    EffectiveNameServers = @()
                    DhcpAssignedNameServers = @()
                    NameServerBadFormat = $false
                }

                if (($ns = Get-OptionalProperty -InputObject $iprop -Name $items.DhcpNameServer)) {
                    $famInfo.EffectiveNameServers = $famInfo.DhcpAssignedNameServers = $ns.Split(' ')
                }

                if (($ns = Get-OptionalProperty -InputObject $iprop -Name $items.StaticNameServer)) {
                    $famInfo.EffectiveNameServers = $famInfo.StaticNameServers = $ns -split '[,;\ ]'
                    $famInfo.UsingDhcp = $false
                    $famInfo.NameServerBadFormat = $ns -match '[;\ ]'
                }

                $famInfo
            }
        }
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

    foreach ($proto in $AdapterInfo.RegInfo) {
        $desired_dns = if ($dns_servers) {
            $dns_servers | Where-Object -FilterScript {$_.AddressFamily -eq $proto.AddressFamily}
        }

        $current_dns = [System.Net.IPAddress[]]($proto.EffectiveNameServers)
        Write-DebugLog ("Current DNS settings for '{1}' Address Family: {0}" -f ([string[]]$current_dns -join ", "),$AddressFamilies[$proto.AddressFamily])

        if ($proto.NameServerBadFormat) {
            Write-DebugLog "Malicious DNS server format detected. Will set DNS desired state."
            return $false
            # See: https://www.welivesecurity.com/2016/06/02/crouching-tiger-hidden-dns/
        }

        if ($proto.UsingDhcp -and -not $desired_dns) {
            Write-DebugLog "DHCP DNS Servers are in use and no DNS servers were requested (DHCP is desired)."
        } else {
            if ($desired_dns -and -not $current_dns) {
                Write-DebugLog "There are currently no DNS servers in use, but they should be present."
                return $false
            }

            if ($current_dns -and -not $desired_dns) {
                Write-DebugLog "There are currently DNS servers in use, but they should be absent."
                return $false
            }

            if ($null -ne $current_dns -and
                $null -ne $desired_dns -and
                (Compare-Object -ReferenceObject $current_dns -DifferenceObject $desired_dns -SyncWindow 0)) {
                Write-DebugLog "Static DNS servers are not in the desired state (incorrect or in the wrong order)."
                return $false
            }
        }

        Write-DebugLog ("Current DNS settings match ({0})." -f ([string[]]$desired_dns -join ", "))
    }
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
