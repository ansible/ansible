#1powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -CSharpUtil Ansible.Test

$result = @{
    res = [Ansible.Test.OutputTest]::GetString()
    changed = $false
}

Exit-Json -obj $result

