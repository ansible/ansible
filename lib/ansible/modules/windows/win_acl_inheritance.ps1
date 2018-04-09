#!powershell
# This file is part of Ansible
#
# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$result = @{
    changed = $false
}

$path = Get-AnsibleParam -obj $params "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params "state" -type "str" -default "absent" -validateSet "present","absent" -resultobj $result
$reorganize = Get-AnsibleParam -obj $params "reorganize" -type "bool" -default $false -resultobj $result

If (-Not (Test-Path -Path $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}
 
Try {
    $objACL = Get-ACL -Path $path
    # AreAccessRulesProtected - $false if inheritance is set ,$true if inheritance is not set
    $inheritanceDisabled = $objACL.AreAccessRulesProtected

    If (($state -eq "present") -And $inheritanceDisabled) {
        # second parameter is ignored if first=$False
        $objACL.SetAccessRuleProtection($False, $False)

        If ($reorganize) {
            # it wont work without intermediate save, state would be the same
            Set-ACL -Path $path -AclObject $objACL -WhatIf:$check_mode
            $result.changed = $true
            $objACL = Get-ACL -Path $path

            # convert explicit ACE to inherited ACE
            ForEach($inheritedRule in $objACL.Access) {
                If (-not $inheritedRule.IsInherited) {
                    Continue
                }

                ForEach($explicitRrule in $objACL.Access) {
                    If ($explicitRrule.IsInherited) {
                        Continue
                    }

                    If (($inheritedRule.FileSystemRights -eq $explicitRrule.FileSystemRights) -And ($inheritedRule.AccessControlType -eq $explicitRrule.AccessControlType) -And ($inheritedRule.IdentityReference -eq $explicitRrule.IdentityReference) -And ($inheritedRule.InheritanceFlags -eq $explicitRrule.InheritanceFlags) -And ($inheritedRule.PropagationFlags -eq $explicitRrule.PropagationFlags)) {
                        $objACL.RemoveAccessRule($explicitRrule)
                    }
                }
            }
        }

        Set-ACL -Path $path -AclObject $objACL -WhatIf:$check_mode
        $result.changed = $true
    } Elseif (($state -eq "absent") -And (-not $inheritanceDisabled)) {
        $objACL.SetAccessRuleProtection($True, $reorganize)
        Set-ACL -Path $path -AclObject $objACL -WhatIf:$check_mode
        $result.changed = $true
    }
} Catch {
    Fail-Json $result "an error occurred when attempting to disable inheritance: $($_.Exception.Message)"
}
 
Exit-Json $result
