#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -OSVersion 20.0

# this shouldn't run as no Windows OS will meet the version of 20.0

Exit-Json -obj @{ output = "output"; changed = $false }
