<#
.SYNOPSIS
Add one or more hosts entries to the Windows hosts file.

.PARAMETER Hosts
A list of hosts entries, delimited by '|'.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)][String]$Hosts
)

$ProgressPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"

Write-Verbose -Message "Adding host file entries"

$hosts_entries = $Hosts.Split('|')
$hosts_file = "$env:SystemRoot\System32\drivers\etc\hosts"
$hosts_file_lines = [System.IO.File]::ReadAllLines($hosts_file)
$changed = $false

foreach ($entry in $hosts_entries) {
    if ($entry -notin $hosts_file_lines) {
        $hosts_file_lines += $entry
        $changed = $true
    }
}

if ($changed) {
    Write-Verbose -Message "Host file is missing entries, adding missing entries"
    [System.IO.File]::WriteAllLines($hosts_file, $hosts_file_lines)
}
