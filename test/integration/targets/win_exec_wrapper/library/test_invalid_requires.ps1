#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy.psm1
#AnsibleRequires -OSVersion 20
#AnsibleRequires -PSVersion 20.0.0

# a version must be only major.minor, this module won't fail

Exit-Json -obj @{ output = "output"; changed = $false }
