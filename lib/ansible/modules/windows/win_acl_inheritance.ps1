#!powershell

# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$result = @{
    changed = $false
}

$path = Get-AnsibleParam -obj $params "path" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params "state" -type "str" -default "absent" -validateSet "present","absent" -resultobj $result
$reorganize = Get-AnsibleParam -obj $params "reorganize" -type "bool" -default $false -resultobj $result

If (-Not (Test-Path -LiteralPath $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}

Try {
    $objACL = Get-ACL -LiteralPath $path
    # AreAccessRulesProtected - $false if inheritance is set ,$true if inheritance is not set
    $inheritanceDisabled = $objACL.AreAccessRulesProtected

    If (($state -eq "present") -And $inheritanceDisabled) {
        # second parameter is ignored if first=$False
        $objACL.SetAccessRuleProtection($False, $False)

        If ($reorganize) {
            # it wont work without intermediate save, state would be the same
            Set-ACL -LiteralPath $path -AclObject $objACL -WhatIf:$check_mode
            $result.changed = $true
            $objACL = Get-ACL -LiteralPath $path

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

        Set-ACL -LiteralPath $path -AclObject $objACL -WhatIf:$check_mode
        $result.changed = $true
    } Elseif (($state -eq "absent") -And (-not $inheritanceDisabled)) {
        $objACL.SetAccessRuleProtection($True, $reorganize)
        Set-ACL -LiteralPath $path -AclObject $objACL -WhatIf:$check_mode
        $result.changed = $true
    }
} Catch {
    Fail-Json $result "an error occurred when attempting to disable inheritance: $($_.Exception.Message)"
}

Exit-Json $result
