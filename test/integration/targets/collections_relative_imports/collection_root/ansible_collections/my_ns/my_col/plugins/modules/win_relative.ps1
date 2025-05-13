#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ..module_utils.PSRel1

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

$module.Result.data = Invoke-FromPSRel1

$module.ExitJson()
