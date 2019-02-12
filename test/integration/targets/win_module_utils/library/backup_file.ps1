#!powershell

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.Backup

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name '_ansible_check_mode' -type 'bool' -default $false
$path = Get-AnsibleParam -obj $params -name 'path' -type 'path' -aliases ['dest']


$result = @{
    backup_file = $null
    changed = $false
}

$result.backup_file = Backup-File $path -WhatIf:$check_mode

if ($result.backup_file) {
    $result.changed = $true
}

Exit-Json -obj $result
