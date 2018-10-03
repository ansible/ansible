#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Basic

$spec = @{
    data = @{ type = "str"; default = "pong" }
}
$module = Get-AnsibleModule -Arguments $args -ArgumentSpec $spec -SupportsCheckMode
$data = $module.Params.data

if ($data -eq "crash") {
    throw "boom"
}

$module.Result.ping = $data
$module.ExitJson()
