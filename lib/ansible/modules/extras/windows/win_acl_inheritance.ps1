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


$params = Parse-Args $args;

$result = New-Object PSObject;
Set-Attr $result "changed" $false;

$path = Get-Attr $params "path" -failifempty $true
$state = Get-Attr $params "state" "absent" -validateSet "present","absent" -resultobj $result
$reorganize = Get-Attr $params "reorganize" "no" -validateSet "no","yes" -resultobj $result
$reorganize = $reorganize | ConvertTo-Bool

If (-Not (Test-Path -Path $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}
 
Try {
    $objACL = Get-ACL $path
    $inheritanceEnabled = !$objACL.AreAccessRulesProtected

    If (($state -eq "present") -And !$inheritanceEnabled) {
        # second parameter is ignored if first=$False
        $objACL.SetAccessRuleProtection($False, $False)

        If ($reorganize) {
            # it wont work without intermediate save, state would be the same
            Set-ACL $path $objACL
            $objACL = Get-ACL $path

            # convert explicit ACE to inherited ACE
            ForEach($inheritedRule in $objACL.Access) {
                If (!$inheritedRule.IsInherited) {
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

        Set-ACL $path $objACL
        Set-Attr $result "changed" $true;
    }
    Elseif (($state -eq "absent") -And $inheritanceEnabled) {
        If ($reorganize) {
            $objACL.SetAccessRuleProtection($True, $True)
        } Else {
            $objACL.SetAccessRuleProtection($True, $False)
        }

        Set-ACL $path $objACL
        Set-Attr $result "changed" $true;
    }
}
Catch {
    Fail-Json $result "an error occured when attempting to disable inheritance"
}
 
Exit-Json $result
