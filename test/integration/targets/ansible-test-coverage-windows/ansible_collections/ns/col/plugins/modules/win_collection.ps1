#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ..module_utils.CollectionPwshCoverage

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})
$module.Result.util = Test-CollectionPwshCoverage
$module.ExitJson()
