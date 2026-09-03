#!powershell

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Secrets

$spec = @{
    options = @{
        incoming = @{ type = "str"; required = $true }
        register_as_secret = @{ type = "str"; required = $false; default = $null }
        no_log_option = @{ type = "str"; required = $true; no_log = $true }
    }
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$masker = [Ansible.Secrets.SecretMasker]::Instance

$incoming = $module.Params.incoming

$secrets = @('PwshModuleSecret1', 'PwshModuleSecret2', 'PwshModuleSecret3')
foreach ($secret in $secrets) {
    $masker.RegisterSecret($secret)
}

$registerAsSecret = $module.Params.register_as_secret
if ($null -ne $registerAsSecret) {
    $masker.RegisterSecret($registerAsSecret)
}

$module.Result.discovered = $secrets[0]
$module.Result.masked = $masker.MaskString("$($secrets[0]) $($secrets[1]) $($secrets[2])")
$module.Result.masked_custom = $masker.MaskString($secrets[0], "<HIDDEN>")
$module.Result.incoming = $incoming
$module.Result.incoming_masked = $masker.MaskString($incoming)
$module.Result.register_as_secret = $registerAsSecret
$module.Result.no_log_option = $module.Params.no_log_option
$module.Result.no_log_option_masked = $masker.MaskString($module.Params.no_log_option)
$module.Result.changed = $false

$module.ExitJson()
