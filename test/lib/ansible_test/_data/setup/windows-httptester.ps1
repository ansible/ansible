<#
.SYNOPSIS
Designed to set a Windows host to connect to the httptester container running
on the Ansible host. This will setup the Windows host file and forward the
local ports to use this connection. This will continue to run in the background
until the script is deleted.

Run this with SSH with the -R arguments to forward ports 8080, 8443 and 8444 to the
httptester container.

.PARAMETER Hosts
A list of hostnames, delimited by '|', to add to the Windows hosts file for the
httptester container, e.g. 'ansible.host.com|secondary.host.test'.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)][String]$Hosts
)
$Hosts = $Hosts.Split('|')

$ProgressPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"
$os_version = [Version](Get-Item -Path "$env:SystemRoot\System32\kernel32.dll").VersionInfo.ProductVersion
Write-Verbose -Message "Configuring HTTP Tester on Windows $os_version for '$($Hosts -join "', '")'"

Function Get-PmapperRuleBytes {
    <#
    .SYNOPSIS
    Create the byte values that configures a rule in the PMapper configuration
    file. This isn't really documented but because PMapper is only used for
    Server 2008 R2 we will stick to 1 version and just live with the legacy
    work for now.

    .PARAMETER ListenPort
    The port to listen on localhost, this will be forwarded to the host defined
    by ConnectAddress and ConnectPort.

    .PARAMETER ConnectAddress
    The hostname or IP to map the traffic to.

    .PARAMETER ConnectPort
    This port of ConnectAddress to map the traffic to.
    #>
    param(
        [Parameter(Mandatory=$true)][UInt16]$ListenPort,
        [Parameter(Mandatory=$true)][String]$ConnectAddress,
        [Parameter(Mandatory=$true)][Int]$ConnectPort
    )

    $connect_field = "$($ConnectAddress):$ConnectPort"
    $connect_bytes = [System.Text.Encoding]::ASCII.GetBytes($connect_field)
    $data_length = [byte]($connect_bytes.Length + 6) # size of payload minus header, length, and footer
    $port_bytes = [System.BitConverter]::GetBytes($ListenPort)

    $payload = [System.Collections.Generic.List`1[Byte]]@()
    $payload.Add([byte]16) > $null # header is \x10, means Configure Mapping rule
    $payload.Add($data_length) > $null
    $payload.AddRange($connect_bytes)
    $payload.AddRange($port_bytes)
    $payload.AddRange([byte[]]@(0, 0)) # 2 extra bytes of padding
    $payload.Add([byte]0) > $null # 0 is TCP, 1 is UDP
    $payload.Add([byte]0) > $null # 0 is Any, 1 is Internet
    $payload.Add([byte]31) > $null # footer is \x1f, means end of Configure Mapping rule

    return ,$payload.ToArray()
}

Write-Verbose -Message "Adding host file entries"
$hosts_file = "$env:SystemRoot\System32\drivers\etc\hosts"
$hosts_file_lines = [System.IO.File]::ReadAllLines($hosts_file)
$changed = $false
foreach ($httptester_host in $Hosts) {
    $host_line = "127.0.0.1 $httptester_host # ansible-test httptester"
    if ($host_line -notin $hosts_file_lines) {
        $hosts_file_lines += $host_line
        $changed = $true
    }
}
if ($changed) {
    Write-Verbose -Message "Host file is missing entries, adding missing entries"
    [System.IO.File]::WriteAllLines($hosts_file, $hosts_file_lines)
}

# forward ports
$forwarded_ports = @{
    80 = 8080
    443 = 8443
    444 = 8444
}
if ($os_version -ge [Version]"6.2") {
    Write-Verbose -Message "Using netsh to configure forwarded ports"
    foreach ($forwarded_port in $forwarded_ports.GetEnumerator()) {
        $port_set = netsh interface portproxy show v4tov4 | `
            Where-Object { $_ -match "127.0.0.1\s*$($forwarded_port.Key)\s*127.0.0.1\s*$($forwarded_port.Value)" }

        if (-not $port_set) {
            Write-Verbose -Message "Adding netsh portproxy rule for $($forwarded_port.Key) -> $($forwarded_port.Value)"
            $add_args = @(
                "interface",
                "portproxy",
                "add",
                "v4tov4",
                "listenaddress=127.0.0.1",
                "listenport=$($forwarded_port.Key)",
                "connectaddress=127.0.0.1",
                "connectport=$($forwarded_port.Value)"
            )
            $null = netsh $add_args 2>&1
        }
    }
} else {
    Write-Verbose -Message "Using Port Mapper to configure forwarded ports"
    # netsh interface portproxy doesn't work on local addresses in older
    # versions of Windows. Use custom application Port Mapper to acheive the
    # same outcome
    # http://www.analogx.com/contents/download/Network/pmapper/Freeware.htm
    $s3_url = "https://ansible-ci-files.s3.amazonaws.com/ansible-test/pmapper-1.04.exe"

    # download the Port Mapper executable to a temporary directory
    $pmapper_folder = Join-Path -Path ([System.IO.Path]::GetTempPath()) -ChildPath ([System.IO.Path]::GetRandomFileName())
    $pmapper_exe = Join-Path -Path $pmapper_folder -ChildPath pmapper.exe
    $pmapper_config = Join-Path -Path $pmapper_folder -ChildPath pmapper.dat
    New-Item -Path $pmapper_folder -ItemType Directory > $null

    $stop = $false
    do {
        try {
            Write-Verbose -Message "Attempting download of '$s3_url'"
            (New-Object -TypeName System.Net.WebClient).DownloadFile($s3_url, $pmapper_exe)
            $stop = $true
        } catch { Start-Sleep -Second 5 }
    } until ($stop)

    # create the Port Mapper rule file that contains our forwarded ports
    $fs = [System.IO.File]::Create($pmapper_config)
    try {
        foreach ($forwarded_port in $forwarded_ports.GetEnumerator()) {
            Write-Verbose -Message "Creating forwarded port rule for $($forwarded_port.Key) -> $($forwarded_port.Value)"
            $pmapper_rule = Get-PmapperRuleBytes -ListenPort $forwarded_port.Key -ConnectAddress 127.0.0.1 -ConnectPort $forwarded_port.Value
            $fs.Write($pmapper_rule, 0, $pmapper_rule.Length)
        }
    } finally {
        $fs.Close()
    }

    Write-Verbose -Message "Starting Port Mapper '$pmapper_exe' in the background"
    $start_args = @{
        CommandLine = $pmapper_exe
        CurrentDirectory = $pmapper_folder
    }
    $res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments $start_args
    if ($res.ReturnValue -ne 0) {
        $error_msg = switch($res.ReturnValue) {
            2 { "Access denied" }
            3 { "Insufficient privilege" }
            8 { "Unknown failure" }
            9 { "Path not found" }
            21 { "Invalid parameter" }
            default { "Undefined Error: $($res.ReturnValue)" }
        }
        Write-Error -Message "Failed to start pmapper: $error_msg"
    }
    $pmapper_pid = $res.ProcessId
    Write-Verbose -Message "Port Mapper PID: $pmapper_pid"
}

Write-Verbose -Message "Wait for current script at '$PSCommandPath' to be deleted before running cleanup"
$fsw = New-Object -TypeName System.IO.FileSystemWatcher
$fsw.Path = Split-Path -Path $PSCommandPath -Parent
$fsw.Filter = Split-Path -Path $PSCommandPath -Leaf
$fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Deleted, 3600000) > $null
Write-Verbose -Message "Script delete or timeout reached, cleaning up Windows httptester artifacts"

Write-Verbose -Message "Cleanup host file entries"
$hosts_file_lines = [System.IO.File]::ReadAllLines($hosts_file)
$new_lines = [System.Collections.ArrayList]@()
$changed = $false
foreach ($host_line in $hosts_file_lines) {
    if ($host_line.EndsWith("# ansible-test httptester")) {
        $changed = $true
        continue
    }
    $new_lines.Add($host_line) > $null
}
if ($changed) {
    Write-Verbose -Message "Host file has extra entries, removing extra entries"
    [System.IO.File]::WriteAllLines($hosts_file, $new_lines)
}

if ($os_version -ge [Version]"6.2") {
    Write-Verbose -Message "Cleanup of forwarded port configured in netsh"
    foreach ($forwarded_port in $forwarded_ports.GetEnumerator()) {
        $port_set = netsh interface portproxy show v4tov4 | `
            Where-Object { $_ -match "127.0.0.1\s*$($forwarded_port.Key)\s*127.0.0.1\s*$($forwarded_port.Value)" }

        if ($port_set) {
            Write-Verbose -Message "Removing netsh portproxy rule for $($forwarded_port.Key) -> $($forwarded_port.Value)"
            $delete_args = @(
                "interface",
                "portproxy",
                "delete",
                "v4tov4",
                "listenaddress=127.0.0.1",
                "listenport=$($forwarded_port.Key)"
            )
            $null = netsh $delete_args 2>&1
        }
    }
} else {
    Write-Verbose -Message "Stopping Port Mapper executable based on pid $pmapper_pid"
    Stop-Process -Id $pmapper_pid -Force

    # the process may not stop straight away, try multiple times to delete the Port Mapper folder
    $attempts = 1
    do {
        try {
            Write-Verbose -Message "Cleanup temporary files for Port Mapper at '$pmapper_folder' - Attempt: $attempts"
            Remove-Item -Path $pmapper_folder -Force -Recurse
            break
        } catch {
            Write-Verbose -Message "Cleanup temporary files for Port Mapper failed, waiting 5 seconds before trying again:$($_ | Out-String)"
            if ($attempts -ge 5) {
                break
            }
            $attempts += 1
            Start-Sleep -Second 5
        }
    } until ($true)
}
