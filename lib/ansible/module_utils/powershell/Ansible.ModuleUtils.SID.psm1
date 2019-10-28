# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

<#
    .SYNOPSIS
    Splited domain and username related to following formats,
    DOMAIN\Username, Username@Domain, .\Username
#>
function Split-UsernameDomainname($account_name){

    $result = New-Object -TypeName PSObject -Property @{ username = $null; domain = $null}

    if ($account_name -like "*\*") {
        $account_name_split = $account_name -split "\\"
        if ($account_name_split[0] -eq ".") {
            $result.domain = $env:COMPUTERNAME
        } else {
            $result.domain = $account_name_split[0]
        }
        $result.username = $account_name_split[1]
    } elseif ($account_name -like "*@*") {
        $account_name_split = $account_name -split "@"
        $result.domain = $account_name_split[1]
        $result.username = $account_name_split[0]
    } else {
        $result.domain = $null
        $result.username = $account_name
    }

    return $result

}

function Get-ADSIObject($Username,$Domain) {

    if ($domain -eq $env:COMPUTERNAME)
    {
        $adsi = [ADSI]("WinNT://$env:COMPUTERNAME,computer")
        $object = $adsi.psbase.children | Where-Object { $_.Name -eq $Username }
    }

    if($domain){
        # searching for a local group with the servername prefixed will fail,
        # need to check for this situation and only use NTAccount(String)
        if ($object.schemaClassName -eq "Group") {
            $account = New-Object System.Security.Principal.NTAccount($Username)
        }
        else {
            $account = New-Object System.Security.Principal.NTAccount($Domain, $Username)
        }
    }
    # when in a domain NTAccount(String) will favour domain lookups check
    # if username is a local user and explictly search on the localhost for
    # that account
    else {
        if ($object.schemaClassName -eq "User") {
            $account = New-Object System.Security.Principal.NTAccount($env:COMPUTERNAME, $Username)
        }
        else {
            $account = New-Object System.Security.Principal.NTAccount($Username)
        }
    }

    return $account

}

<#
    .SYNOPSIS
    Converts a SID to a Down-Level Logon name in the form of DOMAIN\UserName
    If the SID is for a local user or group then DOMAIN would be the server
    name.
#>
function Convert-FromSID($sid) {

    $account_object = New-Object System.Security.Principal.SecurityIdentifier($sid)
    try {
        $nt_account = $account_object.Translate([System.Security.Principal.NTAccount])
    } catch {
        Fail-Json -obj @{} -message "failed to convert sid '$sid' to a logon name: $($_.Exception.Message)"
    }

    return $nt_account.Value

}

<#
    .SYNOPSIS
    converts an account name to a sid, it can take in the following forms
    sid: will just return the sid value that was passed in
    upn:
       principal@domain (domain users only)
    down-level login name
      domain\principal (domain)
      servername\principal (local)
      .\principal (local)
      nt authority\system (local service accounts)
    login name
      principal (local/local service accounts)
#>
function Convert-ToSID($account_name) {
    try {
        $sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList $account_name
        return $sid.Value
    } catch {
        return $null
    }

    $splitedValues = Split-UsernameDomainname -account_name $account_name

    if ($splitedValues.domain) {
        $account = Get-ADSIObject -Username $splitedValues.username -Domain $splitedValues.domain
    }
    else {
        $account = Get-ADSIObject -Username $splitedValues.username -Domain $splitedValues.domain
    }

    try {
        $account_sid = $account.Translate([System.Security.Principal.SecurityIdentifier])
    } catch {
        Fail-Json @{} "account_name $account_name is not a valid account, cannot get SID: $($_.Exception.Message)"
    }

    return $account_sid.Value
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *