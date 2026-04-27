#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic -Optional
#AnsibleRequires -PowerShell ..module_utils.PSRel4 -optional

# These do not exist
#AnsibleRequires -CSharpUtil ..invalid_package.name -Optional
#AnsibleRequires -CSharpUtil ..module_utils.InvalidName -optional
#AnsibleRequires -PowerShell ..invalid_package.pwsh_name -optional
#AnsibleRequires -PowerShell ..module_utils.InvalidPwshName -Optional


$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

$module.Result.data = Invoke-FromPSRel4

$module.ExitJson()
