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
      $result.ansible_facts.Add("ansible_$(($FactsFile.Name).Split('.')[0])", $out)
  }
}

$result = @{
    ansible_facts = @{ }
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$factpath = Get-AnsibleParam -obj $params -name "fact_path" -type "path"

if ($factpath -ne $null) {
    # Get any custom facts
    Get-CustomFacts -factpath $factpath
}

$win32_os = Get-CimInstance Win32_OperatingSystem
$win32_cs = Get-CimInstance Win32_ComputerSystem
$win32_bios = Get-CimInstance Win32_Bios
$win32_cpu = Get-CimInstance Win32_Processor
if ($win32_cpu -is [array]) {
    # multi-socket, pick first
    $win32_cpu = $win32_cpu[0]
}

$ip_props = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
$osversion = [Environment]::OSVersion
$user = [Security.Principal.WindowsIdentity]::GetCurrent()
$netcfg = Get-WmiObject win32_NetworkAdapterConfiguration

$ActiveNetcfg = @()
$ActiveNetcfg += $netcfg | where {$_.ipaddress -ne $null}

$formattednetcfg = @()
foreach ($adapter in $ActiveNetcfg)
{
    $thisadapter = @{
        default_gateway = $null
        dns_domain = $adapter.dnsdomain
        interface_index = $adapter.InterfaceIndex
        interface_name = $adapter.description
        macaddress = $adapter.macaddress
    }

    if ($adapter.defaultIPGateway)
    {
        $thisadapter.default_gateway = $adapter.DefaultIPGateway[0].ToString()
    }

    $formattednetcfg += $thisadapter
}

$cpu_list = @( )
for ($i=1; $i -le ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors); $i++) {
    $cpu_list += $win32_cpu.Manufacturer
    $cpu_list += $win32_cpu.Name
}

$datetime = (Get-Date)
$datetime_utc = $datetime.ToUniversalTime()

$date = @{
    date = $datetime.ToString("yyyy-MM-dd")
    day = $datetime.ToString("dd")
    epoch = (Get-Date -UFormat "%s")
    hour = $datetime.ToString("HH")
    iso8601 = $datetime_utc.ToString("yyyy-MM-ddTHH:mm:ssZ")
    iso8601_basic = $datetime.ToString("yyyyMMddTHHmmssffffff")
    iso8601_basic_short = $datetime.ToString("yyyyMMddTHHmmss")
    iso8601_micro = $datetime_utc.ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
    minute = $datetime.ToString("mm")
    month = $datetime.ToString("MM")
    second = $datetime.ToString("ss")
    time = $datetime.ToString("HH:mm:ss")
    tz = ([System.TimeZoneInfo]::Local.Id)
    tz_offset = $datetime.ToString("zzzz")
    # Ensure that the weekday is in English
    weekday = $datetime.ToString("dddd", [System.Globalization.CultureInfo]::InvariantCulture)
    weekday_number = (Get-Date -UFormat "%w")
    weeknumber = (Get-Date -UFormat "%W")
    year = $datetime.ToString("yyyy")
}

$ips = @()
Foreach ($ip in $netcfg.IPAddress) {
    If ($ip) {
        $ips += $ip
    }
}

$env_vars = @{ }
foreach ($item in Get-ChildItem Env:) {
    $name = $item | select -ExpandProperty Name
    # Powershell ConvertTo-Json fails if string ends with \
    $value = ($item | select -ExpandProperty Value).TrimEnd("\")
    $env_vars.Add($name, $value)
}

$ansible_facts = @{
    ansible_architecture = $win32_os.OSArchitecture
    ansible_bios_date = $win32_bios.ReleaseDate.ToString("MM/dd/yyyy")
    ansible_bios_version = $win32_bios.SMBIOSBIOSVersion
    ansible_date_time = $date
    ansible_distribution = $win32_os.Caption
    ansible_distribution_version = $osversion.Version.ToString()
    ansible_distribution_major_version = $osversion.Version.Major.ToString()
    ansible_domain = $ip_props.DomainName
    ansible_env = $env_vars
    ansible_fqdn = ($ip_props.Hostname + "." + $ip_props.DomainName)
    ansible_hostname = $env:COMPUTERNAME
    ansible_interfaces = $formattednetcfg
    ansible_ip_addresses = $ips
    ansible_kernel = $osversion.Version.ToString()
    ansible_lastboot = $win32_os.lastbootuptime.ToString("u")
    ansible_machine_id = $user.User.AccountDomainSid.Value
    ansible_nodename = ($ip_props.HostName + "." + $ip_props.DomainName)
    ansible_os_family = "Windows"
    ansible_os_name = ($win32_os.Name.Split('|')[0]).Trim()
    ansible_owner_contact = ([string] $win32_cs.PrimaryOwnerContact)
    ansible_owner_name = ([string] $win32_cs.PrimaryOwnerName)
    ansible_powershell_version = ($PSVersionTable.PSVersion.Major)
    ansible_processor = $cpu_list
    ansible_processor_cores = $win32_cpu.NumberOfCores
    ansible_processor_count = $win32_cs.NumberOfProcessors
    ansible_processor_threads_per_core = ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors / $win32_cpu.NumberOfCores)
    ansible_processor_vcpus = ($win32_cpu.NumberOfLogicalProcessors / $win32_cs.NumberOfProcessors)
    ansible_product_name = $win32_cs.Model.Trim()
    ansible_product_serial = $win32_bios.SerialNumber
#    ansible_product_version = ([string] $win32_cs.SystemFamily)
    ansible_reboot_pending = (Get-PendingRebootStatus)
    ansible_system = $osversion.Platform.ToString()
    ansible_system_description = ([string] $win32_os.Description)
    ansible_system_vendor = $win32_cs.Manufacturer
    ansible_uptime_seconds = $([System.Convert]::ToInt64($(Get-Date).Subtract($win32_os.lastbootuptime).TotalSeconds))

    ansible_user_dir = $env:userprofile
    # Win32_UserAccount.FullName is probably the right thing here, but it can be expensive to get on large domains
    ansible_user_gecos = ""
    ansible_user_id = $env:username
    ansible_user_sid = $user.User.Value
    ansible_windows_domain = $win32_cs.Domain

    # Win32_PhysicalMemory is empty on some virtual platforms
    ansible_memtotal_mb = ([math]::round($win32_cs.TotalPhysicalMemory / 1024 / 1024))
    ansible_swaptotal_mb = ([math]::round($win32_os.TotalSwapSpaceSize / 1024 / 1024))

    module_setup = $true
}

$winrm_https_listener_parent_paths = Get-ChildItem -Path WSMan:\localhost\Listener -Recurse | Where-Object {$_.PSChildName -eq "Transport" -and $_.Value -eq "HTTPS"} | select PSParentPath
if ($winrm_https_listener_parent_paths -isnot [array]) {
   $winrm_https_listener_parent_paths = @($winrm_https_listener_parent_paths)
}

$winrm_https_listener_paths = @()
foreach ($winrm_https_listener_parent_path in $winrm_https_listener_parent_paths) {
    $winrm_https_listener_paths += $winrm_https_listener_parent_path.PSParentPath.Substring($winrm_https_listener_parent_path.PSParentPath.LastIndexOf("\"))
}

$https_listeners = @()
foreach ($winrm_https_listener_path in $winrm_https_listener_paths) {
    $https_listeners += Get-ChildItem -Path "WSMan:\localhost\Listener$winrm_https_listener_path"
}

$winrm_cert_thumbprints = @()
foreach ($https_listener in $https_listeners) {
    $winrm_cert_thumbprints += $https_listener | where {$_.Name -EQ "CertificateThumbprint" } | select Value
}

$winrm_cert_expiry = @()
foreach ($winrm_cert_thumbprint in $winrm_cert_thumbprints) {
    Try {
        $winrm_cert_expiry += Get-ChildItem -Path Cert:\LocalMachine\My | where Thumbprint -EQ $winrm_cert_thumbprint.Value.ToString().ToUpper() | select NotAfter
    } Catch {}
}

$winrm_cert_expirations = $winrm_cert_expiry | Sort-Object NotAfter
if ($winrm_cert_expirations) {
    # this fact was renamed from ansible_winrm_certificate_expires due to collision with ansible_winrm_X connection var pattern
    $ansible_facts.Add("ansible_win_rm_certificate_expires", $winrm_cert_expirations[0].NotAfter.ToString("yyyy-MM-dd HH:mm:ss"))
}

# See if Facter is on the System Path
Try {
    $facter_exe = Get-Command facter -ErrorAction Stop
    $facter_installed = $true
} Catch {
    $facter_installed = $false
}

# Get JSON from Facter, and parse it out.
if ($facter_installed) {
    &facter -j | Tee-Object  -Variable facter_output | Out-Null
    $facts = "$facter_output" | ConvertFrom-Json
    ForEach($fact in $facts.PSObject.Properties) {
        $fact_name = $fact.Name
        $ansible_facts.Add("facter_$fact_name", $fact.Value)
    }
}

$result.ansible_facts += $ansible_facts

Exit-Json $result
