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

Set-Variable -Visibility Public -Option ReadOnly,AllScope,Constant -Name "log_path" -Value (
    Get-AnsibleParam $params "log_path"
)

Function Write-DebugLog {
    Param(
    [string]$msg
    )

    $DebugPreference = "Continue"
    $ErrorActionPreference = "Continue"
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug $msg

    $log_path = $null
    $log_path = Get-AnsibleParam -obj $params -name "log_path"

    if($log_path) {
        Add-Content $log_path $msg
    }
}

# minimal impl of Get-NetAdapter we need on 2008/2008R2
Function Get-NetAdapterLegacy {
    Param([string]$Name="*")

    $wmiargs = @{Class="Win32_NetworkAdapter"}

    If($Name.Contains("*")) {
        $wmiargs.Filter = "NetConnectionID LIKE '$($Name.Replace("*","%"))'"
    }
    Else {
        $wmiargs.Filter = "NetConnectionID = '$Name'"
    }

    $wmiprop = @(
        @{Name="Name"; Expression={$_.NetConnectionID}},
        @{Name="ifIndex"; Expression={$_.DeviceID}}
    )

    $res = Get-CIMInstance @wmiargs | Select-Object -Property $wmiprop

    If(@($res).Count -eq 0 -and -not $Name.Contains("*")) {
        throw "Get-NetAdapterLegacy: No Win32_NetworkAdapter objects found with property 'NetConnectionID' equal to '$Name'"
    }

    Write-Output $res
}

If(-not $(Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {
    New-Alias Get-NetAdapter Get-NetAdapterLegacy -Force
}

# minimal impl of Get-DnsClientServerAddress for 2008/2008R2
Function Get-DnsClientServerAddressLegacy {
    Param([string]$InterfaceAlias)

    $idx = Get-NetAdapter -Name $InterfaceAlias | Select-Object -ExpandProperty ifIndex

    $adapter_config = Get-CIMInstance Win32_NetworkAdapterConfiguration -Filter "Index=$idx"

    return @(
        # IPv4 values
        [PSCustomObject]@{InterfaceAlias=$InterfaceAlias;InterfaceIndex=$idx;AddressFamily=2;ServerAddresses=$adapter_config.DNSServerSearchOrder};
        # IPv6 values
        [PSCustomObject]@{InterfaceAlias=$InterfaceAlias;InterfaceIndex=$idx;AddressFamily=23;ServerAddresses=@()};
    )
}

If(-not $(Get-Command Get-DnsClientServerAddress -ErrorAction SilentlyContinue)) {
    New-Alias Get-DnsClientServerAddress Get-DnsClientServerAddressLegacy
}

# minimal impl of Set-DnsClientServerAddress for 2008/2008R2
Function Set-DnsClientServerAddressLegacy {
    Param(
        [string]$InterfaceAlias,
        [Array]$ServerAddresses=@(),
        [switch]$ResetServerAddresses
    )

    $idx = Get-NetAdapter -Name $InterfaceAlias | Select-Object -ExpandProperty ifIndex

    $adapter_config = Get-CIMInstance Win32_NetworkAdapterConfiguration -Filter "Index=$idx"

    If($ResetServerAddresses) {
        $arguments = @{}
    }
    Else {
        $arguments = @{ DNSServerSearchOrder = $ServerAddresses }
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
        [string] $adapter_name,
        [string[]] $dns_servers
    )
    $dns_servers = $dns_servers | Where-Object {
        (Assert-IPAddress $_) -and (([System.Net.IPAddress]$_).AddressFamily -in $AddressFamilies)
    } | ForEach-Object {
        [System.Net.IPAddress]$_
    }
    Write-DebugLog ("Getting DNS config for adapter {0}" -f $adapter_name)

    $current_dns = [System.Net.IPAddress[]](
        Get-DnsClientServerAddress -InterfaceAlias $adapter_name | ForEach-Object {
            $_.ServerAddresses
        } | Where-Object {
            (Assert-IPAddress $_) -and ($_.AddressFamily -in $AddressFamilies)
        }
    )
    Write-DebugLog ("Current DNS settings: " + ($current_dns.IPAddressToString | Out-String))

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
    Write-DebugLog ("Current DNS settings match ({0})." -f ($dns_servers.IPAddressToString -join ", "))
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
        [string] $adapter_name,
        [string[]] $dns_servers
    )
    $dns_servers = [System.Net.IPAddress[]]$dns_servers

    Write-DebugLog ("Setting DNS addresses for adapter {0} to ({1})" -f $adapter_name, ($dns_servers.IPAddressToString -join ", "))

    If ($dns_servers) {
        Set-DnsClientServerAddress -InterfaceAlias $adapter_name -ResetServerAddress
    } Else {
        Set-DnsClientServerAddress -InterfaceAlias $adapter_name -ServerAddresses $dns_servers
    }
}

$result = @{changed=$false}

$params = Parse-Args -arguments $args -supports_check_mode $true

$adapter_names = Get-AnsibleParam $params "adapter_names" -Default "*"
$dns_servers = Get-AnsibleParam $params "dns_servers" -aliases "ipv4_addresses","ip_addresses","addresses" -FailIfEmpty $result

if($dns_servers -is [string]) {
    if($dns_servers.Length -gt 0) {
        $dns_servers = @($dns_servers)
    } else {
        $dns_servers = @()
    }
}
if($adapter_names -is [string]) {
    $adapter_names = @($adapter_names)
}

$check_mode = Get-AnsibleParam $params "_ansible_check_mode" -Default $false

Try {

    Write-DebugLog ("Validating adapter name {0}" -f $adapter_names)

    $adapters = @($adapter_names)

    If($adapter_names -eq "*") {
        $adapters = Get-NetAdapter | Select-Object -ExpandProperty Name
    }
    # TODO: add support for an actual list of adapter names
    # validate network adapter names
    ElseIf(@(Get-NetAdapter | Where-Object Name -eq $adapter_names).Count -eq 0) {
        throw "Invalid network adapter name: {0}" -f $adapter_names
    }

    Write-DebugLog ("Validating IP addresses ({0})" -f ($dns_servers -join ", "))
    $invalid_addresses = @($dns_servers | Where-Object { -not (Assert-IPAddress $_) })
    if($invalid_addresses.Count -gt 0) {
        throw "Invalid IP address(es): ({0})" -f ($invalid_addresses -join ", ")
    }

    foreach($adapter_name in $adapter_names) {
        Write-DebugLog ("Validating adapter name {0}" -f $adapter_name)
        if(-not (Get-DnsClientServerAddress -InterfaceAlias $adapter_name)) {
            throw "Invalid network adapter name: {0}" -f $adapter_name
        }
        if(-not (Test-DnsClientMatch $adapter_name $dns_servers)) {
            $result.changed = $true
            if(-not $check_mode) {
                Set-DnsClientAddresses $adapter_name $dns_servers
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
