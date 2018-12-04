#Requires -Module Ansible.ModuleUtils.Recursive1
#Requires -Module Ansible.ModuleUtils.Recursive3

Function Get-Test2 {
    <#
    .SYNOPSIS
    Test function
    #>
    return "Get-Test2, 1: $(Get-Test1), 3: $(Get-NewTest3)"
}

Export-ModuleMember -Function Get-Test2
