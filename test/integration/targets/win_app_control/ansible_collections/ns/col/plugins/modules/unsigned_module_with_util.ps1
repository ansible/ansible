#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil ..module_utils.CSharpSigned

#AnsibleRequires -PowerShell Ansible.ModuleUtils.AddType
#AnsibleRequires -PowerShell ..module_utils.PwshSigned

@{
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    builtin_csharp = $null -ne ('Ansible.Basic.AnsibleModule' -as [type])
    builtin_pwsh = [bool](Get-Command Add-CSharpType -ErrorAction SilentlyContinue)
    collection_csharp = $null -ne ('ansible_collections.ns.col.plugins.module_utils.CSharpSigned.TestClass' -as [type])
    collection_pwsh = [bool](Get-Command Test-PwshSigned -ErrorAction SilentlyContinue)
} | ConvertTo-Json
