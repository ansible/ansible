#!powershell

# (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# Test module used to grab the latest entry from an event log and output its properties

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$log = Get-AnsibleParam -obj $params -name "log" -type "str" -failifempty $true

$result = @{
    changed = $false
}

try {
    $log_entry = Get-EventLog -LogName $log | Select-Object -First 1 -Property *
}
catch {
    Fail-Json -obj $result -message "Could not find any entries for log $log"
}

$result.source = $log_entry.Source
$result.event_id = $log_entry.EventID
$result.message = $log_entry.Message
$result.entry_type = $log_entry.EntryType.ToString()
$result.category = $log_entry.CategoryNumber
$result.raw_data = $log_entry.Data -join ","

Exit-Json -obj $result
