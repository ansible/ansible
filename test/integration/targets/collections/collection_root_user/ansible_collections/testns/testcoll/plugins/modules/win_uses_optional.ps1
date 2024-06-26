#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Test builtin C# still works with -Optional
#AnsibleRequires -CSharpUtil Ansible.Basic -Optional

# Test no failure when importing an invalid builtin C# and pwsh util with -Optional
#AnsibleRequires -CSharpUtil Ansible.Invalid -Optional
#AnsibleRequires -PowerShell Ansible.ModuleUtils.Invalid -Optional

# Test valid module_util still works with -Optional
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.MyCSMUOptional -Optional
#AnsibleRequires -Powershell ansible_collections.testns.testcoll.plugins.module_utils.MyPSMUOptional -Optional

# Test no failure when importing an invalid collection C# and pwsh util with -Optional
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.invalid -Optional
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.invalid.invalid -Optional
#AnsibleRequires -Powershell ansible_collections.testns.testcoll.plugins.module_utils.invalid -Optional
#AnsibleRequires -Powershell ansible_collections.testns.testcoll.plugins.module_utils.invalid.invalid -Optional

$spec = @{
    options = @{
        data = @{ type = "str"; default = "called $(Invoke-FromUserPSMU)" }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$module.Result.data = $module.Params.data
$module.Result.csharp = [MyCSMU]::HelloWorld()

$module.ExitJson()
