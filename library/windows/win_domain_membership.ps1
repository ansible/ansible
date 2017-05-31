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

If ($params.domain_name) {
    $domainname = $params.domain_name
}
Else {
    Fail-Json $result "missing required argument: domain_name"
}

If ($params.domain_username) {
    $domainusername = $params.domain_username
}
Else {
    Fail-Json $result "missing required argument: domain_username"
}

If ($params.domain_password) {
    $domainpassword = $params.domain_password
}
Else {
    Fail-Json $result "missing required argument: domain_password"
}

If ($params.ou_path) {
    $OUPath = $params.ou_path
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

    Set-Attr $result "domain_membership_result" "success"
    $result.changed = $true
}

Exit-Json $result;
