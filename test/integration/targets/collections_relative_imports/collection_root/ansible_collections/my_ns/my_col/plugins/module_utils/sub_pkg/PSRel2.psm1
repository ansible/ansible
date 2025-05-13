#AnsibleRequires -PowerShell ansible_collections.my_ns.my_col2.plugins.module_utils.PSRel3

Function Invoke-FromPSRel2 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "$(Invoke-FromPSRel3) -> Invoke-FromPSRel2"
}

Export-ModuleMember -Function Invoke-FromPSRel2
