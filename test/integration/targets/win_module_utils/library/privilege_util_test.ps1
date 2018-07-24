#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.PrivilegeUtil

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

Import-PrivilegeUtil

Function Assert-Equals($actual, $expected) {
    if ($actual -cne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

# taken from https://docs.microsoft.com/en-us/windows/desktop/SecAuthZ/privilege-constants
$total_privileges = @(
    "SeAssignPrimaryTokenPrivilege",
    "SeAuditPrivilege",
    "SeBackupPrivilege",
    "SeChangeNotifyPrivilege",
    "SeCreateGlobalPrivilege",
    "SeCreatePagefilePrivilege",
    "SeCreatePermanentPrivilege",
    "SeCreateSymbolicLinkPrivilege",
    "SeCreateTokenPrivilege",
    "SeDebugPrivilege",
    "SeEnableDelegationPrivilege",
    "SeImpersonatePrivilege",
    "SeIncreaseBasePriorityPrivilege",
    "SeIncreaseQuotaPrivilege",
    "SeIncreaseWorkingSetPrivilege",
    "SeLoadDriverPrivilege",
    "SeLockMemoryPrivilege",
    "SeMachineAccountPrivilege",
    "SeManageVolumePrivilege",
    "SeProfileSingleProcessPrivilege",
    "SeRelabelPrivilege",
    "SeRemoteShutdownPrivilege",
    "SeRestorePrivilege",
    "SeSecurityPrivilege",
    "SeShutdownPrivilege",
    "SeSyncAgentPrivilege",
    "SeSystemEnvironmentPrivilege",
    "SeSystemProfilePrivilege",
    "SeSystemtimePrivilege",
    "SeTakeOwnershipPrivilege",
    "SeTcbPrivilege",
    "SeTimeZonePrivilege",
    "SeTrustedCredManAccessPrivilege",
    "SeUndockPrivilege"
)

$raw_privilege_output = &whoami /priv | Where-Object { $_.StartsWith("Se") }
$actual_privileges = @{}
foreach ($raw_privilege in $raw_privilege_output) {
    $split = $raw_privilege.TrimEnd() -split " "
    $actual_privileges."$($split[0])" = ($split[-1] -eq "Enabled")
}
$process = [Ansible.PrivilegeUtil.Helpers]::GetCurrentProcess()

### Test variables ###
Assert-Equals -actual ($ansible_privilege_util_namespaces -is [array]) -expected $true
Assert-Equals -actual ($ansible_privilege_util_code -is [String]) -expected $true

### Test PS cmdlets ###
# test ps Get-AnsiblePrivilege
foreach ($privilege in $total_privileges) {
    $expected = $null
    if ($actual_privileges.ContainsKey($privilege)) {
        $expected = $actual_privileges.$privilege
    }
    $actual = Get-AnsiblePrivilege -Name $privilege
    Assert-Equals -actual $actual -expected $expected
}

# test c# GetAllPrivilegeInfo
$actual = [Ansible.PrivilegeUtil.Helpers]::GetAllPrivilegeInfo($process)
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected $actual_privileges.Count
foreach ($privilege in $total_privileges) {
    if ($actual_privileges.ContainsKey($privilege)) {
        $actual_value = $actual.$privilege
        if ($actual_privileges.$privilege) {
            Assert-Equals -actual $actual_value.HasFlag([Ansible.PrivilegeUtil.NativeHelpers+PrivilegeAttributes]::Enabled) -expected $true
        } else {
            Assert-Equals -actual $actual_value.HasFlag([Ansible.PrivilegeUtil.NativeHelpers+PrivilegeAttributes]::Enabled) -expected $false
        }
    }
}

# test Set-AnsiblePrivilege
Set-AnsiblePrivilege -Name SeUndockPrivilege -Value $false  # ensure we start with a disabled privilege

Set-AnsiblePrivilege -Name SeUndockPrivilege -Value $true -WhatIf
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $false

Set-AnsiblePrivilege -Name SeUndockPrivilege -Value $true
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $true

Set-AnsiblePrivilege -Name SeUndockPrivilege -Value $false -WhatIf
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $true

Set-AnsiblePrivilege -Name SeUndockPrivilege -Value $false
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $false

# test Remove-AnsiblePrivilege
Remove-AnsiblePrivilege -Name SeUndockPrivilege -WhatIf
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $false

Remove-AnsiblePrivilege -Name SeUndockPrivilege
$actual = Get-AnsiblePrivilege -Name SeUndockPrivilege
Assert-Equals -actual $actual -expected $null

### Test C# code ###
# test CheckPrivilegeName
Assert-Equals -actual ([Ansible.PrivilegeUtil.Helpers]::CheckPrivilegeName($total_privileges[0])) -expected $true
Assert-Equals -actual ([Ansible.PrivilegeUtil.Helpers]::CheckPrivilegeName("SeFake")) -expected $false

# test DisablePrivilege
# ensure we start in an enabled state
Set-AnsiblePrivilege -Name SeTimeZonePrivilege -Value $true
$actual = [Ansible.PrivilegeUtil.Helpers]::DisablePrivilege($process, "SeTimeZonePrivilege")
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected 1
Assert-Equals -actual $actual.SeTimeZonePrivilege -expected $true

$actual = [Ansible.PrivilegeUtil.Helpers]::DisablePrivilege($process, "SeTimeZonePrivilege")
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected 0

# test DisableAllPrivileges
$actual_disable_all = [Ansible.PrivilegeUtil.Helpers]::DisableAllPrivileges($process)
Assert-Equals -actual $actual_disable_all.GetType().Name -expected 'Dictionary`2'

$actual = [Ansible.PrivilegeUtil.Helpers]::DisableAllPrivileges($process)
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected 0

# test EnablePrivilege
$actual = [Ansible.PrivilegeUtil.Helpers]::EnablePrivilege($process, "SeTimeZonePrivilege")
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected 1
Assert-Equals -actual $actual.SeTimeZonePrivilege -expected $false

$actual = [Ansible.PrivilegeUtil.Helpers]::EnablePrivilege($process, "SeTimeZonePrivilege")
Assert-Equals -actual $actual.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.Count -expected 0

# test SetTokenPrivileges
$actual = [Ansible.PrivilegeUtil.Helpers]::SetTokenPrivileges($process, $actual_disable_all)
Assert-Equals -actual $actual_disable_all.GetType().Name -expected 'Dictionary`2'
Assert-Equals -actual $actual.ContainsKey("SeTimeZonePrivilege") -expected $false
Assert-Equals -actual $actual.Count -expected $actual_disable_all.Count

# test RemovePrivilege
[Ansible.PrivilegeUtil.Helpers]::RemovePrivilege($process, "SeTimeZonePrivilege")
$actual = Get-AnsiblePrivilege -Name SeTimeZonePrivilege
Assert-Equals -actual $actual -expected $null

$result.data = "success"
Exit-Json -obj $result
