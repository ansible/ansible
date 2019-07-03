#!powershell

# Copyright: (c) 2019, Aameer Raza <mail2aameer@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2.0


$params = Parse-Args $args -supports_check_mode $true
$Source = Get-AnsibleParam -obj $params -name "src" -type "str" -failifempty $true
$Destination = Get-AnsibleParam -obj $params -name "dist" -type "str" -failifempty $true
$SrcPath = Get-AnsibleParam -obj $params -name "src_path" -type "str" -failifempty $true
$DestPath = Get-AnsibleParam -obj $params -name "dest_path" -type "str" -failifempty $true
$Flow = Get-AnsibleParam -obj $params -name "flow" -type "str" -default "W2L" -validateset "W2L", "L2W" -failifempty $true
$LinuxUser = Get-AnsibleParam -obj $params -name "usr" -type "str" -failifempty $true
$LinuxPass = Get-AnsibleParam -obj $params -name "pass" -type "str" -failifempty $true



$result = @{
    changed = $false
    rc      = 0
    msg     = ""    
}
$ErrorActionPreference = "SilentlyContinue"

if ($Flow -eq "W2L") {
    $Statement = $LinuxUser + "@" + $Destination + ":" + $DestPath
    $output = Write-Output 'n' | pscp -pw "$LinuxPass" -r "$SrcPath" "$Statement" 
    if ($LASTEXITCODE -eq 0) {
        $result.msg = $output
        $result.rc = $LASTEXITCODE
        $result.changed = $true
    }
    else {
        $result.msg = $output
        $result.rc = $LASTEXITCODE
        $result.changed = $false
        Fail-Json -obj $Result "Exception occured: $Error" #return the JSON object
    }
}
elseif ($Flow -eq "L2W") {
    $Statement = $LinuxUser + "@" + $Source + ":" + $SrcPath
    $output = Write-Output 'n' | pscp -pw "$LinuxPass" -r "$Statement" "$DestPath"
    if ($LASTEXITCODE -eq 0) {
        $result.msg = $output
        $result.rc = $LASTEXITCODE
        $result.changed = $true
    }
    else {
        $result.msg = $output
        $result.rc = $LASTEXITCODE
        $result.changed = $false
        Fail-Json -obj $Result "Exception occured: $Error" #return the JSON object
    }
}

Exit-Json -obj $Result #return the JSON object