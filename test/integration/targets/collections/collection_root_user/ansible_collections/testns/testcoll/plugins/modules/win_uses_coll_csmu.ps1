#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.MyCSMU
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.subpkg.subcs

$spec = @{
    options = @{
        data = @{ type = "str"; default = "called from $([ansible_collections.testns.testcoll.plugins.module_utils.MyCSMU.CustomThing]::HelloWorld())" }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$data = $module.Params.data

if ($data -eq "crash") {
    throw "boom"
}

$module.Result.ping = $data
$module.Result.source = "user"
$module.Result.subpkg = [ansible_collections.testns.testcoll.plugins.module_utils.subpkg.subcs.NestedUtil]::HelloWorld()
$module.Result.type_accelerator = "called from $([MyCSMU]::HelloWorld())"
$module.ExitJson()
