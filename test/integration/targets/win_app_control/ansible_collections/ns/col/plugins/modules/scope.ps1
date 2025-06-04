#!powershell

using namespace Ansible.Basic
using namespace System.Management.Automation.Language
using namespace Invalid.Namespace.That.Does.Not.Exist

#AnsibleRequires -CSharpUtil Ansible.Basic

$module = [AnsibleModule]::Create($args, @{ options = @{} })

$module.Result.module_using_namespace = [Parser].FullName

# Verifies the module is run in its own script scope
$var = 'foo'
$module.Result.script_var = $script:var

$missingUsingNamespace = $false
try {
    # exec_wrapper does 'using namespace System.IO'. This ensures that this
    # hasn't persisted to the module scope and it has it's own set of using
    # types.
    $null = [File]::Exists('test')
}
catch {
    $missingUsingNamespace = $true
}
$module.Result.missing_using_namespace = $missingUsingNamespace

$module.ExitJson()
