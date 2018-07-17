#!powershell

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

function Test-LogExistence {
    <#
    .SYNOPSIS
    Get information on a log's existence.
    #>
    param(
        [String]$LogName
    )

    $log_exists = $false
    $log = Get-EventLog -List | Where-Object {$_.Log -eq $LogName}
    if ($log) {
        $log_exists = $true
    }
    return $log_exists
}

function Test-SourceExistence {
    <#
    .SYNOPSIS
    Get information on a source's existence.
    #>
    param(
        [String]$LogName,
        [String]$SourceName
    )

    $source_exists = [System.Diagnostics.EventLog]::SourceExists($SourceName)

    if ($source_exists) {
        $source_log = [System.Diagnostics.EventLog]::LogNameFromSourceName($SourceName, ".")
        if ($source_log -ne $LogName) {
            Fail-Json -obj $result -message "Source $SourceName does not belong to log $LogName and cannot be written to"
        }
    }

    return $source_exists
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$log = Get-AnsibleParam -obj $params -name "log" -type "str" -failifempty $true
$source = Get-AnsibleParam -obj $params -name "source" -type "str" -failifempty $true
$event_id = Get-AnsibleParam -obj $params -name "event_id" -type "int" -failifempty $true
$message = Get-AnsibleParam -obj $params -name "message" -type "str" -failifempty $true
$entry_type = Get-AnsibleParam -obj $params -name "entry_type" -type "str" -validateset "Error","FailureAudit","Information","SuccessAudit","Warning"
$category = Get-AnsibleParam -obj $params -name "category" -type "int"
$raw_data = Get-AnsibleParam -obj $params -name "raw_data" -type "str"

$result = @{
    changed = $false
}

$log_exists = Test-LogExistence -LogName $log
if (!$log_exists) {
    Fail-Json -obj $result -message "Log $log does not exist and cannot be written to"
}

$source_exists = Test-SourceExistence -LogName $log -SourceName $source
if (!$source_exists) {
    Fail-Json -obj $result -message "Source $source does not exist"
}

if ($event_id -lt 0 -or $event_id -gt 65535) {
    Fail-Json -obj $result -message "Event ID must be between 0 and 65535"
}

$write_params = @{
    LogName = $log
    Source = $source
    EventId = $event_id
    Message = $message
}

try {
    if ($entry_type) {
        $write_params.EntryType = $entry_type
    }
    if ($category) {
        $write_params.Category = $category
    }
    if ($raw_data) {
        $write_params.RawData = [Byte[]]($raw_data -split ",")
    }

    if (!$check_mode) {
        Write-EventLog @write_params
    }
    $result.changed = $true
    $result.msg = "Entry added to log $log from source $source"
}
catch {
    Fail-Json -obj $result -message $_.Exception.Message
}

Exit-Json -obj $result
