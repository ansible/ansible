#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy.psm1
#AnsibleRequires -PSVersion 20.0

# this shouldn't run as no PS Version will be at 20.0 in the near future

Exit-Json -obj @{ output = "output"; changed = $false }
