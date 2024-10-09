#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{ supports_check_mode = $true }
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$module.Result.ansible_facts = @{ other = 'foo' }

$module.ExitJson()
