#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/input.log"

# YAML source, with the duplicate value repeated within the list to prove intra-file duplicates are ignored.
YAML_SEED='version: 1
secrets:
  - Inputyaml0030Secret
  - Inputdup0033Secret
  - Inputdup0033Secret
'

# JSON source; JSON is valid YAML so it loads through the same parser. Repeats the duplicate value that
# also appears in the YAML source to prove cross-file duplicates are ignored.
JSON_SEED="${OUTPUT_DIR}/seed_input.json"
echo '{"version": 1, "secrets": ["Inputjson0031Secret", "Inputdup0033Secret"]}' > "${JSON_SEED}"

# Executable source: the loader runs files with the executable bit and parses their stdout.
EXEC_SEED="${OUTPUT_DIR}/seed_exec.sh"
cat > "${EXEC_SEED}" <<'EOF'
#!/usr/bin/env bash
echo '{"version": 1, "secrets": ["Inputexec0032Secret", "Inputdup0033Secret"]}'
EOF
chmod +x "${EXEC_SEED}"

# YAML is fed as a pipe to exercise the read-once path; JSON as file, and an executable output
_ANSIBLE_SECRETS_INPUT_FILES=<(printf '%s' "${YAML_SEED}"),${JSON_SEED},"${EXEC_SEED}" \
    ansible-playbook input.yml -i ../../inventory "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Inputyaml0030Secret
    Inputjson0031Secret
    Inputexec0032Secret
    Inputdup0033Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "MARKER input_yaml: \$REDACTED\$"
    "MARKER input_json: \$REDACTED\$"
    "MARKER input_exec: \$REDACTED\$"
    "MARKER input_dup: \$REDACTED\$"
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

expect_failure() {
    local description="$1" seed="$2" expected="$3" leaked="$4" out
    if out=$(_ANSIBLE_SECRETS_INPUT_FILES=<(printf '%s' "${seed}") \
        ansible-playbook input.yml -i ../../inventory 2>&1); then
        echo "FAIL: ${description} was expected to abort but the command succeeded" >&2
        echo "${out}" >&2
        exit 1
    fi
    if ! grep -qF -- "${expected}" <<<"${out}"; then
        echo "FAIL: ${description} did not produce the expected error: ${expected}" >&2
        echo "${out}" >&2
        exit 1
    fi
    if grep -qF -- "${leaked}" <<<"${out}"; then
        echo "FAIL: ${description} disclosed the secret value '${leaked}' in its error output" >&2
        echo "${out}" >&2
        exit 1
    fi
}

expect_failure "unsupported version" 'version: 2
secrets:
  - Inputbadver0034Secret
' "has an unsupported version 2;" "Inputbadver0034Secret"

expect_failure "boolean version" 'version: true
secrets:
  - Inputbadbool0035Secret
' "has an unsupported version True;" "Inputbadbool0035Secret"

expect_failure "non-mapping structure" '- version: 1
- secrets:
    - Inputbadstruct0036Secret
' "must contain a mapping, not a list" "Inputbadstruct0036Secret"

expect_failure "non-string secret entry" 'version: 1
secrets:
  - some secret
  - 1234567
' "entry secrets[1] must be a string, not a int" "1234567"

echo "All secret masking secret input scenarios passed."
