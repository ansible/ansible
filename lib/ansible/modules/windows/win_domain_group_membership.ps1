#!powershell

# Copyright: (c) 2019, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

try {
    Import-Module ActiveDirectory
}
catch {
    Fail-Json -obj @{} -message "win_domain_group_membership requires the ActiveDirectory PS module to be installed"
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

# Module control parameters
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","pure"
$domain_username = Get-AnsibleParam -obj $params -name "domain_username" -type "str"
$domain_password = Get-AnsibleParam -obj $params -name "domain_password" -type "str" -failifempty ($null -ne $domain_username)
$domain_server = Get-AnsibleParam -obj $params -name "domain_server" -type "str"

# Group Membership parameters
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$members = Get-AnsibleParam -obj $params -name "members" -type "list" -failifempty $true

# Filter ADObjects by ObjectClass
$ad_object_class_filter = "(ObjectClass -eq 'user' -or ObjectClass -eq 'group' -or ObjectClass -eq 'computer' -or ObjectClass -eq 'msDS-ManagedServiceAccount')"

$extra_args = @{}
if ($null -ne $domain_username) {
    $domain_password = ConvertTo-SecureString $domain_password -AsPlainText -Force
    $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $domain_username, $domain_password
    $extra_args.Credential = $credential
}
if ($null -ne $domain_server) {
    $extra_args.Server = $domain_server
}

$result = @{
    changed = $false
    added = [System.Collections.Generic.List`1[String]]@()
    removed = [System.Collections.Generic.List`1[String]]@()
}
if ($diff_mode) {
    $result.diff = @{}
}

$members_before = Get-AdGroupMember -Identity $name @extra_args
$pure_members = [System.Collections.Generic.List`1[String]]@()

foreach ($member in $members) {
    $group_member = Get-ADObject -Filter "SamAccountName -eq '$member' -and $ad_object_class_filter" -Properties objectSid, sAMAccountName @extra_args
    if (!$group_member) {
        Fail-Json -obj $result "Could not find domain user, group, service account or computer named $member"
    }

    if ($state -eq "pure") {
        $pure_members.Add($group_member.objectSid)
    }

    $user_in_group = $false
    foreach ($current_member in $members_before) {
        if ($current_member.sid -eq $group_member.objectSid) {
            $user_in_group = $true
            break
        }
    }

    if ($state -in @("present", "pure") -and !$user_in_group) {
        Add-ADGroupMember -Identity $name -Members $group_member -WhatIf:$check_mode @extra_args
        $result.added.Add($group_member.SamAccountName)
        $result.changed = $true
    } elseif ($state -eq "absent" -and $user_in_group) {
        Remove-ADGroupMember -Identity $name -Members $group_member -WhatIf:$check_mode @extra_args -Confirm:$False
        $result.removed.Add($group_member.SamAccountName)
        $result.changed = $true
    }
}

if ($state -eq "pure") {
    # Perform removals for existing group members not defined in $members
    $current_members = Get-AdGroupMember -Identity $name @extra_args

    foreach ($current_member in $current_members) {
        $user_to_remove = $true
        foreach ($pure_member in $pure_members) {
            if ($pure_member -eq $current_member.sid) {
                $user_to_remove = $false
                break
            }
        }

        if ($user_to_remove) {
            Remove-ADGroupMember -Identity $name -Members $current_member -WhatIf:$check_mode @extra_args -Confirm:$False
            $result.removed.Add($current_member.SamAccountName)
            $result.changed = $true
        }
    }
}

$final_members = Get-AdGroupMember -Identity $name @extra_args

if ($final_members) {
    $result.members = [Array]$final_members.SamAccountName
} else {
    $result.members = @()
}

if ($diff_mode -and $result.changed) {
    $result.diff.before = $members_before.SamAccountName | Out-String
    if (!$check_mode) {
        $result.diff.after = [Array]$final_members.SamAccountName | Out-String
    } else {
        $after = [System.Collections.Generic.List`1[String]]$result.members
        $result.removed | ForEach-Object { $after.Remove($_) > $null }
        $after.AddRange($result.added)
        $result.diff.after = $after | Out-String
    }
}

Exit-Json -obj $result
