#!powershell

# Copyright: (c) 2014, Matt Martz <matt@sivel.net>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args  -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"
$extra_args = Get-AnsibleParam -obj $params -name "extra_args" -type "str" -default ""
$wait = Get-AnsibleParam -obj $params -name "wait" -type "bool" -default $false

$result = @{
    changed = $false
}

if (-not (Test-Path -Path $path)) {
    Fail-Json $result "The MSI file ($path) was not found."
}

if ($creates -and (Test-Path -Path $creates)) {
    Exit-Json $result "The 'creates' file or directory ($creates) already exists."
}

if ($removes -and -not (Test-Path -Path $removes)) {
    Exit-Json $result "The 'removes' file or directory ($removes) does not exist."
}

if (-not $check_mode) {

    $logfile = [IO.Path]::GetTempFileName()
    if ($state -eq "absent") {
        Start-Process -FilePath msiexec.exe -ArgumentList "/x `"$path`" /qn /log $logfile $extra_args" -Verb Runas -Wait:$wait
    } else {
        Start-Process -FilePath msiexec.exe -ArgumentList "/i `"$path`" /qn /log $logfile $extra_args" -Verb Runas -Wait:$wait
    }
    $result.log = Get-Content $logfile | Out-String
    Remove-Item $logfile

}

$result.changed = $true

Exit-Json $result
