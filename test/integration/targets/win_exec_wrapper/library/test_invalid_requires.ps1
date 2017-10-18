#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy.psm1
# Requires -Version 20
# AnsibleRequires -OSVersion 20

# requires statement must be straight after the original # with now space, this module won't fail

Exit-Json -obj @{ output = "output"; changed = $false }
