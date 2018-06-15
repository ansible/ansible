#!powershell
# Copyright: (c) 2018, Ripon Banik (@riponbanik)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$current_computer_name = $env:ComputerName
$result = @{
   changed = $false
   old_name = $current_computer_name
   reboot_required = $false
}

if ($name -ne $current_computer_name) {
    Try {
        Rename-Computer -NewName $name -Force -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $result -message "Failed to rename computer to '$name': $($_.Exception.Message)"
    }
    $result.changed = $true
    $result.reboot_required = $true
}

Exit-Json -obj $result
