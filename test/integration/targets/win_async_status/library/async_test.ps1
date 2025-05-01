#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

$module.Result.nested_hashtable = @{
    key = 'value'
}
$module.Result.nested_array = @(
    'string value'
    @{
        key = 'value'
    }
)

$module.ExitJson()
