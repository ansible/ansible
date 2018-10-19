#Requires -Module Ansible.ModuleUtils.Recursive2
#Requires -Version 3.0

Function Get-Test3 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "Get-Test3: 2: $(Get-Test2)"
}

Function Get-NewTest3 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "Get-NewTest3"
}

Export-ModuleMember -Function Get-Test3, Get-NewTest3
