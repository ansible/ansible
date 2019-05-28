#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true

$connect_timeout = Get-AnsibleParam -obj $params -name "connect_timeout" -type "int" -default 5
$delay = Get-AnsibleParam -obj $params -name "delay" -type "int"
$exclude_hosts = Get-AnsibleParam -obj $params -name "exclude_hosts" -type "list"
$hostname = Get-AnsibleParam -obj $params -name "host" -type "str" -default "127.0.0.1"
$path = Get-AnsibleParam -obj $params -name "path" -type "path"
$port = Get-AnsibleParam -obj $params -name "port" -type "int"
$search_regex = Get-AnsibleParam -obj $params -name "search_regex" -type "str"
$sleep = Get-AnsibleParam -obj $params -name "sleep" -type "int" -default 1
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "started" -validateset "present","started","stopped","absent","drained"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 300

$result = @{
    changed = $false
    elapsed = 0
}

# validate the input with the various options
if ($null -ne $port -and $null -ne $path) {
    Fail-Json $result "port and path parameter can not both be passed to win_wait_for"
}
if ($null -ne $exclude_hosts -and $state -ne "drained") {
    Fail-Json $result "exclude_hosts should only be with state=drained"
}
if ($null -ne $path) {
    if ($state -in @("stopped","drained")) {
        Fail-Json $result "state=$state should only be used for checking a port in the win_wait_for module"
    }

    if ($null -ne $exclude_hosts) {
        Fail-Json $result "exclude_hosts should only be used when checking a port and state=drained in the win_wait_for module"
    }
}

if ($null -ne $port) {
    if ($null -ne $search_regex) {
        Fail-Json $result "search_regex should by used when checking a string in a file in the win_wait_for module"
    }

    if ($null -ne $exclude_hosts -and $state -ne "drained") {
        Fail-Json $result "exclude_hosts should be used when state=drained in the win_wait_for module"
    }
}

Function Test-Port($hostname, $port) {
    $timeout = $connect_timeout * 1000
    $socket = New-Object -TypeName System.Net.Sockets.TcpClient
    $connect = $socket.BeginConnect($hostname, $port, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne($timeout, $false)

    if ($wait) {
        try {
            $socket.EndConnect($connect) | Out-Null
            $valid = $true
        } catch {
            $valid = $false
        }
    } else {
        $valid = $false
    }

    $socket.Close()
    $socket.Dispose()

    $valid
}

Function Get-PortConnections($hostname, $port) {
    $connections = @()

    $conn_info = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
    if ($hostname -eq "0.0.0.0") {
        $active_connections = $conn_info.GetActiveTcpConnections() | Where-Object { $_.LocalEndPoint.Port -eq $port }
    } else {
        $active_connections = $conn_info.GetActiveTcpConnections() | Where-Object { $_.LocalEndPoint.Address -eq $hostname -and $_.LocalEndPoint.Port -eq $port }
    }

    if ($null -ne $active_connections) {
        foreach ($active_connection in $active_connections) {
            $connections += $active_connection.RemoteEndPoint.Address
        }
    }

    $connections
}

$module_start = Get-Date

if ($null -ne $delay) {
    Start-Sleep -Seconds $delay
}

$attempts = 0
if ($null -eq $path -and $null -eq $port -and $state -ne "drained") {
    Start-Sleep -Seconds $timeout
} elseif ($null -ne $path) {
    if ($state -in @("present", "started")) {
        # check if the file exists or string exists in file
        $start_time = Get-Date
        $complete = $false
        while (((Get-Date) - $start_time).TotalSeconds -lt $timeout) {
            $attempts += 1
            if (Test-AnsiblePath -Path $path) {
                if ($null -eq $search_regex) {
                    $complete = $true
                    break
                } else {
                    $file_contents = Get-Content -Path $path -Raw
                    if ($file_contents -match $search_regex) {
                        $complete = $true
                        break
                    }
                }
            }
            Start-Sleep -Seconds $sleep
        }

        if ($complete -eq $false) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $result.wait_attempts = $attempts
            if ($null -eq $search_regex) {
                Fail-Json $result "timeout while waiting for file $path to be present"
            } else {
                Fail-Json $result "timeout while waiting for string regex $search_regex in file $path to match"
            }
        }
    } elseif ($state -in @("absent")) {
        # check if the file is deleted or string doesn't exist in file
        $start_time = Get-Date
        $complete = $false
        while (((Get-Date) - $start_time).TotalSeconds -lt $timeout) {
            $attempts += 1
            if (Test-AnsiblePath -Path $path) {
                if ($null -ne $search_regex) {
                    $file_contents = Get-Content -Path $path -Raw
                    if ($file_contents -notmatch $search_regex) {
                        $complete = $true
                        break
                    }
                }
            } else {
                $complete = $true
                break
            }

            Start-Sleep -Seconds $sleep
        }

        if ($complete -eq $false) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $result.wait_attempts = $attempts
            if ($null -eq $search_regex) {
                Fail-Json $result "timeout while waiting for file $path to be absent"
            } else {
                Fail-Json $result "timeout while waiting for string regex $search_regex in file $path to not match"
            }
        }
    }
} elseif ($null -ne $port) {
    if ($state -in @("started","present")) {
        # check that the port is online and is listening
        $start_time = Get-Date
        $complete = $false
        while (((Get-Date) - $start_time).TotalSeconds -lt $timeout) {
            $attempts += 1
            $port_result = Test-Port -hostname $hostname -port $port
            if ($port_result -eq $true) {
                $complete = $true
                break
            }

            Start-Sleep -Seconds $sleep
        }

        if ($complete -eq $false) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $result.wait_attempts = $attempts
            Fail-Json $result "timeout while waiting for $($hostname):$port to start listening"
        }
    } elseif ($state -in @("stopped","absent")) {
        # check that the port is offline and is not listening
        $start_time = Get-Date
        $complete = $false
        while (((Get-Date) - $start_time).TotalSeconds -lt $timeout) {
            $attempts += 1
            $port_result = Test-Port -hostname $hostname -port $port
            if ($port_result -eq $false) {
                $complete = $true
                break
            }

            Start-Sleep -Seconds $sleep
        }

        if ($complete -eq $false) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $result.wait_attempts = $attempts
            Fail-Json $result "timeout while waiting for $($hostname):$port to stop listening"
        }
    } elseif ($state -eq "drained") {
        # check that the local port is online but has no active connections
        $start_time = Get-Date
        $complete = $false
        while (((Get-Date) - $start_time).TotalSeconds -lt $timeout) {
            $attempts += 1
            $active_connections = Get-PortConnections -hostname $hostname -port $port
            if ($null -eq $active_connections) {
                $complete = $true
                break
            } elseif ($active_connections.Count -eq 0) {
                # no connections on port
                $complete = $true
                break
            } else {
                # there are listeners, check if we should ignore any hosts
                if ($null -ne $exclude_hosts) {
                    $connection_info = $active_connections
                    foreach ($exclude_host in $exclude_hosts) {
                        try {
                            $exclude_ips = [System.Net.Dns]::GetHostAddresses($exclude_host) | ForEach-Object { Write-Output $_.IPAddressToString }
                            $connection_info = $connection_info | Where-Object { $_ -notin $exclude_ips }
                        } catch {} # ignore invalid hostnames
                    }

                    if ($connection_info.Count -eq 0) {
                        $complete = $true
                        break
                    }
                }
            }

            Start-Sleep -Seconds $sleep
        }

        if ($complete -eq $false) {
            $result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $result.wait_attempts = $attempts
            Fail-Json $result "timeout while waiting for $($hostname):$port to drain"
        }
    }
}

$result.elapsed = ((Get-Date) - $module_start).TotalSeconds
$result.wait_attempts = $attempts

Exit-Json $result
