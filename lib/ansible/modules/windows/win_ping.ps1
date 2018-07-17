#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true

$data = Get-AnsibleParam -obj $params -name "data" -type "str" -default "pong"

if ($data -eq "crash") {
    throw "boom"
}

$result = @{
    changed = $false
    ping = $data
}

Exit-Json $result
