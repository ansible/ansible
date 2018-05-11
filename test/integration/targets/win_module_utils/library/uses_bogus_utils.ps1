#!powershell

# this should fail
#Requires -Module Ansible.ModuleUtils.BogusModule

Exit-Json @{ data="success" }
