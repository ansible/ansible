#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil ansible_collections.ns.col.plugins.module_utils.CSharpSigned
#AnsibleRequires -PowerShell ansible_collections.ns.col.plugins.module_utils.PwshSigned

# Tests signed util in another trusted collection works

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{ options = @{} })

$module.Result.language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
$module.Result.csharp_util = [ansible_collections.ns.col.plugins.module_utils.CSharpSigned.TestClass]::TestMethod("value")
$module.Result.powershell_util = Test-PwshSigned

$module.ExitJson()
