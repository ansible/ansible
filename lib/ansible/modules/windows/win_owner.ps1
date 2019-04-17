#!powershell

# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$result = @{
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$user = Get-AnsibleParam -obj $params -name "user" -type "str" -failifempty $true
$recurse = Get-AnsibleParam -obj $params -name "recurse" -type "bool" -default $false -resultobj $result

If (-Not (Test-Path -LiteralPath $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = Convert-ToSID -account_name $user
if (!$sid) {
    Fail-Json $result "$user is not a valid user or group on the host machine or domain"
}

Try {
    $objUser = New-Object System.Security.Principal.SecurityIdentifier($sid)

    $file = Get-Item -LiteralPath $path
    $acl = Get-Acl -LiteralPath $file.FullName

    If ($acl.getOwner([System.Security.Principal.SecurityIdentifier]) -ne $objUser) {
        $acl.setOwner($objUser)
        Set-Acl -LiteralPath $file.FullName -AclObject $acl -WhatIf:$check_mode
        $result.changed = $true
    }

    If ($recurse -and $file -is [System.IO.DirectoryInfo]) {
        # Get-ChildItem falls flat on pre PSv5 when dealing with complex path chars
        $files = $file.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
        ForEach($file in $files){
            $acl = Get-Acl -LiteralPath $file.FullName

            If ($acl.getOwner([System.Security.Principal.SecurityIdentifier]) -ne $objUser) {
                $acl.setOwner($objUser)
                Set-Acl -LiteralPath $file.FullName -AclObject $acl -WhatIf:$check_mode
                $result.changed = $true
            }
        }
    }
}
Catch {
    Fail-Json $result "an error occurred when attempting to change owner on $path for $($user): $($_.Exception.Message)"
}

Exit-Json $result
