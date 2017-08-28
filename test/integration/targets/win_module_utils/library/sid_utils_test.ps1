#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

Function Get-ComputerSID() {
    # this is sort off cheating but I can't see any better way of getting this SID
    $admin_sid = Convert-ToSID -account_name "$env:COMPUTERNAME\Administrator"

    return $admin_sid.Substring(0, $admin_sid.Length - 4)
}

$local_sid = Get-ComputerSID

### Set this to the NETBIOS name of the domain you wish to test, not set for shippable ###
$test_domain = $null

$tests = @(
    # Local Users
    @{ sid = "S-1-1-0"; full_name = "Everyone"; names = @("Everyone") },
    @{ sid = "S-1-5-18"; full_name = "NT AUTHORITY\SYSTEM"; names = @("NT AUTHORITY\SYSTEM", "SYSTEM") },
    @{ sid = "S-1-5-20"; full_name = "NT AUTHORITY\NETWORK SERVICE"; names = @("NT AUTHORITY\NETWORK SERVICE", "NETWORK SERVICE") },
    @{ sid = "$local_sid-500"; full_name = "$env:COMPUTERNAME\Administrator"; names = @("$env:COMPUTERNAME\Administrator", "Administrator", ".\Administrator") },

    # Local Groups
    @{ sid = "S-1-5-32-544"; full_name = "BUILTIN\Administrators"; names = @("BUILTIN\Administrators", "Administrators", ".\Administrators") }
)

# Add domain tests if the domain name has been set
if ($test_domain -ne $null) {
    Import-Module ActiveDirectory
    $domain_info = Get-ADDomain -Identity $test_domain
    $domain_sid = $domain_info.DomainSID
    $domain_netbios = $domain_info.NetBIOSName
    $domain_upn = $domain_info.Forest

    $tests += @{
        sid = "$domain_sid-512"
        full_name = "$domain_netbios\Domain Admins"
        names = @("$domain_netbios\Domain Admins", "Domain Admins@$domain_upn", "Domain Admins")
    }

    $tests += @{
        sid = "$domain_sid-500"
        full_name = "$domain_netbios\Administrator"
        names = @("$domain_netbios\Administrator", "Administrator@$domain_upn")
    }
}

foreach ($test in $tests) {
    $actual_account_name = Convert-FromSID -sid $test.sid
    Assert-Equals -actual $actual_account_name -expected $test.full_name

    foreach ($test_name in $test.names) {
        $actual_sid = Convert-ToSID -account_name $test_name
        Assert-Equals -actual $actual_sid -expected $test.sid
    }
}

Exit-Json @{ data = "success" }
