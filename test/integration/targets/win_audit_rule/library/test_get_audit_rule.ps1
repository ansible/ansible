#!powershell

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$params = Parse-Args -arguments $args -supports_check_mode $true

# these are your module parameters
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "destination","dest"
$user = Get-AnsibleParam -obj $params -name "user" -type "str" -failifempty $true
$rights = Get-AnsibleParam -obj $params -name "rights" -type "list"
$inheritance_flags = Get-AnsibleParam -obj $params -name "inheritance_flags" -type "list" -default 'ContainerInherit','ObjectInherit' # -validateset 'None','ContainerInherit','ObjectInherit'
$propagation_flags = Get-AnsibleParam -obj $params -name "propagation_flags" -type "str" -default "none" -ValidateSet 'InheritOnly','None','NoPropagateInherit'
$audit_flags = Get-AnsibleParam -obj $params -name "audit_flags" -type "list" -default "success" #-ValidateSet 'Success','Failure'
#$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset 'present','absent'


If (! (Test-Path $path) )
{
    Fail-Json $result "Path not found ($path)"
}

Function Get-CurrentAuditRules ($path) {
    $ACL = Get-Acl -Path $path -Audit

    $HT = Foreach ($Obj in $ACL.Audit)
    {
        @{
            user = $Obj.IdentityReference.ToString()
            rights = ($Obj | Select-Object -expand "*rights").ToString()
            audit_flags = $Obj.AuditFlags.ToString()
            is_inherited = $Obj.InheritanceFlags.ToString()
            inheritance_flags = $Obj.IsInherited.ToString()
            propagation_flags = $Obj.PropagationFlags.ToString()
        }
    }

    If (-Not $HT)
    {
        "No audit rules defined on $path"
    }
    Else {$HT}
}


$result = @{
    changed = $false
    matching_rule_found = $false
    current_audit_rules = Get-CurrentAuditRules $path
}

$ACL = Get-ACL $Path -Audit
$SID = Convert-ToSid $user

$ItemType = (Get-Item $path).GetType()
switch ($ItemType)
{
    ([Microsoft.Win32.RegistryKey]) {
        $rights = [System.Security.AccessControl.RegistryRights]$rights
        $result.path_type = 'registry'
    }
    ([System.IO.FileInfo]) {
        $rights = [System.Security.AccessControl.FileSystemRights]$rights
        $result.path_type = 'file'
    }
    ([System.IO.DirectoryInfo]) {
        $rights = [System.Security.AccessControl.FileSystemRights]$rights
        $result.path_type = 'directory'
    }
}

$flags = [System.Security.AccessControl.AuditFlags]$audit_flags
$inherit = [System.Security.AccessControl.InheritanceFlags]$inheritance_flags
$prop = [System.Security.AccessControl.PropagationFlags]$propagation_flags

Foreach ($group in $ACL.Audit)
{
    #exit here if any existing rule matches defined rule, otherwise exit below
    #with no matches
    If (
        ($group | Select-Object -expand "*Rights") -eq $rights -and
        $group.AuditFlags -eq $flags -and
        $group.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) -eq $SID -and
        $group.InheritanceFlags -eq $inherit -and
        $group.PropagationFlags -eq $prop
    )
    {
        $result.matching_rule_found = $true
	    $result.current_audit_rules = Get-CurrentAuditRules $path
        Exit-Json $result
    }
}

$result.current_audit_rules = Get-CurrentAuditRules $path
Exit-Json $result
