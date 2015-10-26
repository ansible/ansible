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

#Functions
Function UserSearch
{
    Param ([string]$AccountName)
    #Check if there's a realm specified
    if ($AccountName.Split("\").count -gt 1)
    {
        if ($AccountName.Split("\")[0] -eq $env:COMPUTERNAME)
        {
            $IsLocalAccount = $true
        }
        Else
        {
            $IsDomainAccount = $true
            $IsUpn = $false
        }
 
    }
    Elseif ($AccountName -contains "@")
    {
        $IsDomainAccount = $true
        $IsUpn = $true
    }
    Else
    {
        #Default to local user account
        $accountname = $env:COMPUTERNAME + "\" + $AccountName
        $IsLocalAccount = $true
    }

    if ($IsLocalAccount -eq $true)
    {
        # do not use Win32_UserAccount, because e.g. SYSTEM (BUILTIN\SYSTEM or COMPUUTERNAME\SYSTEM) will not be listed. on Win32_Account groups will be listed too
        $localaccount = get-wmiobject -class "Win32_Account" -namespace "root\CIMV2" -filter "(LocalAccount = True)" | where {$_.Caption -eq $AccountName}
        if ($localaccount)
        {
            return $localaccount.SID
        }
    }
    ElseIf ($IsDomainAccount -eq $true)
    {
        #Search by samaccountname
        $Searcher = [adsisearcher]""

        If ($IsUpn -eq $false) {
            $Searcher.Filter = "sAMAccountName=$($accountname.split("\")[1])"
        }
        Else {
            $Searcher.Filter = "userPrincipalName=$($accountname)"
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
$recurse = Get-Attr $params "recurse" "no" -validateSet "no","yes" -resultobj $result | ConvertTo-Bool

If (-Not (Test-Path -Path $path)) {
    Fail-Json $result "$path file or directory does not exist on the host"
}

# Test that the user/group is resolvable on the local machine
$sid = UserSearch -AccountName ($user)
if (!$sid)
{
    Fail-Json $result "$user is not a valid user or group on the host machine or domain"
}

Try {
    $objUser = New-Object System.Security.Principal.SecurityIdentifier($sid)

    $file = Get-Item -Path $path
    $acl = Get-Acl $file.FullName

    If ($acl.getOwner([System.Security.Principal.SecurityIdentifier]) -ne $objUser) {
        $acl.setOwner($objUser)
        Set-Acl $file.FullName $acl

        Set-Attr $result "changed" $true;
    }

    If ($recurse) {
        $files = Get-ChildItem -Path $path -Force -Recurse
        ForEach($file in $files){
            $acl = Get-Acl $file.FullName

            If ($acl.getOwner([System.Security.Principal.SecurityIdentifier]) -ne $objUser) {
                $acl.setOwner($objUser)
                Set-Acl $file.FullName $acl

                Set-Attr $result "changed" $true;
            }
        }
    }
}
Catch {
    Fail-Json $result "an error occured when attempting to change owner on $path for $user"
}

Exit-Json $result
