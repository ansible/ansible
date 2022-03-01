#AnsibleRequires -CSharpUtil .sub_pkg.CSRel5 -Optional
#AnsibleRequires -PowerShell .sub_pkg.PSRelInvalid -Optional

Function Invoke-FromPSRel4 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "Invoke-FromPSRel4"
}

Export-ModuleMember -Function Invoke-FromPSRel4
