#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

Function Test-Function {
    return "abc"
}

Function Invoke-AnsibleModule {
    param (
        [Parameter(Mandatory=$true)][AllowEmptyCollection()][System.Object[]]$Arguments
    )
    $spec = @{
        options = @{}
        supports_check_mode = $true
    }
    $module = [Ansible.Basic.AnsibleModule]::Create($Arguments, $spec)

    $module.ExitJson()
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-AnsibleModule -Arguments $args
}
