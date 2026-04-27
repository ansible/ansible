#AnsibleRequires -PowerShell .sub_pkg.PSRel2

Function Invoke-FromPSRel1 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "$(Invoke-FromPSRel2) -> Invoke-FromPSRel1"
}

Export-ModuleMember -Function Invoke-FromPSRel1
