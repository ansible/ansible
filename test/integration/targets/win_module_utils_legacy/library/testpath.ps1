#powershell

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args

$path = Get-AnsibleParam -Obj $params -Name path -Type path

Exit-Json @{ path=$path }
