#!powershell
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

# $params is not currently used in this module
# $params = Parse-Args $args;

$result = New-Object psobject @{
    ansible_facts = New-Object psobject
    changed = $false
};

$osversion = [Environment]::OSVersion
$memory = @()
$memory += Get-WmiObject win32_Physicalmemory
$capacity = 0
$memory | foreach {$capacity += $_.Capacity}
$netcfg = Get-WmiObject win32_NetworkAdapterConfiguration

$ActiveNetcfg = @(); $ActiveNetcfg+= $netcfg | where {$_.ipaddress -ne $null}
$formattednetcfg = @()
foreach ($adapter in $ActiveNetcfg)
{
    $thisadapter = New-Object psobject @{
    interface_name = $adapter.description
    dns_domain = $adapter.dnsdomain
    default_gateway = $null
    interface_index = $adapter.InterfaceIndex
    }
    
    if ($adapter.defaultIPGateway)
    {
        $thisadapter.default_gateway = $adapter.DefaultIPGateway[0].ToString()
    }
    
    $formattednetcfg += $thisadapter;$thisadapter = $null
}

Set-Attr $result.ansible_facts "ansible_interfaces" $formattednetcfg

Set-Attr $result.ansible_facts "ansible_hostname" $env:COMPUTERNAME;
Set-Attr $result.ansible_facts "ansible_fqdn" "$([System.Net.Dns]::GetHostByName((hostname)).HostName)"
Set-Attr $result.ansible_facts "ansible_system" $osversion.Platform.ToString()
Set-Attr $result.ansible_facts "ansible_os_family" "Windows"
Set-Attr $result.ansible_facts "ansible_distribution" $osversion.VersionString
Set-Attr $result.ansible_facts "ansible_distribution_version" $osversion.Version.ToString()

Set-Attr $result.ansible_facts "ansible_totalmem" $capacity

$ips = @()
Foreach ($ip in $netcfg.IPAddress) { If ($ip) { $ips += $ip } }
Set-Attr $result.ansible_facts "ansible_ip_addresses" $ips

$psversion = $PSVersionTable.PSVersion.Major
$winrm_cert_expiry = Get-ChildItem -Path Cert:\LocalMachine\My | where Subject -EQ "CN=$env:COMPUTERNAME" | select NotAfter

Set-Attr $result.ansible_facts "ansible_powershell_version" $psversion
Set-Attr $result.ansible_facts "ansible_winrm_certificate_expires" $winrm_cert_expiry.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")


Exit-Json $result;
