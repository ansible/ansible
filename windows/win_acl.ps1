#!powershell
# This file is part of Ansible
#
# Copyright 2015, Phil Schwartz <schwartzmx@gmail.com>
# Copyright 2015, Trond Hindenes
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
 
# win_acl module (File/Resources Permission Additions/Removal)
 
 
#Functions
Function UserSearch
{
    Param ([string]$accountName)
    #Check if there's a realm specified

    $searchDomain = $false
    $searchDomainUPN = $false
    if ($accountName.Split("\").count -gt 1)
    {
        if ($accountName.Split("\")[0] -ne $env:COMPUTERNAME)
        {
            $searchDomain = $true
            $accountName = $accountName.split("\")[1]
        }
    }
    Elseif ($accountName.contains("@"))
    {
        $searchDomain = $true
        $searchDomainUPN = $true
    }
    Else
    {
        #Default to local user account
        $accountName = $env:COMPUTERNAME + "\" + $accountName
    }

    if ($searchDomain -eq $false)
    {
        # do not use Win32_UserAccount, because e.g. SYSTEM (BUILTIN\SYSTEM or COMPUUTERNAME\SYSTEM) will not be listed. on Win32_Account groups will be listed too
        $localaccount = get-wmiobject -class "Win32_Account" -namespace "root\CIMV2" -filter "(LocalAccount = True)" | where {$_.Caption -eq $accountName}
        if ($localaccount)
        {
            return $localaccount.SID
        }
    }
    Else
    {
        #Search by samaccountname
        $Searcher = [adsisearcher]""

        If ($searchDomainUPN -eq $false) {
            $Searcher.Filter = "sAMAccountName=$($accountName)"
        }
        Else {
            $Searcher.Filter = "userPrincipalName=$($accountName)"
        }

        $result = $Searcher.FindOne() 
        if ($result)
        {
            $user = $result.GetDirectoryEntry()

            # get binary SID from AD account
            $binarySID = $user.ObjectSid.Value

            # convert to string SID
            return (New-Object System.Security.Principal.SecurityIdentifier($binarySID,0)).Value
        }
    }
}
 
$params = Parse-Args $args;

$result = New-Object PSObject;
Set-Attr $result "changed" $false;

$path = Get-Attr $params "path" -failifempty $true
$user = Get-Attr $params "user" -failifempty $true
$rights = Get-Attr $params "rights" -failifempty $true

$type = Get-Attr $params "type" -failifempty $true -validateSet "allow","deny" -resultobj $result
$state = Get-Attr $params "state" "present" -validateSet "present","absent" -resultobj $result

$inherit = Get-Attr $params "inherit" ""
$propagation = Get-Attr $params "propagation" "None" -validateSet "None","NoPropagateInherit","InheritOnly" -resultobj $result

If (-Not (Test-Path -Path $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = UserSearch -AccountName ($user)
if (!$sid)
{
    Fail-Json $result "$user is not a valid user or group on the host machine or domain"
}

If (Test-Path -Path $path -PathType Leaf) {
    $inherit = "None"
}
ElseIf ($inherit -eq "") {
    $inherit = "ContainerInherit, ObjectInherit"
}
 
Try {
    $colRights = [System.Security.AccessControl.FileSystemRights]$rights
    $InheritanceFlag = [System.Security.AccessControl.InheritanceFlags]$inherit
    $PropagationFlag = [System.Security.AccessControl.PropagationFlags]$propagation
 
    If ($type -eq "allow") {
        $objType =[System.Security.AccessControl.AccessControlType]::Allow
    }
    Else {
        $objType =[System.Security.AccessControl.AccessControlType]::Deny
    }
 
    $objUser = New-Object System.Security.Principal.SecurityIdentifier($sid)
    $objACE = New-Object System.Security.AccessControl.FileSystemAccessRule ($objUser, $colRights, $InheritanceFlag, $PropagationFlag, $objType)
    $objACL = Get-ACL $path
 
    # Check if the ACE exists already in the objects ACL list
    $match = $false
    ForEach($rule in $objACL.Access){
        $ruleIdentity = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier])
        If (($rule.FileSystemRights -eq $objACE.FileSystemRights) -And ($rule.AccessControlType -eq $objACE.AccessControlType) -And ($ruleIdentity -eq $objACE.IdentityReference) -And ($rule.IsInherited -eq $objACE.IsInherited) -And ($rule.InheritanceFlags -eq $objACE.InheritanceFlags) -And ($rule.PropagationFlags -eq $objACE.PropagationFlags)) { 
            $match = $true
            Break
        } 
    }

    If ($state -eq "present" -And $match -eq $false) {
        Try {
            $objACL.AddAccessRule($objACE)
            Set-ACL $path $objACL
            Set-Attr $result "changed" $true;
        }
        Catch {
            Fail-Json $result "an exception occured when adding the specified rule"
        }
    }
    ElseIf ($state -eq "absent" -And $match -eq $true) {
        Try {
            $objACL.RemoveAccessRule($objACE)
            Set-ACL $path $objACL
            Set-Attr $result "changed" $true;
        }
        Catch {
            Fail-Json $result "an exception occured when removing the specified rule"
        }
    }
    Else {
        # A rule was attempting to be added but already exists
        If ($match -eq $true) {
            Exit-Json $result "the specified rule already exists"
        }
        # A rule didn't exist that was trying to be removed
        Else {
            Exit-Json $result "the specified rule does not exist"
        }       
    }
}
Catch {
    Fail-Json $result "an error occured when attempting to $state $rights permission(s) on $path for $user"
}
 
Exit-Json $result
