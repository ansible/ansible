#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

using namespace Ansible.Basic

$spec = @{
    options = @{
        value = @{ type = 'str'; required = $true }
    }
}
$module = [AnsibleModule]::Create($args, $spec)

$module.Result.value = $module.Params.value
$module.Result.value_type = $module.Params.value.GetType().FullName

$module.ExitJson()
