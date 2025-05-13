#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell Ansible.ModuleUtils.AdjacentPwshCoverage

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})
$module.Result.util = Test-AdjacentPwshCoverage
$module.ExitJson()
