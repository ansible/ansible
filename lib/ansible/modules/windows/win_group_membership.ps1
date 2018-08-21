#!powershell

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

function Test-GroupMember {
    <#
    .SYNOPSIS
    Return SID and consistent account name (DOMAIN\Username) format of desired member.
    Also, ensure member can be resolved/exists on the target system by checking its SID.
    .NOTES
    Returns a hashtable of the same type as returned from Get-GroupMember.
    Accepts username (users, groups) and domains in the formats accepted by Convert-ToSID.
    #>
    param(
        [String]$GroupMember
    )

    $parsed_member = @{
        sid = $null
        account_name = $null
    }

    $sid = Convert-ToSID -account_name $GroupMember
    $account_name = Convert-FromSID -sid $sid

    $parsed_member.sid = $sid
    $parsed_member.account_name = $account_name

    return $parsed_member
}

function Get-GroupMember {
    <#
    .SYNOPSIS
    Retrieve group members for a given group, and return in a common format.
    .NOTES
    Returns an array of hashtables of the same type as returned from Test-GroupMember.
    #>
    param(
        [System.DirectoryServices.DirectoryEntry]$Group
    )

    $members = @()

    $current_members = $Group.psbase.Invoke("Members") | ForEach-Object {
        $bytes = ([ADSI]$_).InvokeGet("objectSID")
        $sid = New-Object -TypeName Security.Principal.SecurityIdentifier -ArgumentList $bytes, 0
        $adspath = ([ADSI]$_).InvokeGet("ADsPath")

        @{sid = $sid; adspath = $adspath} | Write-Output
    }

    foreach ($current_member in $current_members) {
        $parsed_member = @{
            sid = $current_member.sid
            account_name = $null
        }

        $rootless_adspath = $current_member.adspath.Replace("WinNT://", "")
        $split_adspath = $rootless_adspath.Split("/")

        # Ignore lookup on a broken SID, and just return the SID as the account_name
        if ($split_adspath.Count -eq 1 -and $split_adspath[0] -like "S-1*") {
            $parsed_member.account_name = $split_adspath[0]
        } else {
            $account_name = Convert-FromSID -sid $current_member.sid
            $parsed_member.account_name = $account_name
        }

        $members += $parsed_member
    }

    return $members
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$members = Get-AnsibleParam -obj $params -name "members" -type "list" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"

$result = @{
    changed = $false
    name = $name
}
if ($state -eq "present") {
    $result.added = @()
} elseif ($state -eq "absent") {
    $result.removed = @()
}

$adsi = [ADSI]"WinNT://$env:COMPUTERNAME"
$group = $adsi.Children | Where-Object { $_.SchemaClassName -eq "group" -and $_.Name -eq $name }

if (!$group) {
    Fail-Json -obj $result -message "Could not find local group $name"
}

$current_members = Get-GroupMember -Group $group

foreach ($member in $members) {
    $group_member = Test-GroupMember -GroupMember $member

    $user_in_group = $false
    foreach ($current_member in $current_members) {
        if ($current_member.sid -eq $group_member.sid) {
            $user_in_group = $true
            break
        }
    }

    $member_sid = "WinNT://{0}" -f $group_member.sid

    try {
        if ($state -eq "present" -and !$user_in_group) {
            if (!$check_mode) {
                $group.Add($member_sid)
                $result.added += $group_member.account_name
            }
            $result.changed = $true
        } elseif ($state -eq "absent" -and $user_in_group) {
            if (!$check_mode) {
                $group.Remove($member_sid)
                $result.removed += $group_member.account_name
            }
            $result.changed = $true
        }
    } catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }
}

$final_members = Get-GroupMember -Group $group

if ($final_members) {
    $result.members = [Array]$final_members.account_name
} else {
    $result.members = @()
}

Exit-Json -obj $result
