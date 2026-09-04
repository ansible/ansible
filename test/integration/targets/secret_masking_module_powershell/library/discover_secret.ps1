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

$incoming = $module.Params.incoming

$secrets = @('PwshModuleSecret1', 'PwshModuleSecret2', 'PwshModuleSecret3')
foreach ($secret in $secrets) {
    [Ansible.Secrets.SecretMasker]::RegisterSecret($secret)
}

$registerAsSecret = $module.Params.register_as_secret
if ($null -ne $registerAsSecret) {
    [Ansible.Secrets.SecretMasker]::RegisterSecret($registerAsSecret)
}

$module.Result.discovered = $secrets[0]
$module.Result.masked = [Ansible.Secrets.SecretMasker]::MaskString("$($secrets[0]) $($secrets[1]) $($secrets[2])")
$module.Result.masked_custom = [Ansible.Secrets.SecretMasker]::MaskString($secrets[0], "<HIDDEN>")
$module.Result.incoming = $incoming
$module.Result.incoming_masked = [Ansible.Secrets.SecretMasker]::MaskString($incoming)
$module.Result.register_as_secret = $registerAsSecret
$module.Result.no_log_option = $module.Params.no_log_option
$module.Result.no_log_option_masked = [Ansible.Secrets.SecretMasker]::MaskString($module.Params.no_log_option)
$module.Result.changed = $false

$module.ExitJson()
