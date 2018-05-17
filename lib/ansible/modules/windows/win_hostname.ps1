#!powershell
# Copyright: (c) 2018, Ripon Banik (@riponbanik)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Requires -Module Ansible.ModuleUtils.Legacy

########

function Set-ComputerName($newComputerName) {
    $cmdResult = Rename-computer $newComputerName    
    if ($cmdResult.ReturnValue -ne 0) {         
        Fail-Json $result "The computer name could not be set. Check that it is a valid name."                
    }
    return $cmdResult.ReturnValue
}

########

$params = Parse-Args $args -supports_check_mode $true;
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false


$result = @{
 changed = $false
};

$newComputerName = Get-Attr $params "name"
$currentComputerName = $env:computername

if ($check_mode) {
  $result.msg = "Rename-computer $newComputerName -WhatIf" 
}
if ($newComputerName -ine $currentComputerName) {
    Try {
        $rc = Rename-Computer -NewName $newComputerName -Force -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $result -message "Failed to rename computer to '$newComputerName': $($_.Exception.Message)"
    }
    if ($rc -ne 0) {
        Fail-Json -obj $result -message "Failed to rename computer to '$newComputerName', returns $rc"
    }
    $result.changed = $true
    $result.computer_name = $newComputerName
}

Exit-Json -obj $result
