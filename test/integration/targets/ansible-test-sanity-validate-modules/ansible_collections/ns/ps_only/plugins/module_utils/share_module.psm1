#AnsibleRequires -CSharpUtil Ansible.Basic

Function Invoke-AnsibleModule {
    <#
        .SYNOPSIS
        validate
    #>
    [CmdletBinding()]
    param ()

    $module = [Ansible.Basic.AnsibleModule]::Create(@(), @{
            options = @{
                test = @{ type = 'str' }
            }
        })
    $module.ExitJson()
}

Export-ModuleMember -Function Invoke-AnsibleModule
