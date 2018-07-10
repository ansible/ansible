#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Version 20.0.0.0

# this shouldn't run as no PS Version will be at 20 in the near future

Exit-Json -obj @{ output = "output"; changed = $false }
