#!powershell
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "string" -default "imported" -validateset "imported","exported"
$mountpath = Get-AnsibleParam -obj $params -name "mountpath" -type "path"

$result = @{
    changed = $false
}

if ($state -eq "imported") {

    if (-not $mountpath) {
        Fail-Json -obj $result -message "Parameter 'mountpath' is required when 'state=imported'."
    }

    # FIXME: Can we do this more dynamic ?
    try {
        if ($has_filetype_support) {
            Export-StartLayout -LiteralPath "$($path).orig" -As XML -WhatIf:$check_mode
        } else {
            Export-StartLayout -LiteralPath "$($path).orig" -WhatIf:$check_mode
        }
    } catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }

    # Test if there would be a change
    If ($(Get-FileChecksum -path $path) -ne $(Get-FileChecksum -path "$($path).orig")) {
        try {
            Import-StartLayout -LayoutPath $path -MountPath $mountpath -WhatIf:$check_mode
        } catch {
            Fail-Json -obj $result -message $_.Exception.Message
        }
        $result.changed = $true
    }

} elseif ($state -eq "exported") {

    $checksum_orig = (Get-FileChecksum -path $path)

    # FIXME: Can we do this more dynamic ?
    try {
        if ($has_filetype_support) {
            Export-StartLayout -LiteralPath $path -As XML -WhatIf:$check_mode
        } else {
            Export-StartLayout -LiteralPath $path -WhatIf:$check_mode
        }
    } catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }

    # Test if there was a change
    if ($(Get-FileChecksum -path $path) -ne $checksum_orig) {
        $result.changed = $true
    }

}

Exit-Json $result
