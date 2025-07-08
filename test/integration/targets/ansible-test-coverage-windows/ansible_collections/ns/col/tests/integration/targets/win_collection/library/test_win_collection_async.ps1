#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})
$module.ExitJson()
