#Configure a Windows host to add an IP address to no_proxy exception
#-------------------------------------------------------------------
#Input: A valid ipaddress which needs to be added to no_proxy exception.
#
#This script validates the given input to proper IPaddress format and
#it adds that IPaddress to PorxyOverride registry variable in the Windows host.


Param([string]$ip_address)
$ip = [ipaddress]$ip_address
if($ip) 
{
$internet_settings = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
$proxy_override = get-ItemProperty $internet_settings
$proxy_override = $proxy_override.ProxyOverride
if(!($proxy_override -match $ip_address)) {
    $proxy_override = $ip_address + ";" + $proxy_override
    $proxy_override = $proxy_override.TrimEnd(";")
    Set-ItemProperty $internet_settings -Name ProxyOverride -Value $proxy_override }
}
