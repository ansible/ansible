#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy.psm1
#Requires -Module Ansible.ModuleUtils.SID.psm1
#AnsibleRequires -Become
#AnsibleRequires -OSVersion 6.0
#AnsibleRequires -PSVersion 3.0

$output = &whoami.exe
$sid = Convert-ToSID -account_name $output.Trim()

Exit-Json -obj @{ output = $sid; changed = $false }
