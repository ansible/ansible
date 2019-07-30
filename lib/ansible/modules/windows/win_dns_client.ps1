#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# FUTURE: check statically-set values via registry so we can determine difference between DHCP-source values and static values? (prevent spurious changed
# notifications on DHCP-sourced values)

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

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
        # IPv6, only here for completeness since we don't support it yet
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

Function Get-DnsClientMatch {
    Param(
        [string] $adapter_name,
        [string[]] $ipv4_addresses
    )

    Write-DebugLog ("Getting DNS config for adapter {0}" -f $adapter_name)

    $current_dns_all = Get-DnsClientServerAddress -InterfaceAlias $adapter_name

    Write-DebugLog ("Current DNS settings: " + $($current_dns_all | Out-String))

    $current_dns_v4 = ($current_dns_all | Where-Object AddressFamily -eq 2 <# IPv4 #>).ServerAddresses

    If (($null -eq $current_dns_v4) -and ($null -eq $ipv4_addresses)) {
        $v4_match = $True
    }

    ElseIf (($null -eq $current_dns_v4) -or ($null -eq $ipv4_addresses)) {
        $v4_match = $False
    }

    Else {
        $v4_match = @(Compare-Object $current_dns_v4 $ipv4_addresses -SyncWindow 0).Count -eq 0
    }

    # TODO: implement IPv6

    Write-DebugLog ("Current DNS settings match ({0}) : {1}" -f ($ipv4_addresses -join ", "), $v4_match)

    return $v4_match
}

Function Validate-IPAddress {
    Param([string] $address)

    $addrout = $null

    return [System.Net.IPAddress]::TryParse($address, [ref] $addrout)
}

Function Set-DnsClientAddresses
{
    Param(
        [string] $adapter_name,
        [string[]] $ipv4_addresses
    )

    Write-DebugLog ("Setting DNS addresses for adapter {0} to ({1})" -f $adapter_name, ($ipv4_addresses -join ", "))

    If ($null -eq $ipv4_addresses) {
        Set-DnsClientServerAddress -InterfaceAlias $adapter_name -ResetServerAddress
    }

    Else {
    # this silently ignores invalid IPs, so we validate parseability ourselves up front...
        Set-DnsClientServerAddress -InterfaceAlias $adapter_name -ServerAddresses $ipv4_addresses
    }

    # TODO: implement IPv6
}

$result = @{changed=$false}

$params = Parse-Args -arguments $args -supports_check_mode $true

$adapter_names = Get-AnsibleParam $params "adapter_names" -Default "*"
$ipv4_addresses = Get-AnsibleParam $params "ipv4_addresses" -FailIfEmpty $result

If($ipv4_addresses -is [string]) {
    If($ipv4_addresses.Length -gt 0) {
        $ipv4_addresses = @($ipv4_addresses)
    }
    Else {
        $ipv4_addresses = @()
    }
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

    Write-DebugLog ("Validating IP addresses ({0})" -f ($ipv4_addresses -join ", "))

    $invalid_addresses = @($ipv4_addresses | Where-Object  { -not (Validate-IPAddress $_) })

    If($invalid_addresses.Count -gt 0) {
        throw "Invalid IP address(es): ({0})" -f ($invalid_addresses -join ", ")
    }

    ForEach($adapter_name in $adapters) {
        $result.changed = $result.changed -or (-not (Get-DnsClientMatch $adapter_name $ipv4_addresses))

        If($result.changed) {
            If(-not $check_mode) {
                Set-DnsClientAddresses $adapter_name $ipv4_addresses
            }
            Else {
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
