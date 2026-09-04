#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Secrets

# Verifies the C# Ansible.Secrets.SecretMasker produces the same results as the
# pure-Python ansible.module_utils._internal._secrets.SecretMasker. The masking
# corpus fixture is shared with test/units/module_utils/_internal/test_secretmasker.py
# so both implementations are held to the same contract.

$spec = @{
    options = @{
        corpus = @{ type = "str"; required = $true }
    }
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$maskerCtor = [Ansible.Secrets.SecretMasker].GetConstructor(
    [System.Reflection.BindingFlags]"NonPublic, Instance",
    $null,
    [Type[]]@(),
    $null)
$maskerField = [Ansible.Secrets.SecretMasker].GetField(
    "_instance",
    [System.Reflection.BindingFlags]"NonPublic, Static")

Function Reset-Masker {
    # The public interface is static and operates on a process-wide singleton, so
    # reset it to a fresh, pristine instance before each case to keep registered
    # secrets from one case from leaking into another.
    $maskerField.SetValue($null, $maskerCtor.Invoke(@()))
}

Function Assert-True {
    param(
        [Parameter(Mandatory = $true, Position = 0)][AllowNull()]$Condition,
        [Parameter(Mandatory = $true, Position = 1)][String]$Message
    )

    if (-not $Condition) {
        $call_stack = (Get-PSCallStack)[1]
        $module.Result.failed = $true
        $module.Result.line = $call_stack.ScriptLineNumber
        $module.Result.method = $call_stack.Position.Text
        $module.FailJson("AssertionError: $Message")
    }
}

$corpus = [Ansible.Basic.AnsibleModule]::FromJson($module.Params.corpus)
$sentinel = [String]$corpus.sentinel

foreach ($case in $corpus.cases) {
    Reset-Masker
    foreach ($secret in $case.secrets) {
        [Ansible.Secrets.SecretMasker]::RegisterSecret([String]$secret)
    }
    $masked = [Ansible.Secrets.SecretMasker]::MaskString([String]$case.input, $sentinel)

    Assert-True ($masked -ceq [String]$case.expected) "case '$($case.name)': expected '$($case.expected)' but got '$masked'"
}

# --- Registration is idempotent (parity with test_register_secret_text_is_idempotent) ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret("password123")
[Ansible.Secrets.SecretMasker]::RegisterSecret("password123")
$drained = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drained.Count -eq 1) "expected 1 new secret after duplicate registration, got $($drained.Count)"
Assert-True ($drained.Contains("password123")) "expected 'password123' in drained secrets"

# Draining a second time yields nothing new.
$drainedAgain = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drainedAgain.Count -eq 0) "expected 0 new secrets on the second drain, got $($drainedAgain.Count)"

# --- Short secrets are not registered (parity with test_short_secrets_are_not_registered) ---
Reset-Masker
$short = "a" * 3  # below the minimum secret length
[Ansible.Secrets.SecretMasker]::RegisterSecret($short)
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "secret shorter than the minimum length must not be registered"
$text = "XX${short}XX"
Assert-True ([Ansible.Secrets.SecretMasker]::MaskString($text, $sentinel) -ceq $text) "unregistered short secret must pass through unmasked"

# --- MaskString(value) default-placeholder overload (parity with mask_secrets default) ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret("defaultPlaceholderSecret")
$maskedDefault = [Ansible.Secrets.SecretMasker]::MaskString("pre defaultPlaceholderSecret post")
Assert-True ($maskedDefault -ceq 'pre $REDACTED$ post') "MaskString(value) must use the default placeholder, got '$maskedDefault'"

# --- RegisterSecret(SecureString) overload registers and masks the same as the string overload ---
Reset-Masker
$secureSecret = ConvertTo-SecureString -String "SecureStringSecret" -AsPlainText -Force
[Ansible.Secrets.SecretMasker]::RegisterSecret($secureSecret)
$drainedSecure = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drainedSecure.Count -eq 1) "expected 1 new secret after SecureString registration, got $($drainedSecure.Count)"
Assert-True ($drainedSecure.Contains("SecureStringSecret")) "expected 'SecureStringSecret' in drained secrets"
$maskedSecure = [Ansible.Secrets.SecretMasker]::MaskString("pre SecureStringSecret post", $sentinel)
Assert-True ($maskedSecure -ceq "pre $sentinel post") "SecureString-registered secret must be masked, got '$maskedSecure'"

$module.Result.data = "success"
$module.ExitJson()
