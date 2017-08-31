#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
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

<#

https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.inheritanceflags(v=vs.110).aspx
https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.propagationflags(v=vs.110).aspx

#>

#Make sure target path is valid
If (-not (Test-Path -Path $path) )
{
    Fail-Json -obj $result -message "defined path ($path) is not found/invalid"
}

#reusable get current audit rules and convert to hashtable
Function Get-CurrentAuditRules ($path) {
    $ACL = Get-Acl -Path $path -Audit

    $HT = Foreach ($Obj in $ACL.Audit)
    {
        @{
            identity_reference = $Obj.IdentityReference.ToString()
            rights = ($Obj | Select-Object -expand "*rights").ToString()
            audit_flags = $Obj.AuditFlags.ToString()
            is_inherited = $Obj.IsInherited.ToString()
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
    current_audit_rules = Get-CurrentAuditRules $path
}

#Make sure target path is valid
If (-not (Test-Path -Path $path) )
{
    Fail-Json -obj $result -message "defined path ($path) is not found/invalid"
}

#Make sure identity is valid and can be looked up
Try {
    $SID = Convert-ToSid $identity_reference
}
Catch {
    Fail-Json -obj $result -message "Failed to lookup the identity ($identity_reference) - $($_.exception.message)"
}


#Make sure identity is valid and can be looked up
Try {
    $SID = Convert-ToSid $identity_reference
}
Catch {
    Fail-Json -obj $result -message "Failed to lookup the identity ($identity_reference) - $($_.exception.message)"
}

#Make sure that the defined rights are valid and define type of audit rule
If ($path -match "^HK(CC|CR|CU|LM|U):\\" -and $state -eq 'present')
{
    $PossibleRights = [System.Enum]::GetNames([System.Security.AccessControl.RegistryRights])
    Foreach ($right in $rights)
    {
        if ($right -notin $PossibleRights)
        {
            Fail-Json -obj $result -message "$right does not seem to be a valid REGISTRY right"
        }
    }
    $Registry = $True
}
Elseif ($state -eq 'present')
{
    $PossibleRights = [System.Enum]::GetNames([System.Security.AccessControl.FileSystemRights])
    Foreach ($right in $rights)
    {
        if ($right -notin $PossibleRights)
        {
            Fail-Json -obj $result -message "$right does not seem to be a valid FILE SYSTEM right"
        }
    }
    $FileSystem = $True
}

$ACL = Get-Acl $path -Audit

#configure acl object to remove the specified user
If ($state -eq 'absent')
{
    #Try and find an identity on the object that matches identity_reference
    $ToRemove = ($ACL.Audit | ? {$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) -eq $SID}).IdentityReference

    #Exit with changed false if no identity is found
    If (-Not $ToRemove)
    {
        $result.current_audit_rules = Get-CurrentAuditRules $path
        Exit-Json -obj $result -message
    }

    #update the ACL object if identity found
    Try
    {
        $ACL.PurgeAuditRules($ToRemove)
    }
    Catch
    {
        $result.current_audit_rules = Get-CurrentAuditRules $path
        fail-Json -obj $result -message "Failed to remove auditrule: $($_.Exception.Message)"
    }

}
#otherwise configure acl object to add/modify user
Else
{
    $flags = [System.Security.AccessControl.AuditFlags]$audit_flags
    $inherit = [System.Security.AccessControl.InheritanceFlags]$inheritance_flags
    $prop = [System.Security.AccessControl.PropagationFlags]$propagation_flags

    If ($FileSystem)
    {
        $rights = [System.Security.AccessControl.FileSystemRights]$rights
        $AccessRule = New-Object System.Security.AccessControl.FileSystemAuditRule($identity_reference,$rights,$inheritance_flags,$propagation_flags,$audit_flags)
    }
    Else
    {
        $rights = [System.Security.AccessControl.RegistryRights]$rights
        $AccessRule = New-Object System.Security.AccessControl.RegistryAuditRule($identity_reference,$rights,$inheritance_flags,$propagation_flags,$audit_flags)
    }

    Foreach ($group in $ACL.Audit)
    {
        #exit here if any existing rule matches defined rule since no change is needed
        If (
            ($group | select -expand "*Rights") -eq $rights -and
            $group.AuditFlags -eq $flags -and
            $group.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) -eq $SID -and
            $group.InheritanceFlags -eq $inherit -and
            $group.PropagationFlags -eq $prop
        )
        {
            $result.current_audit_rules = Get-CurrentAuditRules $path
            Exit-Json -obj $result -message
        }
    }

    Try
    {
        $ACL.SetAuditRule($AccessRule)
    }
    Catch
    {
        fail-Json -obj $result -message "Failed to set the audit rule: $($_.Exception.Message)"
    }
}

#finally set the permissions
Try {
    Set-Acl -Path $path -ACLObject $ACL -WhatIf:$check_mode
}
Catch {
    $result.current_audit_rules = Get-CurrentAuditRules $path
    Fail-Json -obj $result -message "Failed to apply audit change: $($_.Exception.Message)"
}

#exit here after a change is applied
$result.current_audit_rules = Get-CurrentAuditRules $path
$result.changed = $true
exit-Json -obj $result
