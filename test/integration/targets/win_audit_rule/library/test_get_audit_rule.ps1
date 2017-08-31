#!powershell

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy.psm1
#Requires -Module Ansible.ModuleUtils.SID.psm1

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

# these are your module parameters
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "destination","dest"
$identity_reference = Get-AnsibleParam -obj $params -name "identity_reference" -type "str" -failifempty $true
$rights = Get-AnsibleParam -obj $params -name "rights" -type "list"
$inheritance_flags = Get-AnsibleParam -obj $params -name "inheritance_flags" -type "list" -default 'ContainerInherit','ObjectInherit' # -validateset 'None','ContainerInherit','ObjectInherit'
$propagation_flags = Get-AnsibleParam -obj $params -name "propagation_flags" -type "str" -default "none" -ValidateSet 'InheritOnly','None','NoPropagateInherit'
$audit_flags = Get-AnsibleParam -obj $params -name "audit_flags" -type "list" -default "success" #-ValidateSet 'Success','Failure'
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset 'present','absent'


If (! (Test-Path $path) )
{
    Fail-Json $result "Path not found ($path)"
}

Function Get-CurrentAuditRules ($path) {
    $ACL = Get-Acl $path -Audit

    $HT = Foreach ($Obj in $ACL.Audit)
    {
        @{
        identity_reference = $Obj.IdentityReference.ToString()
        rights = ($Obj | select -expand "*rights").ToString()
        audit_flags = $Obj.AuditFlags.ToString()
        is_inherited = $Obj.IsInherited.ToString()
        inheritance_flags = $Obj.IsInherited.ToString()
        propagation_flags = $Obj.PropagationFlags.ToString()
        }
    }
    $HT
}

$result = @{
    changed = $false
    matching_rule_found = $false
    current_audit_rules = Get-CurrentAuditRules $path
}

#set type. we say $state -eq present because absent doesn't care about the path type.
If ($path -match "^HK(CC|CR|CU|LM|U):\\" -and $state -eq 'present')
{
    $Registry = $True
    $rights = [System.Security.AccessControl.RegistryRights]$rights
}
Elseif ($state -eq 'present')
{
    $FileSystem = $True
    $rights = [System.Security.AccessControl.FileSystemRights]$rights
}

$ACL = Get-ACL $Path -Audit
$SID = Convert-ToSid $identity_reference

$flags = [System.Security.AccessControl.AuditFlags]$audit_flags
$inherit = [System.Security.AccessControl.InheritanceFlags]$inheritance_flags
$prop = [System.Security.AccessControl.PropagationFlags]$propagation_flags

Foreach ($group in $ACL.Audit)
{
    #exit here if any existing rule matches defined rule, otherwise exit below
    #with no matches
    If (
        ($group | select -expand "*Rights") -eq $rights -and
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
