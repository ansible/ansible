#AnsibleRequires -CSharpUtil Ansible.Invalid -Optional
#AnsibleRequires -Powershell Ansible.ModuleUtils.Invalid -Optional
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.invalid -Optional
#AnsibleRequires -CSharpUtil ansible_collections.testns.testcoll.plugins.module_utils.invalid.invalid -Optional
#AnsibleRequires -Powershell ansible_collections.testns.testcoll.plugins.module_utils.invalid -Optional
#AnsibleRequires -Powershell ansible_collections.testns.testcoll.plugins.module_utils.invalid.invalid -Optional

Function Invoke-FromUserPSMU {
    <#
    .SYNOPSIS
    Test function
    #>
    return "from optional user_mu"
}

Export-ModuleMember -Function Invoke-FromUserPSMU
