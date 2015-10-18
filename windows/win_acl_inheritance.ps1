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
$copy = Get-Attr $params "copy" "no" -validateSet "no","yes" -resultobj $result

If (-Not (Test-Path -Path $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}
 
Try {
    $objACL = Get-ACL $path
    $alreadyDisabled = !$objACL.AreAccessRulesProtected

    If ($copy -eq "yes") {
        $objACL.SetAccessRuleProtection($True, $True)
    } Else {
        $objACL.SetAccessRuleProtection($True, $False)
    }

    If ($alreadyDisabled) {
        Set-Attr $result "changed" $true;
    }

    Set-ACL $path $objACL
}
Catch {
    Fail-Json $result "an error occured when attempting to disable inheritance"
}
 
Exit-Json $result
