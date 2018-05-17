#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID
#Requires -Version 3.0
#AnsibleRequires -OSVersion 6
#AnsibleRequires -Become

$output = &whoami.exe
$sid = Convert-ToSID -account_name $output.Trim()

Exit-Json -obj @{ output = $sid; changed = $false }
