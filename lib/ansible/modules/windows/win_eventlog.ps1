#!powershell

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

function Get-EventLogDetail {
    <#
    .SYNOPSIS
    Get details of an event log, sources, and associated attributes.
    Used for comparison against passed-in option values to ensure idempotency.
    #>
    param(
        [String]$LogName
    )

    $log_details = @{}
    $log_details.name = $LogName
    $log_details.exists = $false
    $log = Get-EventLog -List | Where-Object {$_.Log -eq $LogName}

    if ($log) {
        $log_details.exists = $true
        $log_details.maximum_size_kb = $log.MaximumKilobytes
        $log_details.overflow_action = $log.OverflowAction.ToString()
        $log_details.retention_days = $log.MinimumRetentionDays
        $log_details.entries = $log.Entries.Count
        $log_details.sources = [Ordered]@{}

        # Retrieve existing sources and category/message/parameter file locations
        # Associating file locations and sources with logs can only be done from the registry

        $root_key = "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\{0}" -f $LogName
        $log_root = Get-ChildItem -Path $root_key

        foreach ($child in $log_root) {
            $source_name = $child.PSChildName
            $log_details.sources.$source_name = @{}
            $hash_cursor = $log_details.sources.$source_name

            $source_root = "{0}\{1}" -f $root_key, $source_name
            $resource_files = Get-ItemProperty -Path $source_root

            $hash_cursor.category_file = $resource_files.CategoryMessageFile
            $hash_cursor.message_file = $resource_files.EventMessageFile
            $hash_cursor.parameter_file = $resource_files.ParameterMessageFile
        }
    }

    return $log_details
}

function Test-SourceExistence {
    <#
    .SYNOPSIS
    Get information on a source's existence.
    Examine existence regarding the parent log it belongs to and its expected state.
    #>
    param(
        [String]$LogName,
        [String]$SourceName,
        [Switch]$NoLogShouldExist
    )

    $source_exists = [System.Diagnostics.EventLog]::SourceExists($SourceName)

    if ($source_exists -and $NoLogShouldExist) {
        Fail-Json -obj $result -message "Source $SourceName already exists and cannot be created"
    }
    elseif ($source_exists) {
        $source_log = [System.Diagnostics.EventLog]::LogNameFromSourceName($SourceName, ".")
        if ($source_log -ne $LogName) {
            Fail-Json -obj $result -message "Source $SourceName does not belong to log $LogName and cannot be modified"
        }
    }

    return $source_exists
}

function ConvertTo-MaximumSize {
    <#
    .SYNOPSIS
    Convert a string KB/MB/GB value to common bytes and KB representations.
    .NOTES
    Size must be between 64KB and 4GB and divisible by 64KB, as per the MaximumSize parameter of Limit-EventLog.
    #>
    param(
        [String]$Size
    )

    $parsed_size = @{
        bytes = $null
        KB = $null
    }

    $size_regex = "^\d+(\.\d+)?(KB|MB|GB)$"
    if ($Size -notmatch $size_regex) {
        Fail-Json -obj $result -message "Maximum size $Size is not properly specified"
    }

    $size_upper = $Size.ToUpper()
    $size_numeric = [Double]$Size.Substring(0, $Size.Length -2)

    if ($size_upper.EndsWith("GB")) {
        $size_bytes = $size_numeric * 1GB
    }
    elseif ($size_upper.EndsWith("MB")) {
        $size_bytes = $size_numeric * 1MB
    }
    elseif ($size_upper.EndsWith("KB")) {
        $size_bytes = $size_numeric * 1KB
    }

    if (($size_bytes -lt 64KB) -or ($size_bytes -ge 4GB)) {
        Fail-Json -obj $result -message "Maximum size must be between 64KB and 4GB"
    }
    elseif (($size_bytes % 64KB) -ne 0) {
        Fail-Json -obj $result -message "Maximum size must be divisible by 64KB"
    }

    $parsed_size.bytes = $size_bytes
    $parsed_size.KB = $size_bytes / 1KB
    return $parsed_size
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","clear","absent"
$sources = Get-AnsibleParam -obj $params -name "sources" -type "list"
$category_file = Get-AnsibleParam -obj $params -name "category_file" -type "path"
$message_file = Get-AnsibleParam -obj $params -name "message_file" -type "path"
$parameter_file = Get-AnsibleParam -obj $params -name "parameter_file" -type "path"
$maximum_size = Get-AnsibleParam -obj $params -name "maximum_size" -type "str"
$overflow_action = Get-AnsibleParam -obj $params -name "overflow_action" -type "str" -validateset "OverwriteOlder","OverwriteAsNeeded","DoNotOverwrite"
$retention_days = Get-AnsibleParam -obj $params -name "retention_days" -type "int"

$result = @{
    changed = $false
    name = $name
    sources_changed = @()
}

$log_details = Get-EventLogDetail -LogName $name

# Handle common error cases up front
if ($state -eq "present" -and !$log_details.exists -and !$sources) {
    # When creating a log, one or more sources must be passed
    Fail-Json -obj $result -message "You must specify one or more sources when creating a log for the first time"
}
elseif ($state -eq "present" -and $log_details.exists -and $name -in $sources -and ($category_file -or $message_file -or $parameter_file)) {
    # After a default source of the same name is created, it cannot be modified without removing the log
    Fail-Json -obj $result -message "Cannot modify default source $name of log $name - you must remove the log"
}
elseif ($state -eq "clear" -and !$log_details.exists) {
    Fail-Json -obj $result -message "Cannot clear log $name as it does not exist"
}
elseif ($state -eq "absent" -and $name -in $sources) {
    # You also cannot remove a default source for the log - you must remove the log itself
    Fail-Json -obj $result -message "Cannot remove default source $name from log $name - you must remove the log"
}

try {
    switch ($state) {
        "present" {
            foreach ($source in $sources) {
                if ($log_details.exists) {
                    $source_exists = Test-SourceExistence -LogName $name -SourceName $source
                }
                else {
                    $source_exists = Test-SourceExistence -LogName $name -SourceName $source -NoLogShouldExist
                }

                if ($source_exists) {
                    $category_change = $category_file -and $log_details.sources.$source.category_file -ne $category_file
                    $message_change = $message_file -and $log_details.sources.$source.message_file -ne $message_file
                    $parameter_change = $parameter_file -and $log_details.sources.$source.parameter_file -ne $parameter_file
                    # Remove source and recreate later if any of the above are true
                    if ($category_change -or $message_change -or $parameter_change) {
                        Remove-EventLog -Source $source -WhatIf:$check_mode
                    }
                    else {
                        continue
                    }
                }

                $new_params = @{
                    LogName = $name
                    Source = $source
                }
                if ($category_file) {
                    $new_params.CategoryResourceFile = $category_file
                }
                if ($message_file) {
                    $new_params.MessageResourceFile = $message_file
                }
                if ($parameter_file) {
                    $new_params.ParameterResourceFile = $parameter_file
                }

                if (!$check_mode) {
                    New-EventLog @new_params
                    $result.sources_changed += $source
                }
                $result.changed = $true
            }

            if ($maximum_size) {
                $converted_size = ConvertTo-MaximumSize -Size $maximum_size
            }

            $size_change = $maximum_size -and $log_details.maximum_size_kb -ne $converted_size.KB
            $overflow_change = $overflow_action -and $log_details.overflow_action -ne $overflow_action
            $retention_change = $retention_days -and $log_details.retention_days -ne $retention_days

            if ($size_change -or $overflow_change -or $retention_change) {
                $limit_params = @{
                    LogName = $name
                    WhatIf = $check_mode
                }
                if ($maximum_size) {
                    $limit_params.MaximumSize = $converted_size.bytes
                }
                if ($overflow_action) {
                    $limit_params.OverflowAction = $overflow_action
                }
                if ($retention_days) {
                    $limit_params.RetentionDays = $retention_days
                }

                Limit-EventLog @limit_params
                $result.changed = $true
            }

        }
        "clear" {
            if ($log_details.entries -gt 0) {
                Clear-EventLog -LogName $name -WhatIf:$check_mode
                $result.changed = $true
            }
        }
        "absent" {
            if ($sources -and $log_details.exists) {
                # Since sources were passed, remove sources tied to event log
                foreach ($source in $sources) {
                    $source_exists = Test-SourceExistence -LogName $name -SourceName $source
                    if ($source_exists) {
                        Remove-EventLog -Source $source -WhatIf:$check_mode
                        if (!$check_mode) {
                            $result.sources_changed += $source
                        }
                        $result.changed = $true
                    }
                }
            }
            elseif ($log_details.exists) {
                # Only name passed, so remove event log itself (which also removes contained sources)
                Remove-EventLog -LogName $name -WhatIf:$check_mode
                if (!$check_mode) {
                    $log_details.sources.GetEnumerator() | ForEach-Object { $result.sources_changed += $_.Name }
                }
                $result.changed = $true
            }
        }
    }
}
catch {
    Fail-Json -obj $result -message $_.Exception.Message
}

$final_log_details = Get-EventLogDetail -LogName $name
foreach ($final_log_detail in $final_log_details.GetEnumerator()) {
    if ($final_log_detail.Name -eq "sources") {
        $sources = @()
        $final_log_detail.Value.GetEnumerator() | ForEach-Object { $sources += $_.Name }
        $result.$($final_log_detail.Name) = [Array]$sources
    }
    else {
        $result.$($final_log_detail.Name) = $final_log_detail.Value
    }
}

Exit-Json -obj $result
