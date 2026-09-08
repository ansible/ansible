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

# --- Short secrets are not registered (the masking side is in the corpus) ---
Reset-Masker
$short = "a" * 3  # below the minimum secret length
[Ansible.Secrets.SecretMasker]::RegisterSecret($short)
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "secret shorter than the minimum length must not be registered"

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

# --- Re-registering a drained secret does not report it again ---
[Ansible.Secrets.SecretMasker]::RegisterSecret("SecureStringSecret")
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "re-registering an already registered secret must not report it as new"

# --- Only the secret itself is reported as new, not its derived JSON forms (parity with test_only_the_secret_itself_is_tracked_as_new) ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret('test"secret\value')
$drainedJson = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drainedJson.Count -eq 1) "expected only the literal secret to be reported as new, got $($drainedJson.Count)"
Assert-True ($drainedJson.Contains('test"secret\value')) "expected the literal secret in the drained secrets"
$maskedJsonForm = [Ansible.Secrets.SecretMasker]::MaskString('{"k": "test\"secret\\value"}', $sentinel)
Assert-True ($maskedJsonForm -ceq "{`"k`": `"$sentinel`"}") "JSON escaped form of a secret must be masked, got '$maskedJsonForm'"

# --- Oversized secrets are reported trimmed and de-duplicated on the trimmed value (parity with test_tracker_records_trimmed_secret) ---
Reset-Masker
$maxLength = 65536
$base = -join (0..($maxLength - 1) | ForEach-Object { [char](0x21 + ($_ % 90)) })
[Ansible.Secrets.SecretMasker]::RegisterSecret($base + "AAA")
[Ansible.Secrets.SecretMasker]::RegisterSecret($base + "BBB")
$drainedTrimmed = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drainedTrimmed.Count -eq 1) "two secrets that differ only beyond the cap must be reported as one, got $($drainedTrimmed.Count)"
Assert-True ($drainedTrimmed.Contains($base)) "expected the trimmed secret in the drained secrets"

# --- Surrounding whitespace is stripped before registration (parity with test_tracker_records_stripped_secret) ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret(" `tStrippedSecretValue`r`n")
$drainedStripped = [Ansible.Secrets.SecretMasker]::DrainNewSecrets()
Assert-True ($drainedStripped.Count -eq 1) "expected 1 new secret after registering a padded value, got $($drainedStripped.Count)"
Assert-True ($drainedStripped.Contains("StrippedSecretValue")) "expected the stripped secret to be reported as new"
[Ansible.Secrets.SecretMasker]::RegisterSecret("    ")
[Ansible.Secrets.SecretMasker]::RegisterSecret(" ab ")
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "whitespace-only and padded short values must not be registered"

# --- Lengths are measured in code points, matching Python (surrogate pairs count once) ---
Reset-Masker
$astral = [char]::ConvertFromUtf32(0x1F600)  # one code point, two UTF-16 chars
[Ansible.Secrets.SecretMasker]::RegisterSecret($astral * 3)
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "a secret of 3 code points must not be registered even though it is 6 chars"
[Ansible.Secrets.SecretMasker]::RegisterSecret($astral * 4)
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 1) "a secret of 4 code points must be registered"

# --- Interleaving registration and masking keeps every earlier secret masked (parity with test_registering_a_secret_does_not_rebuild_previous_state) ---
Reset-Masker
$interleaved = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 50; $i++) {
    $secret = "secret{0:D4}xyz" -f $i
    $interleaved.Add($secret)
    [Ansible.Secrets.SecretMasker]::RegisterSecret($secret)
    $maskedInterleaved = [Ansible.Secrets.SecretMasker]::MaskString(($interleaved -join " "), $sentinel)
    $expectedInterleaved = (@($sentinel) * $interleaved.Count) -join " "
    Assert-True ($maskedInterleaved -ceq $expectedInterleaved) "secret registered after masking started was not masked at iteration $i"
}

# --- A new secret that changes an existing fail link is honoured (parity with test_registering_a_secret_that_changes_an_existing_fail_link) ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret("abcdefgh-one")
$failText = "xabcdefgh-two bcdefgh-two"
Assert-True ([Ansible.Secrets.SecretMasker]::MaskString($failText, $sentinel) -ceq $failText) "no secret present, text must be unchanged"
[Ansible.Secrets.SecretMasker]::RegisterSecret("bcdefgh-two")
$maskedFail = [Ansible.Secrets.SecretMasker]::MaskString($failText, $sentinel)
Assert-True ($maskedFail -ceq "xa$sentinel $sentinel") "secret that is a suffix of an existing path must be masked after registration, got '$maskedFail'"

# --- _RegisterAnsibleSecrets registers the controller's secrets without reporting them as new ---
Reset-Masker
$initial = [System.Collections.Generic.List[System.Security.SecureString]]::new()
$initial.Add((ConvertTo-SecureString -String "InitialSecretOne" -AsPlainText -Force))
$initial.Add((ConvertTo-SecureString -String "InitialSecretTwo" -AsPlainText -Force))
[Ansible.Secrets.SecretMasker]::_RegisterAnsibleSecrets($initial)
Assert-True ([Ansible.Secrets.SecretMasker]::DrainNewSecrets().Count -eq 0) "secrets registered by the controller must not be reported back as new"
$maskedInitial = [Ansible.Secrets.SecretMasker]::MaskString("InitialSecretOne InitialSecretTwo", $sentinel)
Assert-True ($maskedInitial -ceq "$sentinel $sentinel") "secrets registered by the controller must be masked, got '$maskedInitial'"

# --- Edge inputs: empty value and empty placeholder ---
Reset-Masker
[Ansible.Secrets.SecretMasker]::RegisterSecret("EdgeCaseSecret")
Assert-True ([Ansible.Secrets.SecretMasker]::MaskString("", $sentinel) -ceq "") "empty value must be returned unchanged"
Assert-True ($null -eq [Ansible.Secrets.SecretMasker]::MaskString([NullString]::Value, $sentinel)) "null value must be returned unchanged"
Assert-True ([Ansible.Secrets.SecretMasker]::MaskString("pre EdgeCaseSecret post", "") -ceq "pre  post") "an empty placeholder must remove the secret"

$module.Result.data = "success"
$module.ExitJson()
