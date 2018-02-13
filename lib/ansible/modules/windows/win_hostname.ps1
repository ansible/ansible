#!powershell
# Copyright: (c) 2018, Ripon Banik (@riponbanik)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Requires -Module Ansible.ModuleUtils.Legacy

########

function Get-ComputerName() {
    Get-Content env:computername
    return
}

function Set-ComputerName($newComputerName) {
    $systemInfo = Get-WmiObject Win32_ComputerSystem
    $cmdResult = $systemInfo.Rename($newComputerName)    
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


$result = New-Object psobject @{
    changed = $false
};

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name"
}

$newComputerName = Get-Attr $params "name"
$currentComputerName = (Get-ComputerName)

if ($check_mode) {
  $result.msg = "Running in check mode - would change computer name to $newComputerName from $currentComputerName"  
}
if (-not $check_mode) {
    if ($newComputerName -ne $currentComputerName) {
        $setResult = (Set-ComputerName($newComputerName))
        $result.changed = $true
        $result.rc = $setResult
        # Set-Attr $result "user" $user_obj
        Set-Attr $result "computer_name" $newComputerName
    }   
   
}

Exit-Json $result;
