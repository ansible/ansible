#!powershell

# This scenario needs to use Legacy, the same HadErrors won't be set if using
# Ansible.Basic
#Requires -Module Ansible.ModuleUtils.Legacy

# This will set `$ps.HadErrors` in the running pipeline but with no error
# record written. We are testing that it won't set the rc to 1 for this
# scenario.
try {
    Write-Error -Message err -ErrorAction Stop
}
catch {
    Exit-Json @{}
}

Fail-Json @{} "This should not be reached"
