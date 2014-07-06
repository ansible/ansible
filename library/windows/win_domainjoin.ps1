#!powershell
# This file is part of Ansible.
#
# Copyright 2014, Trond Hindenes <trond@hindenes.com>
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


$params = Parse-Args $args;

$result = New-Object psobject @{
    changed = $false
}

If ($params.domainname) {
    $domainname = $params.domainname
}
Else {
    Fail-Json $result "mising required argument: domainname"
}

If ($params.domainusername) {
    $domainusername = $params.domainusername
}
Else {
    Fail-Json $result "mising required argument: domainusername"
}

If ($params.domainpassword) {
    $domainpassword = $params.domainpassword
}
Else {
    Fail-Json $result "mising required argument: domainpassword"
}

If ($params.OUPath) {
    $OUPath = $params.OUPath
}
Else {
    $oupath = $null
}

If ($params.restart) {
    $restart = $params.restart | ConvertTo-Bool
}
Else {
    $restart = $false
}

#Test if we're already member
if ((gwmi win32_computersystem).domain -eq $domainname)
{
    $JoinDOmain = $false
}
Else
{
    $JoinDomain = $true

}


if ($JoinDomain)
{
    #Construct credobject from username/password
    #Test parameters
    #new-item -ItemType file -Path "C:\win_domainjoin.txt" -Force
    #Add-Content -Path "C:\win_domainjoin.txt" -Value $domainname
    #Add-Content -Path "C:\win_domainjoin.txt" -Value $domainusername
    #Add-Content -Path "C:\win_domainjoin.txt" -Value $domainpassword

    $passwordsecurestring = $domainpassword | ConvertTo-SecureString -AsPlainText -Force
    $credential = new-object System.Management.Automation.PSCredential($domainusername,$passwordsecurestring)

    #Perform domain join
    if (!($OUPath))
    {
        try
        {
            $ErrorActionPreference = "Stop"
            Add-Computer -DomainName $domainname -Credential $credential -WarningVariable WarningVar -Restart:$restart
        }
        catch
        {
            Fail-Json $result $_.Exception.Message
        }
    }
    Else
    {
        try
        {
            $ErrorActionPreference = "Stop"
            Add-Computer -DomainName $domainname -Credential $credential -OUPath $OUPath -WarningVariable WarningVar -restart:$restart
        }
        catch
        {
            Fail-Json $result $_.Exception.Message
        }
    }

    Set-Attr $result "domainjoin_result" $success
    $result.changed = $true
}
Else
{
    #Already part of domain
    $result.changed = $false
}

Exit-Json $result;
