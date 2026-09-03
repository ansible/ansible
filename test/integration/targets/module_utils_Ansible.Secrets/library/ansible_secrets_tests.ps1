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

Function New-Masker {
    # A fresh, isolated masker so registered secrets from one case never leak
    # into another (the public singleton is shared process-wide).
    return $maskerCtor.Invoke(@())
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
    $masker = New-Masker
    foreach ($secret in $case.secrets) {
        $masker.RegisterSecret([String]$secret)
    }
    $masked = $masker.MaskString([String]$case.input, $sentinel)

    Assert-True ($masked -ceq [String]$case.expected) "case '$($case.name)': expected '$($case.expected)' but got '$masked'"
}

# --- Registration is idempotent (parity with test_register_secret_text_is_idempotent) ---
$masker = New-Masker
$masker.RegisterSecret("password123")
$masker.RegisterSecret("password123")
$drained = $masker.DrainNewSecrets()
Assert-True ($drained.Count -eq 1) "expected 1 new secret after duplicate registration, got $($drained.Count)"
Assert-True ($drained.Contains("password123")) "expected 'password123' in drained secrets"

# Draining a second time yields nothing new.
$drainedAgain = $masker.DrainNewSecrets()
Assert-True ($drainedAgain.Count -eq 0) "expected 0 new secrets on the second drain, got $($drainedAgain.Count)"

# --- Short secrets are not registered (parity with test_short_secrets_are_not_registered) ---
$masker = New-Masker
$short = "a" * 3  # below the minimum secret length
$masker.RegisterSecret($short)
Assert-True ($masker.DrainNewSecrets().Count -eq 0) "secret shorter than the minimum length must not be registered"
$text = "XX${short}XX"
Assert-True ($masker.MaskString($text, $sentinel) -ceq $text) "unregistered short secret must pass through unmasked"

# --- MaskString(value) default-placeholder overload (parity with mask_secrets default) ---
$masker = New-Masker
$masker.RegisterSecret("defaultPlaceholderSecret")
$maskedDefault = $masker.MaskString("pre defaultPlaceholderSecret post")
Assert-True ($maskedDefault -ceq 'pre $REDACTED$ post') "MaskString(value) must use the default placeholder, got '$maskedDefault'"

$module.Result.data = "success"
$module.ExitJson()
