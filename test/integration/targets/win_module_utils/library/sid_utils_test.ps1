#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

Function Get-ComputerSID() {
    # find any local user and trim off the final UID
    $luser_sid = (Get-CimInstance Win32_UserAccount -Filter "Domain='$env:COMPUTERNAME'")[0].SID

    return $luser_sid -replace '(S-1-5-21-\d+-\d+-\d+)-\d+', '$1'
}

$local_sid = Get-ComputerSID

# most machines should have a -500 Administrator account, but it may have been renamed. Look it up by SID
$default_admin = Get-CimInstance Win32_UserAccount -Filter "SID='$local_sid-500'"

# this group is called Administrators by default on English Windows, but could named something else. Look it up by SID
$default_admin_group = Get-CimInstance Win32_Group -Filter "SID='S-1-5-32-544'"

if (@($default_admin).Length -ne 1) {
    Fail-Json @{} "could not find a local admin account with SID ending in -500"
}

### Set this to the NETBIOS name of the domain you wish to test, not set for shippable ###
$test_domain = $null

$tests = @(
    # Local Users
    @{ sid = "S-1-1-0"; full_name = "Everyone"; names = @("Everyone") },
    @{ sid = "S-1-5-18"; full_name = "NT AUTHORITY\SYSTEM"; names = @("NT AUTHORITY\SYSTEM", "SYSTEM") },
    @{ sid = "S-1-5-20"; full_name = "NT AUTHORITY\NETWORK SERVICE"; names = @("NT AUTHORITY\NETWORK SERVICE", "NETWORK SERVICE") },
    @{ sid = "$($default_admin.SID)"; full_name = "$($default_admin.FullName)"; names = @("$env:COMPUTERNAME\$($default_admin.Name)", "$($default_admin.Name)", ".\$($default_admin.Name)") },

    # Local Groups
    @{ sid = "$($default_admin_group.SID)"; full_name = "BUILTIN\$($default_admin_group.Name)"; names = @("BUILTIN\$($default_admin_group.Name)", "$($default_admin_group.Name)", ".\$($default_admin_group.Name)") }
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
    # renamed admins may have an empty FullName; skip comparison in that case
    if ($test.full_name) {
        Assert-Equals -actual $actual_account_name -expected $test.full_name
    }

    foreach ($test_name in $test.names) {
        $actual_sid = Convert-ToSID -account_name $test_name
        Assert-Equals -actual $actual_sid -expected $test.sid
    }
}

Exit-Json @{ data = "success" }
