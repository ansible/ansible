#!powershell

#AnsibleRequires -PowerShell Ansible.ModuleUtils.InvalidSyntax

@{
    changed = $false
    complex_args = Test-UtilFunction
} | ConvertTo-Json -Compress
