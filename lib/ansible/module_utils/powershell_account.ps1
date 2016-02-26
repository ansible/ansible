# Helper function to get account SID from multiple sources for various usage
# Example: $sid = GetAccountSID "user"
# Example: $sid = GetAccountSID "domain\user"
# Example: $sid = GetAccountSID "user@domain.com"
#          $objUser = New-Object System.Security.Principal.SecurityIdentifier($sid)
#          $fullUsername = $objUser.Translate([System.Security.Principal.NTAccount]).Value
Function Get-AccountSid
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