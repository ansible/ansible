#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil ..module_utils.CSharpSigned

#AnsibleRequires -PowerShell Ansible.ModuleUtils.AddType
#AnsibleRequires -PowerShell ..module_utils.PwshSigned

# Tests builtin C# util
$module = [Ansible.Basic.AnsibleModule]::Create($args, @{ options = @{} })

# Tests builtin pwsh util
Add-CSharpType -AnsibleModule $module -References @'
using System;

namespace ns.col.module_utils
{
    public class InlineCSharp
    {
        public static string TestMethod(string input)
        {
            return input;
        }
    }
}
'@

$module.Result.language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
$module.Result.builtin_powershell_util = [ns.col.module_utils.InlineCSharp]::TestMethod("value")
$module.Result.csharp_util = [ansible_collections.ns.col.plugins.module_utils.CSharpSigned.TestClass]::TestMethod("value")
$module.Result.powershell_util = Test-PwshSigned

$module.ExitJson()
