#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

# module parameters
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "destination","dest"
$user = Get-AnsibleParam -obj $params -name "user" -type "str" -failifempty $true
$rights = Get-AnsibleParam -obj $params -name "rights" -type "list"
$inheritance_flags = Get-AnsibleParam -obj $params -name "inheritance_flags" -type "list" -default 'ContainerInherit','ObjectInherit'
$propagation_flags = Get-AnsibleParam -obj $params -name "propagation_flags" -type "str" -default "none" -ValidateSet 'InheritOnly','None','NoPropagateInherit'
$audit_flags = Get-AnsibleParam -obj $params -name "audit_flags" -type "list" -default 'success'
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset 'present','absent'

#Make sure target path is valid
If (-not (Test-Path -Path $path) )
{
    Fail-Json -obj $result -message "defined path ($path) is not found/invalid"
}

#function get current audit rules and convert to hashtable
Function Get-CurrentAuditRules ($path) {
    Try {
        $ACL = Get-Acl $path -Audit
    }
    Catch {
        Return "Unable to retrieve the ACL on $Path"
    }

    $HT = Foreach ($Obj in $ACL.Audit)
    {
        @{
            user = $Obj.IdentityReference.ToString()
            rights = ($Obj | Select-Object -expand "*rights").ToString()
            audit_flags = $Obj.AuditFlags.ToString()
            is_inherited = $Obj.IsInherited.ToString()
            inheritance_flags = $Obj.InheritanceFlags.ToString()
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

#Make sure identity is valid and can be looked up
Try {
    $SID = Convert-ToSid $user
}
Catch {
    Fail-Json -obj $result -message "Failed to lookup the identity ($user) - $($_.exception.message)"
}

#get the path type
$ItemType = (Get-Item $path -Force).GetType()
switch ($ItemType)
{
    ([Microsoft.Win32.RegistryKey]) {$registry = $true;  $result.path_type = 'registry'}
    ([System.IO.FileInfo]) {$file = $true;  $result.path_type = 'file'}
    ([System.IO.DirectoryInfo]) {$result.path_type = 'directory'}
}

#Get current acl/audit rules on the target
Try {
    $ACL = Get-Acl $path -Audit
}
Catch {
    Fail-Json -obj $result -message "Unable to retrieve the ACL on $Path -  $($_.Exception.Message)"
}

#configure acl object to remove the specified user
If ($state -eq 'absent')
{
    #Try and find an identity on the object that matches user
    #We skip inherited items since we can't remove those
    $ToRemove = ($ACL.Audit | Where-Object {$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) -eq $SID -and
    $_.IsInherited -eq $false}).IdentityReference

    #Exit with changed false if no identity is found
    If (-Not $ToRemove)
    {
        $result.current_audit_rules = Get-CurrentAuditRules $path
        Exit-Json -obj $result
    }

    #update the ACL object if identity found
    Try
    {
        $ToRemove | ForEach-Object { $ACL.PurgeAuditRules($_) }
    }
    Catch
    {
        $result.current_audit_rules = Get-CurrentAuditRules $path
        Fail-Json -obj $result -message "Failed to remove audit rule: $($_.Exception.Message)"
    }
}

Else
{
    If ($registry)
    {
        $PossibleRights = [System.Enum]::GetNames([System.Security.AccessControl.RegistryRights])

        Foreach ($right in $rights)
        {
            if ($right -notin $PossibleRights)
            {
                Fail-Json -obj $result -message "$right does not seem to be a valid REGISTRY right"
            }
        }

        $NewAccessRule = New-Object System.Security.AccessControl.RegistryAuditRule($user,$rights,$inheritance_flags,$propagation_flags,$audit_flags)
    }
    Else
    {
        $PossibleRights = [System.Enum]::GetNames([System.Security.AccessControl.FileSystemRights])

        Foreach ($right in $rights)
        {
            if ($right -notin $PossibleRights)
            {
                Fail-Json -obj $result -message "$right does not seem to be a valid FILE SYSTEM right"
            }
        }

        If ($file -and $inheritance_flags -ne 'none')
        {
            Fail-Json -obj $result -message "The target type is a file. inheritance_flags must be changed to 'none'"
        }

        $NewAccessRule = New-Object System.Security.AccessControl.FileSystemAuditRule($user,$rights,$inheritance_flags,$propagation_flags,$audit_flags)
    }

    #exit here if any existing rule matches defined rule since no change is needed
    #if we need to ignore inherited rules in the future, this would be where to do it
    #Just filter out inherited rules from $ACL.Audit
    Foreach ($group in $ACL.Audit | Where-Object {$_.IsInherited -eq $false})
    {
        If (
            ($group | Select-Object -expand "*Rights") -eq ($NewAccessRule | Select-Object -expand "*Rights") -and
            $group.AuditFlags -eq $NewAccessRule.AuditFlags -and
            $group.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) -eq $SID -and
            $group.InheritanceFlags -eq $NewAccessRule.InheritanceFlags -and
            $group.PropagationFlags -eq $NewAccessRule.PropagationFlags
        )
        {
            $result.current_audit_rules = Get-CurrentAuditRules $path
            Exit-Json -obj $result
        }
    }

    #try and set the acl object. AddAuditRule allows for multiple entries to exist under the same
    #identity...so if someone wanted success: write and failure: delete for example, that setup would be
    #possible. The alternative is SetAuditRule which would instead modify an existing rule and not allow
    #for setting the above example.
    Try
    {
        $ACL.AddAuditRule($NewAccessRule)
    }
    Catch
    {
        Fail-Json -obj $result -message "Failed to set the audit rule: $($_.Exception.Message)"
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
Exit-Json -obj $result
