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

# enabled $params (David O'Brien, 06/08/2015)
$params = Parse-Args $args;


Function Get-CustomFacts {
  [cmdletBinding()]
  param (
    [Parameter(mandatory=$false)]
    $factpath = $null
  )

  if (-not (Test-Path -Path $factpath)) {
    Fail-Json $result "The path $factpath does not exist. Typo?"
  }

  $FactsFiles = Get-ChildItem -Path $factpath | Where-Object -FilterScript {($PSItem.PSIsContainer -eq $false) -and ($PSItem.Extension -eq '.ps1')}

  foreach ($FactsFile in $FactsFiles) {
      $out = & $($FactsFile.FullName)
      Set-Attr $result.ansible_facts "ansible_$(($FactsFile.Name).Split('.')[0])" $out
  }
}

$result = New-Object psobject @{
    ansible_facts = New-Object psobject
    changed = $false
};

# failifempty = $false is default and thus implied
$factpath = Get-AnsibleParam -obj $params -name fact_path
if ($factpath -ne $null) {
  # Get any custom facts
  Get-CustomFacts -factpath $factpath
}

$win32_os = Get-CimInstance Win32_OperatingSystem
$win32_cs = Get-CimInstance Win32_ComputerSystem
$win32_bios = Get-CimInstance Win32_Bios
$win32_cpu = Get-CimInstance Win32_Processor
If ($win32_cpu -is [array]) { # multi-socket, pick first
    $win32_cpu = $win32_cpu[0]
}

$ip_props = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
$osversion = [Environment]::OSVersion
$user = [Security.Principal.WindowsIdentity]::GetCurrent()
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

$cpu_list = @( )
for ($i=1; $i -le ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors); $i++) {
    $cpu_list += $win32_cpu.Manufacturer
    $cpu_list += $win32_cpu.Name
}

Set-Attr $result.ansible_facts "ansible_interfaces" $formattednetcfg

Set-Attr $result.ansible_facts "ansible_architecture" $win32_os.OSArchitecture

Set-Attr $result.ansible_facts "ansible_bios_date" $win32_bios.ReleaseDate.ToString("MM/dd/yyyy")
Set-Attr $result.ansible_facts "ansible_bios_version" $win32_bios.SMBIOSBIOSVersion
Set-Attr $result.ansible_facts "ansible_hostname" $env:COMPUTERNAME
Set-Attr $result.ansible_facts "ansible_fqdn" ($ip_props.Hostname + "." + $ip_props.DomainName)
Set-Attr $result.ansible_facts "ansible_processor" $cpu_list
Set-Attr $result.ansible_facts "ansible_processor_cores" $win32_cpu.NumberOfCores
Set-Attr $result.ansible_facts "ansible_processor_count" $win32_cs.NumberOfProcessors
Set-Attr $result.ansible_facts "ansible_processor_threads_per_core" ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors / $win32_cpu.NumberOfCores)
Set-Attr $result.ansible_facts "ansible_processor_vcpus" ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors)
Set-Attr $result.ansible_facts "ansible_product_name" $win32_cs.Model.Trim()
Set-Attr $result.ansible_facts "ansible_product_serial" $win32_bios.SerialNumber
#Set-Attr $result.ansible_facts "ansible_product_version" ([string] $win32_cs.SystemFamily)
Set-Attr $result.ansible_facts "ansible_system" $osversion.Platform.ToString()
Set-Attr $result.ansible_facts "ansible_system_description" ([string] $win32_os.Description)
Set-Attr $result.ansible_facts "ansible_system_vendor" $win32_cs.Manufacturer
Set-Attr $result.ansible_facts "ansible_os_family" "Windows"
Set-Attr $result.ansible_facts "ansible_os_name" ($win32_os.Name.Split('|')[0]).Trim()
Set-Attr $result.ansible_facts "ansible_distribution" $win32_os.Caption
Set-Attr $result.ansible_facts "ansible_distribution_version" $osversion.Version.ToString()
Set-Attr $result.ansible_facts "ansible_distribution_major_version" $osversion.Version.Major.ToString()
Set-Attr $result.ansible_facts "ansible_kernel" $osversion.Version.ToString()

Set-Attr $result.ansible_facts "ansible_machine_id" $user.User.AccountDomainSid.Value
Set-Attr $result.ansible_facts "ansible_domain" $ip_props.DomainName
Set-Attr $result.ansible_facts "ansible_nodename" ($ip_props.HostName + "." + $ip_props.DomainName)
Set-Attr $result.ansible_facts "ansible_windows_domain" $win32_cs.Domain

Set-Attr $result.ansible_facts "ansible_owner_name" ([string] $win32_cs.PrimaryOwnerName)
Set-Attr $result.ansible_facts "ansible_owner_contact" ([string] $win32_cs.PrimaryOwnerContact)

Set-Attr $result.ansible_facts "ansible_user_dir" $env:userprofile
Set-Attr $result.ansible_facts "ansible_user_gecos" "" # Win32_UserAccount.FullName is probably the right thing here, but it can be expensive to get on large domains
Set-Attr $result.ansible_facts "ansible_user_id" $env:username
Set-Attr $result.ansible_facts "ansible_user_uid" ([int] $user.User.Value.Substring(42))
Set-Attr $result.ansible_facts "ansible_user_sid" $user.User.Value

$date = New-Object psobject
$datetime = (Get-Date)
$datetime_utc = $datetime.ToUniversalTime()
Set-Attr $date "date" $datetime.ToString("yyyy-MM-dd")
Set-Attr $date "day" $datetime.ToString("dd")
Set-Attr $date "epoch" (Get-Date -UFormat "%s")
Set-Attr $date "hour" $datetime.ToString("HH")
Set-Attr $date "iso8601" $datetime_utc.ToString("yyyy-MM-ddTHH:mm:ssZ")
Set-Attr $date "iso8601_basic" $datetime.ToString("yyyyMMddTHHmmssffffff")
Set-Attr $date "iso8601_basic_short" $datetime.ToString("yyyyMMddTHHmmss")
Set-Attr $date "iso8601_micro" $datetime_utc.ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
Set-Attr $date "minute" $datetime.ToString("mm")
Set-Attr $date "month" $datetime.ToString("MM")
Set-Attr $date "second" $datetime.ToString("ss")
Set-Attr $date "time" $datetime.ToString("HH:mm:ss")
Set-Attr $date "tz_offset" $datetime.ToString("zzzz")
Set-Attr $date "tz" ([System.TimeZoneInfo]::Local.Id)
# Ensure that the weekday is in English
Set-Attr $date "weekday" $datetime.ToString("dddd", [System.Globalization.CultureInfo]::InvariantCulture)
Set-Attr $date "weekday_number" (Get-Date -UFormat "%w")
Set-Attr $date "weeknumber" (Get-Date -UFormat "%W")
Set-Attr $date "year" $datetime.ToString("yyyy")
Set-Attr $result.ansible_facts "ansible_date_time" $date

# Win32_PhysicalMemory is empty on some virtual platforms
Set-Attr $result.ansible_facts "ansible_memtotal_mb" ([math]::round($win32_cs.TotalPhysicalMemory / 1024 / 1024))
Set-Attr $result.ansible_facts "ansible_swaptotal_mb" ([math]::round($win32_os.TotalSwapSpaceSize / 1024 / 1024))

Set-Attr $result.ansible_facts "ansible_lastboot" $win32_os.lastbootuptime.ToString("u")
Set-Attr $result.ansible_facts "ansible_uptime_seconds" $([System.Convert]::ToInt64($(Get-Date).Subtract($win32_os.lastbootuptime).TotalSeconds))

$ips = @()
Foreach ($ip in $netcfg.IPAddress) { If ($ip) { $ips += $ip } }
Set-Attr $result.ansible_facts "ansible_ip_addresses" $ips

$env_vars = New-Object psobject
foreach ($item in Get-ChildItem Env:)
{
    $name = $item | select -ExpandProperty Name
    # Powershell ConvertTo-Json fails if string ends with \
    $value = ($item | select -ExpandProperty Value).TrimEnd("\")
    Set-Attr $env_vars $name $value
}
Set-Attr $result.ansible_facts "ansible_env" $env_vars

$psversion = $PSVersionTable.PSVersion.Major
Set-Attr $result.ansible_facts "ansible_powershell_version" $psversion

$winrm_https_listener_parent_path = Get-ChildItem -Path WSMan:\localhost\Listener -Recurse | Where-Object {$_.PSChildName -eq "Transport" -and $_.Value -eq "HTTPS"} | select PSParentPath
$winrm_https_listener_path = $null
$https_listener = $null
$winrm_cert_thumbprint = $null
$uppercase_cert_thumbprint = $null

if ($winrm_https_listener_parent_path ) {
    $winrm_https_listener_path = $winrm_https_listener_parent_path.PSParentPath.Substring($winrm_https_listener_parent_path.PSParentPath.LastIndexOf("\"))
}

if ($winrm_https_listener_path)
{
    $https_listener = Get-ChildItem -Path "WSMan:\localhost\Listener$winrm_https_listener_path"
}

if ($https_listener)
{
    $winrm_cert_thumbprint = $https_listener | where {$_.Name -EQ "CertificateThumbprint" } | select Value
}

if ($winrm_cert_thumbprint)
{
   $uppercase_cert_thumbprint = $winrm_cert_thumbprint.Value.ToString().ToUpper()
}

$winrm_cert_expiry = Get-ChildItem -Path Cert:\LocalMachine\My | where Thumbprint -EQ $uppercase_cert_thumbprint | select NotAfter

if ($winrm_cert_expiry)
{
    # this fact was renamed from ansible_winrm_certificate_expires due to collision with ansible_winrm_X connection var pattern
    Set-Attr $result.ansible_facts "ansible_win_rm_certificate_expires" $winrm_cert_expiry.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
}

$PendingReboot = Get-PendingRebootStatus
Set-Attr $result.ansible_facts "ansible_reboot_pending" $PendingReboot

Set-Attr $result.ansible_facts "module_setup" $true

# See if Facter is on the System Path
Try {
    $facter_exe = Get-Command facter -ErrorAction Stop
    $facter_installed = $true
}
Catch {
    $facter_installed = $false
}

# Get JSON from Facter, and parse it out.
if ($facter_installed) {
    &facter -j | Tee-Object  -Variable facter_output | Out-Null
    $facts = "$facter_output" | ConvertFrom-Json
    ForEach($fact in $facts.PSObject.Properties) {
        $fact_name = $fact.Name
        Set-Attr $result.ansible_facts "facter_$fact_name" $fact.Value
    }
}

Exit-Json $result;
