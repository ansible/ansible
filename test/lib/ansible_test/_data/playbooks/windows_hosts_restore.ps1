<#
.SYNOPSIS
Remove one or more hosts entries from the Windows hosts file.

.PARAMETER Hosts
A list of hosts entries, delimited by '|'.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)][String]$Hosts
)

$ProgressPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"

Write-Verbose -Message "Removing host file entries"

$hosts_entries = $Hosts.Split('|')
$hosts_file = "$env:SystemRoot\System32\drivers\etc\hosts"
$hosts_file_lines = [System.IO.File]::ReadAllLines($hosts_file)
$changed = $false

$new_lines = [System.Collections.ArrayList]@()

foreach ($host_line in $hosts_file_lines) {
    if ($host_line -in $hosts_entries) {
        $changed = $true
    } else {
        $new_lines += $host_line
    }
}

if ($changed) {
    Write-Verbose -Message "Host file has extra entries, removing extra entries"
    [System.IO.File]::WriteAllLines($hosts_file, $new_lines)
}
