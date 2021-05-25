#AnsibleRequires -CSharpUtil .sub_pkg.CSRel4

Function Invoke-FromPSRel3 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "$([CSRel4]::Invoke()) -> Invoke-FromPSRel3"
}

Export-ModuleMember -Function Invoke-FromPSRel3
