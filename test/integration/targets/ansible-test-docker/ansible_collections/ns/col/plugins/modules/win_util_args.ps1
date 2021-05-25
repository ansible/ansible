#!powershell

# Copyright (c) 2020 Ansible Project
# # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ..module_utils.PSUtil

$spec = @{
    options = @{
      my_opt = @{ type = "str"; required = $true }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec, @(Get-PSUtilSpec))
$module.ExitJson()
