#!powershell

# (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
#
# This file is part of Ansible
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

$ErrorActionPreference = "Stop"

function Test-GroupMember {
    <#
    .SYNOPSIS
    Parse desired member into domain and username.
    Also, ensure member can be resolved/exists on the target system by checking its SID.
    .NOTES
    Returns a hashtable of the same type as returned from Get-GroupMember.
    Accepts username (users, groups) and domains in the following formats:
    - username
    - .\username
    - SERVERNAME\username
    - NT AUTHORITY\username
    - DOMAIN\username
    - username@DOMAIN
    #>
    param(
        [String]$GroupMember
    )

    $parsed_member = @{
        domain = $null
        username = $null
        combined = $null
    }

    # Split domain and account name into separate values
    # '\' or '@' needs additional parsing, otherwise assume local computer

    if ($GroupMember -match "\\") {
        # DOMAIN\username
        $split_member = $GroupMember.Split("\")

        if ($split_member[0] -in @($env:COMPUTERNAME, ".")) {
            # Local
            $parsed_member.domain = $env:COMPUTERNAME
        }
        else {
            # Domain or service (i.e. NT AUTHORITY)
            $parsed_member.domain = $split_member[0]
        }
        $parsed_member.username = $split_member[1]
    }
    elseif ($GroupMember -match "@") {
        # username@DOMAIN
        $parsed_member.domain = $GroupMember.Split("@")[1]
        $parsed_member.username = $GroupMember.Split("@")[0]
    }
    else {
        # Local
        $parsed_member.domain = $env:COMPUTERNAME
        $parsed_member.username = $GroupMember
    }

    if ($parsed_member.domain -match "\.") {
        # Assume FQDN was passed - change to NetBIOS/short name for later ADSI membership comparisons
        $netbios_name = (Get-CimInstance -ClassName Win32_NTDomain -Filter "DnsForestName = '$($parsed_member.domain)'").DomainName

        if (!$netbios_name) {
            Fail-Json -obj $result -message "Could not resolve NetBIOS name for domain $($parsed_member.domain)"
        }
        $parsed_member.domain = $netbios_name
    }

    # Set SID check arguments, and 'combined' for later comparison and output reporting
    if ($parsed_member.domain -eq $env:COMPUTERNAME) {
        $sid_check_args = @($parsed_member.username)
        $parsed_member.combined = "{0}" -f $parsed_member.username
    }
    else {
        $sid_check_args = @($parsed_member.domain, $parsed_member.username)
        $parsed_member.combined = "{0}\{1}" -f $parsed_member.domain, $parsed_member.username
    }

    try {
        $user_object = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $sid_check_args
        $user_object.Translate([System.Security.Principal.SecurityIdentifier])
    }
    catch {
        Fail-Json -obj $result -message "Could not resolve group member $GroupMember"
    }

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
        ([ADSI]$_).InvokeGet("ADsPath")
    }

    foreach ($current_member in $current_members) {
        $parsed_member = @{
            domain = $null
            username = $null
            combined = $null
        }

        $rootless_adspath = $current_member.Replace("WinNT://", "")
        $split_adspath = $rootless_adspath.Split("/")

        if ($split_adspath -match $env:COMPUTERNAME) {
            # Local
            $parsed_member.domain = $env:COMPUTERNAME
            $parsed_member.username = $split_adspath[-1]
            $parsed_member.combined = $split_adspath[-1]
        }
        elseif ($split_adspath.Count -eq 1 -and $split_adspath[0] -like "S-1*") {
            # Broken SID
            $parsed_member.username = $split_adspath[0]
            $parsed_member.combined = $split_adspath[0]
        }
        else {
            # Domain or service (i.e. NT AUTHORITY)
            $parsed_member.domain = $split_adspath[0]
            $parsed_member.username = $split_adspath[1]
            $parsed_member.combined = "{0}\{1}" -f $split_adspath[0], $split_adspath[1]
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
}
elseif ($state -eq "absent") {
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
        if ($current_member.combined -eq $group_member.combined) {
            $user_in_group = $true
            break
        }
    }

    $member_adspath = "WinNT://{0}/{1}" -f $group_member.domain, $group_member.username

    try {
        if ($state -eq "present" -and !$user_in_group) {
            if (!$check_mode) {
                $group.Add($member_adspath)
                $result.added += $group_member.combined
            }
            $result.changed = $true
        }
        elseif ($state -eq "absent" -and $user_in_group) {
            if (!$check_mode) {
                $group.Remove($member_adspath)
                $result.removed += $group_member.combined
            }
            $result.changed = $true
        }
    }
    catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }
}

$final_members = Get-GroupMember -Group $group

if ($final_members) {
    $result.members = [Array]$final_members.combined
}
else {
    $result.members = @()
}

Exit-Json -obj $result
